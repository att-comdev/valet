import operator
import sys
import copy

from constraint_solver import ConstraintSolverSimple
from search_base import Node, Resource, LogicalGroupResource
from search_base import compute_reservation

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, LEVELS

sys.path.insert(0, '../resource_manager')
from resource_base import Datacenter


class SearchSimple:

    def __init__(self, _logger):
        self.logger = _logger

        self.resource = None  
        self.app_topology = None

        self.avail_hosts = {} 
        self.avail_logical_groups = {}

        self.node_placements = {}
        self.num_of_hosts = 0

        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

        self.constraint_solver = None

        self.status = "success"

    def place_nodes(self, _app_topology, _resource):
        self._init_placements()

        self.app_topology = _app_topology

        if self.app_topology.optimization_priority == None:
            return True

        self.resource = _resource

        self.constraint_solver = ConstraintSolverSimple(self.logger)

        self._create_avail_logical_groups()
        self._create_avail_hosts()

        self._compute_resource_weights()

        (open_node_list, level) = self._create_open_list(self.app_topology.vms, \
                                                         self.app_topology.vgroups) 

        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def _init_placements(self):
        self.avail_hosts.clear()
        self.avail_logical_groups.clear()

        self.node_placements.clear()
        self.num_of_hosts = 0

        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1

    def _create_avail_hosts(self):
        for hk, host in self.resource.hosts.iteritems():

            if host.check_availability() == False:
                continue

            r = Resource()
            r.host_name = hk

            for mk in host.memberships.keys():
                if mk in self.avail_logical_groups.keys():
                    r.host_memberships[mk] = self.avail_logical_groups[mk]

            r.host_vCPUs = host.original_vCPUs
            r.host_avail_vCPUs = host.avail_vCPUs
            r.host_mem = host.original_mem_cap
            r.host_avail_mem = host.avail_mem_cap
            r.host_local_disk = host.original_local_disk_cap
            r.host_avail_local_disk = host.avail_local_disk_cap

            r.host_num_of_placed_vms = len(host.vm_list)

            rack = host.host_group
            if isinstance(rack, Datacenter):
                r.rack_name = "any"
                r.cluster_name = "any"
            else:
                if rack.status != "enabled":
                    continue

                r.rack_name = rack.name

                for mk in rack.memberships.keys():
                    if mk in self.avail_logical_groups.keys():
                        r.rack_memberships[mk] = self.avail_logical_groups[mk]

                r.rack_vCPUs = rack.original_vCPUs
                r.rack_avail_vCPUs = rack.avail_vCPUs
                r.rack_mem = rack.original_mem_cap
                r.rack_avail_mem = rack.avail_mem_cap
                r.rack_local_disk = rack.original_local_disk_cap
                r.rack_avail_local_disk = rack.avail_local_disk_cap

                r.rack_num_of_placed_vms = len(rack.vm_list)
  
                cluster = rack.parent_resource
                if isinstance(cluster, Datacenter):
                    r.cluster_name = "any"

            if r.host_num_of_placed_vms > 0:
                self.num_of_hosts += 1

            self.avail_hosts[hk] = r

    def _create_avail_logical_groups(self):
        for lgk, lg in self.resource.logical_groups.iteritems():
        
            if lg.status != "enabled":
                continue

            lgr = LogicalGroupResource()
            lgr.name = lgk
            lgr.group_type = lg.group_type

            for mk, mv in lg.metadata.iteritems():
                lgr.metadata[mk] = mv

            lgr.num_of_placed_vms = len(lg.vm_list)
            for hk in lg.vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[hk] = len(lg.vms_per_host[hk])

            for hk in lg.vms_per_host.keys():
                if hk in self.resource.hosts.keys():                                                      
                    host = self.resource.hosts[hk]     
                    if host.check_availability() == False:                                       
                        for vm_id in host.vm_list:                                               
                            if lg.exist_vm_by_uuid(vm_id[2]) == True: 
                                lgr.num_of_placed_vms -= 1  
                        if hk in lgr.num_of_placed_vms_per_host.keys():                                    
                            del lgr.num_of_placed_vms_per_host[hk]       
                elif hk in self.resource.host_groups.keys():                                              
                    host_group = self.resource.host_groups[hk]                                            
                    if host_group.check_availability() == False:                                 
                        for vm_id in host_group.vm_list:                                         
                            if lg.exist_vm_by_uuid(vm_id[2]) == True:                                       
                                lgr.num_of_placed_vms -= 1                                        
                        if hk in lgr.num_of_placed_vms_per_host.keys():                                    
                            del lgr.num_of_placed_vms_per_host[hk]                                       

            self.avail_logical_groups[lgk] = lgr

    def _compute_resource_weights(self):
        denominator = 0.0
        for (t, w) in self.app_topology.optimization_priority:
            denominator += w

        for (t, w) in self.app_topology.optimization_priority:
            if t == "cpu":
                self.CPU_weight = float(w / denominator)
            elif t == "mem":
                self.mem_weight = float(w / denominator)
            elif t == "lvol":
                self.local_disk_weight = float(w / denominator)

    def _create_open_list(self, _vms, _volumes, _vgroups): 
        open_node_list = []
        level = "host"

        for vmk, vm in _vms.iteritems():
            n = Node()
            n.node = vm
            n.sort_base = self._set_virtual_capacity_based_sort(vm)
            open_node_list.append(n)

        for gk, g in _vgroups.iteritems():
            if LEVELS.index(g.level) > LEVELS.index(level):
                level = g.level

            n = Node()
            n.node = g
            n.sort_base = self._set_virtual_capacity_based_sort(g)
            open_node_list.append(n)

        return (open_node_list, level)

    def _set_virtual_capacity_based_sort(self, _v):
        sort_base = -1

        sort_base = self.CPU_weight * _v.vCPU_weight + \
                    self.mem_weight * _v.mem_weight + \
                    self.local_disk_weight * _v.local_volume_weight
 
        return sort_base
        
    def _run_greedy(self, _open_node_list, _level, _avail_hosts):
        success = True

        avail_resources = {}
        if _level == "rack":
            for hk, h in _avail_hosts.iteritems():
                if h.rack_name not in avail_resources.keys():
                    avail_resources[h.rack_name] = h
        elif _level == "host":
            avail_resources = _avail_hosts

        _open_node_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        while len(_open_node_list) > 0:
            n = _open_node_list.pop(0)

            best_resource = self._get_best_resource(n, _level, avail_resources)
            if best_resource == None:
                success = False
                break

            self._deduct_reservation(_level, best_resource, n)
            self._close_node_placement(_level, best_resource, n.node)

        return success

    def _get_best_resource(self, _n, _level, _avail_resources):
        candidate_list = self.constraint_solver.compute_candidate_list(_level, \
                                                                       _n, \
                                                                       self.node_placements, \
                                                                       _avail_resources, \
                                                                       self.avail_logical_groups)
        if len(candidate_list) == 0:
            self.status = self.constraint_solver.status
            return None

        self._set_compute_sort_base(_level, candidate_list)
        candidate_list.sort(key=operator.attrgetter("sort_base"))

        best_resource = None
        if _level == "host" and isinstance(_n.node, VM:
            best_resource = copy.deepcopy(top_candidate_list[0])
            best_resource.level = "host"
        else:
            while True:
 
                while len(candidate_list) > 0:
                    cr = candidate_list.pop(0)

                    vms = {}
                    vgroups = {}
                    if isinstance(_n.node, VGroup):
                        if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                            vgroups[_n.node.uuid] = _n.node
                        else:
                            for sgk, sg in _n.node.subvgroups.iteritems():
                                if isinstance(sg, VM):
                                    vms[sg.uuid] = sg
                                elif isinstance(sg, VGroup):
                                    vgroups[sg.uuid] = sg
                    else:
                        vms[_n.node.uuid] = _n.node

                    (open_node_list, level) = self._create_open_list(vms, vgroups)
 
                    avail_hosts = {}
                    for hk, h in self.avail_hosts.iteritems():
                        if _level == "rack":
                            if h.rack_name == cr.rack_name:
                                avail_hosts[hk] = h
                        elif _level == "host":
                            if h.host_name == cr.host_name:
                                avail_hosts[hk] = h

                    if self._run_greedy(open_node_list, level, avail_hosts) == True:
                        best_resource = copy.deepcopy(cr)
                        best_resource.level = _level
                        break
                    else:
                        self._rollback_reservation(_n.node)
                        self._rollback_node_placement(_n.node)

                if best_resource != None:
                    break
                else:
                    if len(candidate_list) == 0:
                        self.status = "no available hosts"
                        break
 
        return best_resource

    def _set_compute_sort_base(self, _level, _candidate_list):
        for c in _candidate_list:
            CPU_ratio = -1
            mem_ratio = -1
            local_disk_ratio = -1
            if _level == "rack":
                CPU_ratio = float(c.rack_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.rack_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.rack_avail_local_disk) / \
                                   float(self.resource.local_disk_avail)
            elif _level == "host":
                CPU_ratio = float(c.host_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.host_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.host_avail_local_disk) / \
                                   float(self.resource.local_disk_avail)
            c.sort_base = (1.0 - self.CPU_weight) * CPU_ratio + \
                          (1.0 - self.mem_weight) * mem_ratio + \
                          (1.0 - self.local_disk_weight) * local_disk_ratio 
                          
    def _deduct_reservation(self, _level, _best, _n):
        exclusivities = self.constraint_solver.get_exclusivities(_n.node.exclusivity_groups, _level)
        exclusivity_id = None
        if len(exclusivities) == 1:
            exclusivity_id = exclusivities[exclusivities.keys()[0]]
        if exclusivity_id != None:
            self._add_exclusivity(_level, _best, exclusivity_id)

        affinity_id = _n.get_affinity_id()
        if affinity_id != None:
            self._add_affinity(_level, _best, affinity_id)

        self._deduct_vm_resources(_best, _n)

    def _add_exclusivity(self, _level, _best, _exclusivity_id):
        lgr = None
        if _exclusivity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _exclusivity_id
            lgr.group_type = "EX"
            self.avail_logical_groups[lgr.name] = lgr
        else:
            lgr = self.avail_logical_groups[_exclusivity_id]
 
        if _exclusivity_id.split(":")[0] == _level:
            lgr.num_of_placed_vms += 1

            host_name = _best.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[host_name] = 0
            lgr.num_of_placed_vms_per_host[host_name] += 1

        chosen_host = self.avail_hosts[_best.host_name]
        if _level == "host":
            if _exclusivity_id not in chosen_host.host_memberships.keys():
                chosen_host.host_memberships[_exclusivity_id] = lgr
            for npk, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    if _exclusivity_id not in np.rack_memberships.keys():
                        np.rack_memberships[_exclusivity_id] = lgr
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    if _exclusivity_id not in np.cluster_memberships.keys():
                        np.cluster_memberships[_exclusivity_id] = lgr
        elif _level == "rack": 
            for npk, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    if _exclusivity_id not in np.rack_memberships.keys():
                        np.rack_memberships[_exclusivity_id] = lgr
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    if _exclusivity_id not in np.cluster_memberships.keys():
                        np.cluster_memberships[_exclusivity_id] = lgr

    def _add_affinity(self, _level, _best, _affinity_id):
        lgr = None
        if _affinity_id not in self.avail_logical_groups.keys():
            lgr = LogicalGroupResource()
            lgr.name = _affinity_id
            lgr.group_type = "AFF"
            self.avail_logical_groups[lgr.name] = lgr
        else:
            lgr = self.avail_logical_groups[_affinity_id]
 
        if _affinity_id.split(":")[0] == _level:
            lgr.num_of_placed_vms += 1

            host_name = _best.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[host_name] = 0
            lgr.num_of_placed_vms_per_host[host_name] += 1

            self.logger.debug("node added to affinity (" + _affinity_id + ")")

        chosen_host = self.avail_hosts[_best.host_name]
        if _level == "host":
            if _affinity_id not in chosen_host.host_memberships.keys():
                chosen_host.host_memberships[_affinity_id] = lgr
            for npk, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    if _affinity_id not in np.rack_memberships.keys():
                        np.rack_memberships[_affinity_id] = lgr
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    if _affinity_id not in np.cluster_memberships.keys():
                        np.cluster_memberships[_affinity_id] = lgr
        elif _level == "rack": 
            for npk, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    if _affinity_id not in np.rack_memberships.keys():
                        np.rack_memberships[_affinity_id] = lgr
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    if _affinity_id not in np.cluster_memberships.keys():
                        np.cluster_memberships[_affinity_id] = lgr

    def _deduct_vm_resources(self, _best, _n):
        chosen_host = self.avail_hosts[_best.host_name]
        chosen_host.host_avail_vCPUs -= _n.node.vCPUs
        chosen_host.host_avail_mem -= _n.node.mem
        chosen_host.host_avail_local_disk -= _n.node.local_volume_size

        if chosen_host.host_num_of_placed_vms == 0:
            self.num_of_hosts += 1
        chosen_host.host_num_of_placed_vms += 1

        for npk, np in self.avail_hosts.iteritems():
            if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                np.rack_avail_vCPUs -= _n.node.vCPUs
                np.rack_avail_mem -= _n.node.mem
                np.rack_avail_local_disk -= _n.node.local_volume_size
                np.rack_num_of_placed_vms += 1
            if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                np.cluster_avail_vCPUs -= _n.node.vCPUs
                np.cluster_avail_mem -= _n.node.mem
                np.cluster_avail_local_disk -= _n.node.local_volume_size
                np.cluster_num_of_placed_vms += 1

        for vml in _n.node.vm_list:
            if vml.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = vml.nw_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)

        for voll in _n.node.volume_list:
            if voll.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[voll.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = voll.io_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)

    def _close_node_placement(self, _level, _best, _v):
        if _level == "host": 
            if _v not in self.node_placements.keys():
                self.node_placements[_v] = _best
        else:
            if isinstance(_v, VGroup):
                if _v not in self.node_placements.keys():
                    self.node_placements[_v] = _best

    def _rollback_reservation(self, _v):
        if isinstance(_v, VM):
            self._rollback_vm_reservation(_v)

        elif isinstance(_v, VGroup):
            if _v in self.node_placements.keys():
                affinity_id = _v.level + ":" + _v.name
                chosen_host = self.avail_hosts[self.node_placements[_v].host_name]

                self._remove_affinity(chosen_host, affinity_id, self.node_placements[_v].level)

            for vk, v in _v.subvgroups.iteritems():
                self._rollback_reservation(v) 

        if _v in self.node_placements.keys():
            exclusivities = self.constraint_solver.get_exclusivities(_v.exclusivity_groups, \
                                                                     self.node_placements[_v].level)

            if len(exclusivities) == 1:
                exclusivity_id = exclusivities[exclusivities.keys()[0]]
                chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
                self._remove_exclusivity(chosen_host, exclusivity_id, self.node_placements[_v].level) 

    def _remove_exclusivity(self, _chosen_host, _exclusivity_id, _level):
        if _exclusivity_id.split(":")[0] == _level: 
            lgr = self.avail_logical_groups[_exclusivity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1 

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_logical_groups[_exclusivity_id]

        if _level == "host":
            if _chosen_host.host_num_of_placed_vms == 0 and \
               _exclusivity_id in _chosen_host.host_memberships.keys():
                del _chosen_host.host_memberships[_exclusivity_id]

                for npk, np in self.avail_hosts.iteritems():
                    if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                        if _exclusivity_id in np.rack_memberships.keys():
                            del np.rack_memberships[_exclusivity_id]
                    if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                        if _exclusivity_id in np.cluster_memberships.keys():
                            del np.cluster_memberships[_exclusivity_id]

        elif _level == "rack": 
            if _chosen_host.rack_num_of_placed_vms == 0:
                for npk, np in self.avail_hosts.iteritems():
                    if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                        if _exclusivity_id in np.rack_memberships.keys():
                            del np.rack_memberships[_exclusivity_id]
                    if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                        if _exclusivity_id in np.cluster_memberships.keys():
                            del np.cluster_memberships[_exclusivity_id]

    def _remove_affinity(self, _chosen_host, _affinity_id, _level):
        if _affinity_id.split(":")[0] == _level: 
            lgr = self.avail_logical_groups[_affinity_id]

            host_name = _chosen_host.get_resource_name(_level)
            lgr.num_of_placed_vms -= 1
            lgr.num_of_placed_vms_per_host[host_name] -= 1 

            if lgr.num_of_placed_vms_per_host[host_name] == 0:
                del lgr.num_of_placed_vms_per_host[host_name]

            if lgr.num_of_placed_vms == 0:
                del self.avail_logical_groups[_affinity_id]

        exist_affinity = True
        if _affinity_id not in self.avail_logical_groups.keys():
            exist_affinity = False
        else:
            lgr = self.avail_logical_groups[_affinity_id]
            host_name = _chosen_host.get_resource_name(_level)
            if host_name not in lgr.num_of_placed_vms_per_host.keys(): 
                exist_affinity = False

        if _level == "host":
            if exist_affinity == False and _affinity_id in _chosen_host.host_memberships.keys():
                del _chosen_host.host_memberships[_affinity_id]

                for npk, np in self.avail_hosts.iteritems():
                    if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                        if _affinity_id in np.rack_memberships.keys():
                            del np.rack_memberships[_affinity_id]
                    if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                        if _affinity_id in np.cluster_memberships.keys():
                            del np.cluster_memberships[_affinity_id]

        elif _level == "rack": 
            if exist_affinity == False:
                for npk, np in self.avail_hosts.iteritems():
                    if _chosen_host.rack_name != "any" and np.rack_name == _chosen_host.rack_name:
                        if _affinity_id in np.rack_memberships.keys():
                            del np.rack_memberships[_affinity_id]
                    if _chosen_host.cluster_name != "any" and np.cluster_name == _chosen_host.cluster_name:
                        if _affinity_id in np.cluster_memberships.keys():
                            del np.cluster_memberships[_affinity_id]

    def _rollback_vm_reservation(self, _v):
        if _v in self.node_placements.keys():
            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]
            chosen_host.host_avail_vCPUs += _v.vCPUs
            chosen_host.host_avail_mem += _v.mem
            chosen_host.host_avail_local_disk += _v.local_volume_size

            chosen_host.host_num_of_placed_vms -= 1
            if chosen_host.host_num_of_placed_vms == 0:
                self.num_of_hosts -= 1

            for npk, np in self.avail_hosts.iteritems():
                if chosen_host.rack_name != "any" and np.rack_name == chosen_host.rack_name:
                    np.rack_avail_vCPUs += _v.vCPUs
                    np.rack_avail_mem += _v.mem
                    np.rack_avail_local_disk += _v.local_volume_size
                    np.rack_num_of_placed_vms -= 1
                if chosen_host.cluster_name != "any" and np.cluster_name == chosen_host.cluster_name:
                    np.cluster_avail_vCPUs += _v.vCPUs
                    np.cluster_avail_mem += _v.mem
                    np.cluster_avail_local_disk += _v.local_volume_size
                    np.cluster_num_of_placed_vms -= 1

            for vml in _v.vm_list:
                if vml.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = vml.nw_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

            for voll in _v.volume_list:
                if voll.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[voll.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = voll.io_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

        return nw_reservation

    def _rollback_node_placement(self, _v):
        if _v in self.node_placements.keys():
            del self.node_placements[_v]

        if isinstance(_v, VGroup):
            for sgk, sg in _v.subvgroups.iteritems():
                self._rollback_node_placement(sg)





