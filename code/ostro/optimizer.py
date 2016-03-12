#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Perform constrained optimization solving using search algorithm
#
#################################################################################################################


import time
import sys

from search import Search

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, Volume

sys.path.insert(0, '../resource_manager')
from resource_base import LogicalGroup


class Optimizer:

    def __init__(self, _resource, _logger):
        self.resource = _resource

        self.logger = _logger

        self.search = Search(self.logger)

        self.status = "success"

    def place(self, _app_topology): 
        placement_map = self._place_nodes(_app_topology)
        if len(placement_map) > 0:
            return placement_map
        else:
            return None

    def _place_nodes(self, _app_topology):
        start_ts = time.time() 
        success = self.search.place_nodes(_app_topology, self.resource)
        end_ts = time.time()

        if success == True:
            self.logger.info("search running time = " + str(end_ts - start_ts) + " sec")
            self.logger.info("total bandwidth reservation to be made = " + str(self.search.bandwidth_usage))
            self.logger.info("total number of hosts to be used = " + str(self.search.num_of_hosts))

            placement_map = {}
            for v in self.search.node_placements.keys(): 
                if isinstance(v, VM):
                    placement_map[v] = self.search.node_placements[v].host_name
                if isinstance(v, Volume):
                    placement_map[v] = self.search.node_placements[v].host_name + "@" + \
                                       self.search.node_placements[v].storage.storage_name
            
            self._update_resource_status()

            return placement_map

        else:
            self.status = self.search.status
            return {}

    def _update_resource_status(self):
        for v, np in self.search.node_placements.iteritems():

            if isinstance(v, VM):
                host = self.resource.hosts[np.host_name]

                host.vm_list.append((v.uuid, v.name, "none"))  

                host.avail_vCPUs -= v.vCPUs
                host.avail_mem_cap -= v.mem
                host.avail_local_disk_cap -= v.local_volume_size

                for vl in v.vm_list:
                    tnp = self.search.node_placements[vl.node]

                    placement_level = np.get_common_placement(tnp)

                    self._update_bandwidth_availability(host, placement_level, vl.nw_bandwidth)

                for voll in v.volume_list:
                    tnp = self.search.node_placements[voll.node]

                    placement_level = np.get_common_placement(tnp)

                    self._update_bandwidth_availability(host, placement_level, voll.io_bandwidth)

                self._update_logical_grouping(v, self.search.avail_hosts[np.host_name])

                host.last_update = time.time()
                self.resource.update_rack_resource(host)

            elif isinstance(v, Volume):
                host = self.resource.hosts[np.host_name]

                host.volume_list.append(v.name)

                storage_host = self.resource.storage_hosts[np.storage.storage_name]
                storage_host.volume_list.append(v.name)

                storage_host.avail_disk_cap -= v.volume_size

                for vl in v.vm_list:
                    tnp = self.search.node_placements[vl.node]

                    placement_level = np.get_common_placement(tnp)

                    self._update_bandwidth_availability(host, placement_level, vl.io_bandwidth)

                storage_host.last_cap_update = time.time()

    # NOTE: Assume the up-link of spine switch is not used except out-going from datacenter
    # NOTE: What about peer-switches?
    def _update_bandwidth_availability(self, _host, _placement_level, _bandwidth):
        if _placement_level == "host":
            self._deduct_host_bandwidth(_host, _bandwidth)

        elif _placement_level == "rack":
            self._deduct_host_bandwidth(_host, _bandwidth)

            rack = _host.host_group
            if isinstance(rack, Datacenter):
                pass
            else:
                self._deduct_host_bandwidth(rack, _bandwidth)

        elif _placement_level == "cluster":
            self._deduct_host_bandwidth(_host, _bandwidth)

            rack = _host.host_group
            self._deduct_host_bandwidth(rack, _bandwidth)

            cluster = rack.parent_resource
            for sk, s in cluster.switches.iteritems():
                if s.switch_type == "spine":
                    for ulk, ul in s.up_links.iteritems():
                        ul.avail_nw_bandwidth -= _bandwidth
        
                    s.last_update = time.time()

    def _deduct_host_bandwidth(self, _host, _bandwidth):
        for hsk, hs in _host.switches.iteritems():
            for ulk, ul in hs.up_links.iteritems():
                ul.avail_nw_bandwidth -= _bandwidth

            hs.last_update = time.time()

    def _update_logical_grouping(self, _v, _avail_host):
        host = self.resource.hosts[_avail_host.host_name]

        for lgk, lg in _avail_host.host_memberships.iteritems():
            if lg.group_type == "EX" or lg.group_type == "AFF":
                if lgk.split(":")[0] == "host":
                    if lgk not in self.resource.logical_groups.keys():
                        self.resource.logical_groups[lgk] = LogicalGroup(lgk)
                        self.resource.logical_groups[lgk].group_type = lg.group_type
                        self.resource.logical_groups[lgk].last_update = time.time()

                    if lgk not in host.memberships.keys():
                        host.memberships[lgk] = self.resource.logical_groups[lgk]

        if _avail_host.rack_name != "any":
            for lgk, lg in _avail_host.rack_memberships.iteritems():
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if lgk.split(":")[0] == "rack":
                        if lgk not in self.resource.logical_groups.keys():
                            self.resource.logical_groups[lgk] = LogicalGroup(lgk)
                            self.resource.logical_groups[lgk].group_type = lg.group_type
                            self.resource.logical_groups[lgk].last_update = time.time()

                        rack = self.resource.host_groups[_avail_host.rack_name]
                        if lgk not in rack.memberships.keys():
                            rack.memberships[lgk] = self.resource.logical_groups[lgk]
                            rack.last_update = time.time()
                            self.resource.update_cluster_resource(rack)

        if _avail_host.cluster_name != "any":
            for lgk, lg in _avail_host.cluster_memberships.iteritems():
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if lgk.split(":")[0] == "cluster":
                        if lgk not in self.resource.logical_groups.keys():
                            self.resource.logical_groups[lgk] = LogicalGroup(lgk)
                            self.resource.logical_groups[lgk].group_type = lg.group_type
                            self.resource.logical_groups[lgk].last_update = time.time()

                        cluster = self.resource.host_groups[_avail_host.cluster_name]
                        if lgk not in cluster.memberships.keys():
                            cluster.memberships[lgk] = self.resource.logical_groups[lgk]
                            cluster.last_update = time.time()
                            self.resource.update_cluster_resource(cluster)

        vm_logical_groups = []
        self._collect_logical_groups_of_vm(_v, vm_logical_groups)

        self.resource.add_vm_to_logical_groups(host, (_v.uuid, _v.name, "none"), vm_logical_groups)

    def _collect_logical_groups_of_vm(self, _v, _vm_logical_groups):
        # availability_zone
        # integrity_zones
        for hgk in _v.host_aggregates.keys():
            _vm_logical_groups.append(hgk)
  
        if isinstance(_v, VGroup):
            _vm_logical_groups.append(_v.level + ":" + _v.name)

        if _v.survgroup != None:
            self._collect_logical_groups_of_vm(_v.survgroup, _vm_logical_groups)












