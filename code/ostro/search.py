#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions
# - Search the optimal placement
#
#################################################################################################################


import operator
import sys
import copy

from constraint_solver import ConstraintSolver
from search_base import Node, Resource, LogicalGroupResource, SwitchResource, StorageResource
from search_base import compute_reservation

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, Volume, VGroupLink, VMLink, VolumeLink, LEVELS

sys.path.insert(0, '../resource_manager')
from resource_base import Datacenter


class Search:

    def __init__(self, _logger):
        self.logger = _logger

        # Search inputs
        self.resource = None  
        self.app_topology = None

        # Snapshot of current resource status
        self.avail_hosts = {} 
        self.avail_logical_groups = {}
        self.avail_storage_hosts = {}
        self.avail_switches = {}

        # Search results
        self.node_placements = {}
        self.bandwidth_usage = 0
        self.num_of_hosts = 0

        # Optimization criteria
        self.nw_bandwidth_weight = -1
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1
        self.disk_weight = -1

        self.constraint_solver = None

        self.status = "success"

    def place_nodes(self, _app_topology, _resource):
        self.app_topology = _app_topology
        self.resource = _resource

        self.constraint_solver = ConstraintSolver(self.logger)

        self._init_placements()

        self.logger.info("start search")

        self._create_avail_logical_groups()
        self._create_avail_storage_hosts()
        self._create_avail_switches()
        self._create_avail_hosts()

        self._compute_resource_weights()

        (open_node_list, level) = self._create_open_list(self.app_topology.vms, \
                                                         self.app_topology.volumes, \
                                                         self.app_topology.vgroups) 

        return self._run_greedy(open_node_list, level, self.avail_hosts)

    def _init_placements(self):
        self.avail_hosts.clear()
        self.avail_logical_groups.clear()
        self.avail_storage_hosts.clear()
        self.avail_switches.clear()

        self.node_placements.clear()
        self.bandwidth_usage = 0
        self.num_of_hosts = 0

        self.nw_bandwidth_weight = -1
        self.CPU_weight = -1
        self.mem_weight = -1
        self.local_disk_weight = -1
        self.disk_weight = -1

    def _create_avail_hosts(self):
        for hk, h in self.resource.hosts.iteritems():

            if h.status != "enabled" or h.state != "up":
                continue
            if ("nova" not in h.tag) or ("infra" not in h.tag):
                continue

            r = Resource()
            r.host_name = hk

            for mk in h.memberships.keys():
                if mk in self.avail_logical_groups.keys():
                    r.host_memberships[mk] = self.avail_logical_groups[mk]

            for sk in h.storages.keys():
                if sk in self.avail_storage_hosts.keys():
                    r.host_avail_storages[sk] = self.avail_storage_hosts[sk]

            for sk in h.switches.keys():
                if sk in self.avail_switches.keys():
                    r.host_avail_switches[sk] = self.avail_switches[sk]

            r.host_avail_vCPUs = h.avail_vCPUs
            r.host_avail_mem = h.avail_mem_cap
            r.host_avail_local_disk = h.avail_local_disk_cap

            r.host_num_of_placed_vms = len(h.vm_list)

            rack = h.host_group
            if isinstance(rack, Datacenter):
                r.rack_name = "any"
                #r.rack_avail_vCPUs = sys.maxint
                #r.rack_avail_mem = sys.maxint
                #r.rack_avail_local_disk = sys.maxint

                r.cluster_name = "any"
                #r.cluster_avail_vCPUs = sys.maxint
                #r.cluster_avail_mem = sys.maxint
                #r.cluster_avail_local_disk = sys.maxint
            else:
                if rack.status != "enabled":
                    continue

                r.rack_name = rack.name

                for mk in rack.memberships.keys():
                    if mk in self.avail_logical_groups.keys():
                        r.rack_memberships[mk] = self.avail_logical_groups[mk]

                for rsk in rack.storages.keys():
                    if rsk in self.avail_storage_hosts.keys():
                        r.rack_avail_storages[rsk] = self.avail_storage_hosts[rsk]

                for rsk in rack.switches.keys():
                    if rsk in self.avail_switches.keys():
                        r.rack_avail_switches[rsk] = self.avail_switches[rsk]

                r.rack_avail_vCPUs = rack.avail_vCPUs
                r.rack_avail_mem = rack.avail_mem_cap
                r.rack_avail_local_disk = rack.avail_local_disk_cap

                r.rack_num_of_placed_vms = len(rack.vm_list)
  
                cluster = rack.parent_resource
                if isinstance(cluster, Datacenter):
                    r.cluster_name = "any"
                    #r.cluster_avail_vCPUs = sys.maxint
                    #r.cluster_avail_mem = sys.maxint
                    #r.cluster_avail_local_disk = sys.maxint
                else:
                    if cluster.status != "enabled":
                        continue

                    r.cluster_name = cluster.name

                    for mk in cluster.memberships.keys():
                        if mk in self.avail_logical_groups.keys():
                            r.cluster_memberships[mk] = self.avail_logical_groups[mk]

                    for csk in cluster.storages.keys():
                        if csk in self.avail_storage_hosts.keys():
                            r.cluster_avail_storages[csk] = self.avail_storage_hosts[csk]

                    for csk in cluster.switches.keys():
                        if csk in self.avail_switches.keys():
                            r.cluster_avail_switches[csk] = self.avail_switches[csk]

                    r.cluster_avail_vCPUs = cluster.avail_vCPUs
                    r.cluster_avail_mem = cluster.avail_mem_cap
                    r.cluster_avail_local_disk = cluster.avail_local_disk_cap

                    r.cluster_num_of_placed_vms = len(cluster.vm_list)

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

            lgr.num_of_placed_vms = len(lg.vm_list)
            for hk in lg.vms_per_host.keys():
                lgr.num_of_placed_vms_per_host[hk] = len(lg.vms_per_host[hk])

            self.avail_logical_groups[lgk] = lgr

    def _create_avail_storage_hosts(self):
        for shk, sh in self.resource.storage_hosts.iteritems():

            if sh.status != "enabled":
                continue

            sr = StorageResource()
            sr.storage_name = sh.name
            sr.storage_class = sh.storage_class 
            sr.storage_avail_disk = sh.avail_disk_cap

            self.avail_storage_hosts[sr.storage_name] = sr

    def _create_avail_switches(self):
        for sk, s in self.resource.switches.iteritems():

            if s.status != "enabled":
                continue

            sr = SwitchResource()
            sr.switch_name = s.name
            sr.switch_type = s.switch_type
            
            for ulk, ul in s.up_links.iteritems():
                sr.avail_bandwidths.append(ul.avail_nw_bandwidth) 

            # NOTE: peer_links?

            self.avail_switches[sk] = sr

    def _compute_resource_weights(self):
        denominator = 0.0
        for (t, w) in self.app_topology.optimization_priority:
            denominator += w

        for (t, w) in self.app_topology.optimization_priority:
            if t == "bw":
                self.nw_bandwidth_weight = float(w / denominator)
            elif t == "cpu":
                self.CPU_weight = float(w / denominator)
            elif t == "mem":
                self.mem_weight = float(w / denominator)
            elif t == "lvol":
                self.local_disk_weight = float(w / denominator)
            elif t == "vol":
                self.disk_weight = float(w / denominator)

        self.logger.debug("placement priority weights")
        for (r, w) in self.app_topology.optimization_priority:
            if r == "bw":
                self.logger.debug("    nw weight = " + str(self.nw_bandwidth_weight))
            elif r == "cpu":
                self.logger.debug("    cpu weight = " + str(self.CPU_weight))
            elif r == "mem":
                self.logger.debug("    mem weight = " + str(self.mem_weight))
            elif r == "lvol":
                self.logger.debug("    local disk weight = " + str(self.local_disk_weight))
            elif r == "vol":
                self.logger.debug("    disk weight = " + str(self.disk_weight))

    def _create_open_list(self, _vms, _volumes, _vgroups): 
        open_node_list = []
        level = "host"

        for vmk in _vms.keys():
            vm = _vms[vmk]
            n = Node()
            n.node = vm
            n.sort_base = self._set_virtual_capacity_based_sort(vm)
            open_node_list.append(n)

        for volk in _volumes.keys():
            volume = _volumes[volk]
            n = Node()
            n.node = volume
            n.sort_base = self._set_virtual_capacity_based_sort(volume)
            open_node_list.append(n)

        for gk in _vgroups.keys():
            g = _vgroups[gk]
            n = Node()
            if LEVELS.index(g.level) > LEVELS.index(level):
                level = g.level
            n.node = g
            n.sort_base = self._set_virtual_capacity_based_sort(g)
            open_node_list.append(n)

        return (open_node_list, level)

    def _set_virtual_capacity_based_sort(self, _v):
        sort_base = -1

        if isinstance(_v, Volume):
            sort_base = self.disk_weight * _v.volume_weight + \
                        self.nw_bandwidth_weight * _v.bandwidth_weight
        elif isinstance(_v, VM): 
            sort_base = self.nw_bandwidth_weight * _v.bandwidth_weight + \
                        self.CPU_weight * _v.vCPU_weight + \
                        self.mem_weight * _v.mem_weight + \
                        self.local_disk_weight * _v.local_volume_weight
        elif isinstance(_v, VGroup): 
            sort_base = self.nw_bandwidth_weight * _v.bandwidth_weight + \
                        self.CPU_weight * _v.vCPU_weight + \
                        self.mem_weight * _v.mem_weight + \
                        self.local_disk_weight * _v.local_volume_weight + \
                        self.disk_weight * _v.volume_weight
 
        return sort_base
        
    def _run_greedy(self, _open_node_list, _level, _avail_hosts):
        success = True

        avail_resources = {}
        if _level == "cluster":
            for hk, h in _avail_hosts.iteritems():
                if h.cluster_name not in avail_resources.keys():
                    avail_resources[h.cluster_name] = h
        elif _level == "rack":
            for hk, h in _avail_hosts.iteritems():
                if h.rack_name not in avail_resources.keys():
                    avail_resources[h.rack_name] = h
        elif _level == "host":
            avail_resources = _avail_hosts

        _open_node_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        self.logger.debug("the order of open node list in level = " + _level)
        for on in _open_node_list:
            self.logger.debug("    node = {}, value = {}".format(on.node.name, on.sort_base))

        while len(_open_node_list) > 0:
            n = _open_node_list.pop(0)
            self.logger.debug("level = " + _level)
            self.logger.debug("placing node = " + n.node.name)

            best_resource = self._get_best_resource(n, _level, avail_resources)
            if best_resource == None:
                success = False
                break

            debug_best_resource = None
            if _level == "cluster":
                debug_best_resource = best_resource.cluster_name
            elif _level == "rack":
                debug_best_resource = best_resource.rack_name
            elif _level == "host":
                if isinstance(n.node, VM) or isinstance(n.node, VGroup):
                    debug_best_resource = best_resource.host_name
                elif isinstance(n.node, Volume):
                    debug_best_resource = best_resource.host_name + "@" + best_resource.storage.storage_name
            self.logger.debug("best resource = " + debug_best_resource + " for node = " + n.node.name)

            # For VM or Volume under host level only
            self._deduct_reservation(_level, best_resource, n)
            # Close all types of nodes under any level, but VM or Volume with above host level
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

        self.logger.debug("candidate list")
        for c in candidate_list:
            self.logger.debug("    candidate = " + c.get_resource_name(_level))

        (target, weight) = self.app_topology.optimization_priority[0]
        top_candidate_list = None
        if target == "bw":
            constrained_list = []
            for cr in candidate_list:
                cr.sort_base = self._estimate_max_bandwidth(_level, _n, cr)
                if cr.sort_base == -1:
                    constrained_list.append(cr)
        
            for c in constrained_list:
                if c in candidate_list:
                    candidate_list.remove(c)
    
            if len(candidate_list) == 0:
                self.status = "no available network bandwidth left, for node = " + _n.node.name
                self.logger.error(self.status)
                return None

            candidate_list.sort(key=operator.attrgetter("sort_base"))
            top_candidate_list = self._sort_highest_consolidation(_n, _level, candidate_list)
        else:
            if target == "vol":
                if isinstance(_n.node, VGroup) or isinstance(_n.node, Volume):
                    volume_class = None
                    if isinstance(_n.node, Volume):
                        volume_class = _n.node.volume_class
                    else:
                        max_size = 0
                        for vck in _n.node.volume_sizes.keys():
                            if _n.node.volume_sizes[vck] > max_size:
                                max_size = _n.node.volume_sizes[vck]
                                volume_class = vck

                    self._set_disk_sort_base(_level, candidate_list, volume_class)
                    candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)
                else:
                    self._set_compute_sort_base(_level, candidate_list)
                    candidate_list.sort(key=operator.attrgetter("sort_base"))
            else:
                if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
                    self._set_compute_sort_base(_level, candidate_list)
                    candidate_list.sort(key=operator.attrgetter("sort_base"))
                else:
                    self._set_disk_sort_base(_level, candidate_list, _n.node.volume_class)
                    candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

            top_candidate_list = self._sort_lowest_bandwidth_usage(_n, _level, candidate_list)

            if len(top_candidate_list) == 0:
                self.status = "no available network bandwidth left"
                self.logger.error(self.status)
                return None

        best_resource = None
        if _level == "host" and (isinstance(_n.node, VM) or isinstance(_n.node, Volume)):
            best_resource = copy.deepcopy(top_candidate_list[0])
            best_resource.level = "host"
            if isinstance(_n.node, Volume):
                self._set_best_storage(_n, best_resource)
        else:
            while True:
 
                while len(top_candidate_list) > 0:
                    cr = top_candidate_list.pop(0)

                    vms = {}
                    volumes = {}
                    vgroups = {}
                    if isinstance(_n.node, VGroup):
                        if LEVELS.index(_n.node.level) < LEVELS.index(_level):
                            vgroups[_n.node.uuid] = _n.node
                        else:
                            for sg in _n.node.subvgroup_list:
                                if isinstance(sg, VM):
                                    vms[sg.uuid] = sg
                                elif isinstance(sg, Volume):
                                    volumes[sg.uuid] = sg
                                elif isinstance(sg, VGroup):
                                    vgroups[sg.uuid] = sg
                    else:
                        if isinstance(_n.node, VM):
                            vms[_n.node.uuid] = _n.node
                        elif isinstance(_n.node, Volume):
                            volumes[_n.node.uuid] = _n.node

                    (open_node_list, level) = self._create_open_list(vms, volumes, vgroups)
 
                    avail_hosts = {}
                    for hk, h in self.avail_hosts.iteritems():
                        if _level == "cluster":
                            if h.cluster_name == cr.cluster_name:
                                avail_hosts[hk] = h
                        elif _level == "rack":
                            if h.rack_name == cr.rack_name:
                                avail_hosts[hk] = h
                        elif _level == "host":
                            if h.host_name == cr.host_name:
                                avail_hosts[hk] = h

                    # Recursive call
                    if self._run_greedy(open_node_list, level, avail_hosts) == True:
                        best_resource = copy.deepcopy(cr)
                        best_resource.level = _level
                        break
                    else:
                        debug_candidate_name = None
                        if _level == "cluster":
                            debug_candidate_name = cr.cluster_name
                        elif _level == "rack":
                            debug_candidate_name = cr.rack_name
                        else:
                            debug_candidate_name = cr.host_name
                        self.logger.debug("rollback of candidate resource = " + debug_candidate_name)

                        # Recursively rollback deductions of all child VMs and Volumes of _n
                        self._rollback_reservation(_n.node)
                        # Recursively rollback closing
                        self._rollback_node_placement(_n.node)

                # After explore top candidate list for _n
                if best_resource != None:
                    break
                else:
                    if len(candidate_list) == 0:
                        self.status = "no available hosts"
                        self.logger.warn(self.status)
                        break
                    else:
                        if target == "bw":
                            top_candidate_list = self._sort_highest_consolidation(_n, _level, candidate_list)
                        else:
                            top_candidate_list = self._sort_lowest_bandwidth_usage(_n, _level, candidate_list)
                            if len(top_candidate_list) == 0:
                                self.status = "no available network bandwidth left"
                                self.logger.warn(self.status)
                                break
 
        return best_resource

    def _set_best_storage(self, _n, _resource):
        max_storage_size = 0
        for sk in _resource.host_avail_storages.keys():
            s = self.avail_storage_hosts[sk]
            if _n.node.volume_class == "any" or s.storage_class == _n.node.volume_class:
                if s.storage_avail_disk > max_storage_size:
                    max_storage_size = s.storage_avail_disk
                    _resource.storage = s

    def _sort_lowest_bandwidth_usage(self, _n, _level, _candidate_list):
        while True:
            top_candidate_list = []
            best_usage = _candidate_list[0].sort_base
            while len(_candidate_list) > 0:
                ch = _candidate_list.pop(0)
                if ch.sort_base == best_usage:
                    top_candidate_list.append(ch)
                else:
                    break

            constrained_list = []
            for c in top_candidate_list:
                c.sort_base = self._estimate_max_bandwidth(_level, _n, c)
                if c.sort_base == -1:
                    constrained_list.append(c)
        
            for c in constrained_list:
                if c in top_candidate_list:
                    top_candidate_list.remove(c)

            if len(top_candidate_list) > 0:
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
                break

            if len(_candidate_list) == 0:
                break

        return top_candidate_list

    def _sort_highest_consolidation(self, _n, _level, _candidate_list):
        top_candidate_list = []
        best_bandwidth_usage = _candidate_list[0].sort_base
        while len(_candidate_list) > 0:
            ch = _candidate_list.pop(0)
            if ch.sort_base == best_bandwidth_usage:
                top_candidate_list.append(ch)
            else:
                break

        target = None
        for (t, w) in self.app_topology.optimization_priority:
            if t != "bw":
                target = t
                break

        if target == "vol":
            if isinstance(_n.node, VGroup) or isinstance(_n.node, Volume):
                volume_class = None
                if isinstance(_n.node, Volume):
                    volume_class = _n.node.volume_class
                else:
                    max_size = 0
                    for vck in _n.node.volume_sizes.keys():
                        if _n.node.volume_sizes[vck] > max_size:
                            max_size = _n.node.volume_sizes[vck]
                            volume_class = vck
                self._set_disk_sort_base(_level, top_candidate_list, volume_class)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)
            else:
                self._set_compute_sort_base(_level, top_candidate_list)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
        else:
            if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
                self._set_compute_sort_base(_level, top_candidate_list)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"))
            else:
                self._set_disk_sort_base(_level, top_candidate_list, _n.node.volume_class)
                top_candidate_list.sort(key=operator.attrgetter("sort_base"), reverse=True)

        return top_candidate_list

    def _set_disk_sort_base(self, _level, _candidate_list, _class):
        for c in _candidate_list:
            avail_storages = {}
            if _level == "cluster":
                for sk in c.cluster_avail_storages.keys():
                    s = c.cluster_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s
            elif _level == "rack":
                for sk in c.rack_avail_storages.keys():
                    s = c.rack_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s
            elif _level == "host":
                for sk in c.host_avail_storages.keys():
                    s = c.host_avail_storages[sk]
                    if _class == "any" or s.storage_class == _class:
                        avail_storages[sk] = s
            
            current_max = 0
            for sk in avail_storages.keys():
                s = avail_storages[sk]
                if s.storage_avail_disk > current_max:
                    current_max = s.storage_avail_disk

            c.sort_base = current_max

    def _set_compute_sort_base(self, _level, _candidate_list):
        for c in _candidate_list:
            CPU_ratio = -1
            mem_ratio = -1
            local_disk_ratio = -1
            if _level == "cluster":
                CPU_ratio = float(c.cluster_avail_vCPUs) / float(self.resource.CPU_avail)
                mem_ratio = float(c.cluster_avail_mem) / float(self.resource.mem_avail)
                local_disk_ratio = float(c.cluster_avail_local_disk) / \
                                   float(self.resource.local_disk_avail)
            elif _level == "rack":
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
                          
    def _estimate_max_bandwidth(self, _level, _n, _candidate):
        nw_bandwidth_penalty = self._estimate_nw_bandwidth_penalty(_level, _n, _candidate)

        if nw_bandwidth_penalty >= 0:
            return nw_bandwidth_penalty
        else:
            return -1

    def _estimate_nw_bandwidth_penalty(self, _level, _n, _candidate):
        sort_base = 0 # Set bandwidth usage penalty by placement

        # To check the bandwidth constraint at the last moment
        # 3rd entry to be used for special node communicating beyond datacenter or zone
        req_bandwidths = [0, 0, 0]

        link_list = _n.get_all_links()
        
        placed_link_list = []
        for vl in link_list:
            for v in self.node_placements.keys():
                if v.uuid == vl.node.uuid:
                    placed_link_list.append(vl)

                    bandwidth = _n.get_bandwidth_of_link(vl)
                    placement_level = _candidate.get_common_placement(self.node_placements[v])
                    if placement_level != "ANY" and LEVELS.index(placement_level) >= LEVELS.index(_level):
                        sort_base += compute_reservation(_level, placement_level, bandwidth)
                        self.constraint_solver.get_req_bandwidths(_level, \
                                                                  placement_level, \
                                                                  bandwidth, \
                                                                  req_bandwidths)

        candidate = copy.deepcopy(_candidate) 

        exclusivity_id = _n.get_exclusivity_id()
        temp_exclusivity_insert = False 
        if exclusivity_id != None:
            if exclusivity_id not in self.avail_logical_groups.keys():
                temp_lgr = LogicalGroupResource()
                temp_lgr.name = exclusivity_id
                temp_lgr.group_type = "EX"

                self.avail_logical_groups[exclusivity_id] = temp_lgr
                temp_exclusivity_insert = True

            self._add_exclusivity_to_candidate(_level, candidate, exclusivity_id) 

        affinity_id = _n.get_affinity_id()
        temp_affinity_insert = False 
        if affinity_id != None:
            if affinity_id not in self.avail_logical_groups.keys():
                temp_lgr = LogicalGroupResource()
                temp_lgr.name = affinity_id
                temp_lgr.group_type = "AFF"

                self.avail_logical_groups[affinity_id] = temp_lgr
                temp_affinity_insert = True

            self._add_affinity_to_candidate(_level, candidate, affinity_id)

        self._deduct_reservation_from_candidate(candidate, _n, req_bandwidths, _level)

        handled_vgroups = {}
        for vl in link_list:
            if vl in placed_link_list:
                continue

            bandwidth = _n.get_bandwidth_of_link(vl)

            diversity_level = _n.get_common_diversity(vl.node.diversity_groups)
            if diversity_level == "ANY":
                implicit_diversity = self.constraint_solver.get_implicit_diversity(_n.node, \
                                                                                   link_list, \
                                                                                   vl.node, \
                                                                                   _level)
                if implicit_diversity[0] != None:
                    diversity_level = implicit_diversity[1]
            if diversity_level == "ANY" or LEVELS.index(diversity_level) < LEVELS.index(_level):
                vg = self._get_top_vgroup(vl.node, _level)
                if vg.uuid not in handled_vgroups.keys(): 
                    handled_vgroups[vg.uuid] = vg

                    temp_n = Node()
                    temp_n.node = vg
                    temp_req_bandwidths = [0, 0, 0]
                    self.constraint_solver.get_req_bandwidths(_level, _level, bandwidth, temp_req_bandwidths)

                    if self._check_availability(_level, temp_n, candidate) == True:
                        self._deduct_reservation_from_candidate(candidate, temp_n, temp_req_bandwidths, _level)
                    else:
                        sort_base += compute_reservation(_level, _level, bandwidth)
                        req_bandwidths[0] += temp_req_bandwidths[0]
                        req_bandwidths[1] += temp_req_bandwidths[1]
                        req_bandwidths[2] += temp_req_bandwidths[2]
            else:
                self.constraint_solver.get_req_bandwidths(_level, diversity_level, bandwidth, req_bandwidths)
                sort_base += compute_reservation(_level, diversity_level, bandwidth) 

        if self.constraint_solver._check_nw_bandwidth_availability(_level, req_bandwidths, _candidate) == False:
            sort_base = -1

        if temp_exclusivity_insert == True:
            del self.avail_logical_groups[exclusivity_id]

        if temp_affinity_insert == True:
            del self.avail_logical_groups[affinity_id]

        return sort_base

    def _add_exclusivity_to_candidate(self, _level, _candidate, _exclusivity_id):
        lgr = self.avail_logical_groups[_exclusivity_id]

        if _level == "host":
            if _exclusivity_id not in _candidate.host_memberships.keys():
                _candidate.host_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr
        elif _level == "rack": 
            if _exclusivity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_exclusivity_id] = lgr
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr
        elif _level == "cluster": 
            if _exclusivity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_exclusivity_id] = lgr

    def _add_affinity_to_candidate(self, _level, _candidate, _affinity_id):
        lgr = self.avail_logical_groups[_affinity_id]

        if _level == "host":
            if _affinity_id not in _candidate.host_memberships.keys():
                _candidate.host_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr
        elif _level == "rack": 
            if _affinity_id not in _candidate.rack_memberships.keys():
                _candidate.rack_memberships[_affinity_id] = lgr
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr
        elif _level == "cluster": 
            if _affinity_id not in _candidate.cluster_memberships.keys():
                _candidate.cluster_memberships[_affinity_id] = lgr

    def _get_top_vgroup(self, _v, _level):
        vg = _v.survgroup

        if vg == None:
            return _v
        
        if LEVELS.index(vg.level) > LEVELS.index(_level):
            return _v
  
        return self._get_top_vgroup(vg, _level)

    def _check_availability(self, _level, _n, _candidate):
        if isinstance(_n.node, VM):
            if self.constraint_solver.check_compute_availability(_level, _n.node, _candidate) == False:
                return False
        elif isinstance(_n.node, Volume):
            if self.constraint_solver.check_storage_availability(_level, _n.node, _candidate) == False:
                return False
        else:
            if self.constraint_solver.check_compute_availability(_level, _n.node, _candidate) == False or \
               self.constraint_solver.check_storage_availability(_level, _n.node, _candidate) == False:
                return False

        if self.constraint_solver.check_nw_bandwidth_availability(_level, \
                                                                  _n, \
                                                                  self.node_placements, \
                                                                  _candidate) == False:
            return False

        if len(_n.node.host_aggregates) > 0:
            if self.constraint_solver.check_host_aggregates(_level, _n.node, _candidate) == False:
                return False
        else:
            if _level == "host":
                if self.constraint_solver.conflict_host_aggregates(_candidate.memberships) == True:
                    return False

        if self.constraint_solver.conflict_diversity(_level, _n, self.node_placements, _candidate) == True:
            return False

        exc_id = _n.get_exclusivity_id()
        if exc_id == None:
            exc_id = _n.get_parent_exclusivity_id()
            if exc_id == None:
                if self.constraint_solver.conflict_exclusivity(_level, _candidate) == True:
                    return False
            else: # no way to check
                pass
        else:
            if self.constraint_solver.check_exclusivity(_level, exc_id, _candidate) == False:
                return False

        aff_id = _n.get_affinity_id()
        if aff_id != None:
            if aff_id in self.avail_logical_groups.keys():
                if self.constraint_solver.check_affinity(_level, _aff_id, _candidate) == False:
                    return False

        return True

    def _deduct_reservation_from_candidate(self, _candidate, _n, _rsrv, _level):
        if isinstance(_n.node, VM) or isinstance(_n.node, VGroup):
            self._deduct_candidate_vm_reservation(_level, _n.node, _candidate)

        if isinstance(_n.node, Volume) or isinstance(_n.node, VGroup):
            self._deduct_candidate_volume_reservation(_level, _n.node, _candidate)

        self._deduct_candidate_nw_reservation(_candidate, _rsrv)

    def _deduct_candidate_vm_reservation(self, _level, _v, _candidate):
        is_vm_included = False
        if isinstance(_v, VM):
            is_vm_included = True
        elif isinstance(_v, VGroup):
            is_vm_included = self._check_vm_included(_v)

        if _level == "cluster":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.cluster_num_of_placed_vms += 1
        elif _level == "rack":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.cluster_num_of_placed_vms += 1
            _candidate.rack_avail_vCPUs -= _v.vCPUs
            _candidate.rack_avail_mem -= _v.mem
            _candidate.rack_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.rack_num_of_placed_vms += 1
        elif _level == "host":
            _candidate.cluster_avail_vCPUs -= _v.vCPUs
            _candidate.cluster_avail_mem -= _v.mem
            _candidate.cluster_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.cluster_num_of_placed_vms += 1
            _candidate.rack_avail_vCPUs -= _v.vCPUs
            _candidate.rack_avail_mem -= _v.mem
            _candidate.rack_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.rack_num_of_placed_vms += 1
            _candidate.host_avail_vCPUs -= _v.vCPUs
            _candidate.host_avail_mem -= _v.mem
            _candidate.host_avail_local_disk -= _v.local_volume_size
            if is_vm_included == True:
                _candidate.host_num_of_placed_vms += 1

    def _check_vm_included(self, _v):
        is_vm_included = False

        for sv in _v.subvgroup_list:
            if isinstance(sv, VM):
                is_vm_included = True
                break
            elif isinstance(sv, VGroup):
                is_vm_included = self._check_vm_included(sv)
                if is_vm_included == True:
                    break

        return is_vm_included

    def _deduct_candidate_volume_reservation(self, _level, _v, _candidate):
        volume_sizes = []
        if isinstance(_v, VGroup):
            for vck in _v.volume_sizes.keys():
                volume_sizes.append((vck, _v.volume_sizes[vck]))
        else:
            volume_sizes.append((_v.volume_class, _v.volume_size))

        for (vc, vs) in volume_sizes:
            max_size = 0
            selected_storage = None
            if _level == "cluster":
                for sk in _candidate.cluster_avail_storages.keys():
                    s = _candidate.cluster_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc: 
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs
            elif _level == "rack":
                for sk in _candidate.rack_avail_storages.keys():
                    s = _candidate.rack_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc: 
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs
            elif _level == "host":
                for sk in _candidate.host_avail_storages.keys():
                    s = _candidate.host_avail_storages[sk]
                    if vc == "any" or s.storage_class == vc:
                        if s.storage_avail_disk > max_size:
                            max_size = s.storage_avail_disk
                            selected_storage = s
                selected_storage.storage_avail_disk -= vs

    def _deduct_candidate_nw_reservation(self, _candidate, _rsrv):
        for srk in _candidate.host_avail_switches.keys():
            sr = _candidate.host_avail_switches[srk]
            sr.avail_bandwidths = [bw - _rsrv[0] for bw in sr.avail_bandwidths]    
             
        for srk in _candidate.rack_avail_switches.keys():
            sr = _candidate.rack_avail_switches[srk]
            sr.avail_bandwidths = [bw - _rsrv[1] for bw in sr.avail_bandwidths]    
             
        for srk in _candidate.cluster_avail_switches.keys():
            sr = _candidate.cluster_avail_switches[srk]
            if sr.switch_type == "spine":
                sr.avail_bandwidths = [bw - _rsrv[2] for bw in sr.avail_bandwidths]    
 
    def _deduct_reservation(self, _level, _best, _n):
        exclusivity_id = _n.get_exclusivity_id()
        if exclusivity_id != None:
            self._add_exclusivity(_level, _best, exclusivity_id)

        affinity_id = _n.get_affinity_id()
        if affinity_id != None:
            self._add_affinity(_level, _best, affinity_id)

        if isinstance(_n.node, VM) and _level == "host":
            self._deduct_vm_resources(_best, _n)
        elif isinstance(_n.node, Volume) and _level == "host":
            self._deduct_volume_resources(_best, _n)

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
        elif _level == "cluster": 
            for npk, np in self.avail_hosts.iteritems():
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
        elif _level == "cluster": 
            for npk, np in self.avail_hosts.iteritems():
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

    def _deduct_volume_resources(self, _best, _n):
        storage_host = self.avail_storage_hosts[_best.storage.storage_name]
        storage_host.storage_avail_disk -= _n.node.volume_size

        chosen_host = self.avail_hosts[_best.host_name]

        for vml in _n.node.vm_list:
            if vml.node in self.node_placements.keys():
                cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                placement_level = cn.get_common_placement(chosen_host)
                bandwidth = vml.io_bandwidth
                self.bandwidth_usage += self._deduct_nw_reservation(placement_level, chosen_host, cn, bandwidth)
            
    def _deduct_nw_reservation(self, _placement_level, _host1, _host2, _rsrv):
        nw_reservation = compute_reservation("host", _placement_level, _rsrv)

        if _placement_level == "host":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
        elif _placement_level == "rack":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths] 
   
            for srk, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths] 
        elif _placement_level == "cluster":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths] 
   
            for srk, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths] 

            for srk, sr in _host1.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths]    
            for srk, sr in _host2.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw - _rsrv for bw in sr.avail_bandwidths] 
  
        return nw_reservation

    def _close_node_placement(self, _level, _best, _v):
        if _level == "host": 
            self.node_placements[_v] = _best
        else:
            if isinstance(_v, VGroup):
                self.node_placements[_v] = _best

    def _rollback_reservation(self, _v):
        if isinstance(_v, VM):
            self._rollback_vm_reservation(_v)

        elif isinstance(_v, Volume):
            self._rollback_volume_reservation(_v)

        elif isinstance(_v, VGroup):
            if _v in self.node_placements.keys():
                if _v.vgroup_type == "EX":
                    exclusivity_id = _v.level + ":" + _v.name
                    chosen_host = self.avail_hosts[self.node_placements[_v].host_name]

                    self._remove_exclusivity(chosen_host, exclusivity_id, self.node_placements[_v].level) 

                if _v.vgroup_type == "AFF":
                    affinity_id = _v.level + ":" + _v.name
                    chosen_host = self.avail_hosts[self.node_placements[_v].host_name]

                    self._remove_affinity(chosen_host, affinity_id, self.node_placements[_v].level)

            for v in _v.subvgroup_list:
                self._rollback_reservation(v) 

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

        elif _level == "cluster": 
            if _chosen_host.cluster_num_of_placed_vms == 0:
                for npk, np in self.avail_hosts.iteritems():
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

        elif _level == "cluster": 
            if exist_affinity == False:
                for npk, np in self.avail_hosts.iteritems():
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

    def _rollback_volume_reservation(self, _v):
        if _v in self.node_placements.keys():
            cs = self.node_placements[_v]
            storage_host = self.avail_storage_hosts[cs.storage.storage_name]
            storage_host.storage_avail_disk += _v.volume_size

            chosen_host = self.avail_hosts[self.node_placements[_v].host_name]

            for vml in _v.vm_list:
                if vml.node in self.node_placements.keys():
                    cn = self.avail_hosts[self.node_placements[vml.node].host_name]
                    level = cn.get_common_placement(chosen_host)
                    bandwidth = vml.io_bandwidth
                    self.bandwidth_usage -= self._rollback_nw_reservation(level, chosen_host, cn, bandwidth)

    def _rollback_nw_reservation(self, _level, _host1, _host2, _rsrv):
        nw_reservation = compute_reservation("host", _level, _rsrv)

        if _level == "host":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
        elif _level == "rack":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for srk, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
        elif _level == "cluster":
            for srk, sr in _host1.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.host_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for srk, sr in _host1.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.rack_avail_switches.iteritems():
                sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

            for srk, sr in _host1.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]
            for srk, sr in _host2.cluster_avail_switches.iteritems():
                if sr.switch_type == "spine":
                    sr.avail_bandwidths = [bw + _rsrv for bw in sr.avail_bandwidths]

        return nw_reservation

    def _rollback_node_placement(self, _v):
        if _v in self.node_placements.keys():
            del self.node_placements[_v]

        if isinstance(_v, VGroup):
            for sg in _v.subvgroup_list:
                self._rollback_node_placement(sg)





