#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Dec. 7, 2015
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
        for v in self.search.node_placements.keys():
            np = self.search.node_placements[v]

            if isinstance(v, VGroup):
                if v.vgroup_type != "EX":
                    continue

                if v.level == "host":
                    host = self.resource.hosts[np.host_name]
                    for mk in np.host_memberships.keys():
                        if np.host_memberships[mk] == "EX":
                            level = mk.split(:)[0]
                            if level == v.level:
                                if mk not in self.resource.logical_groups.keys():
                                    self.resource.logical_groups[mk] = LogicalGroup(mk)
                                    self.resource.logical_groups[mk].group_type = "EX"
                                if mk not in host.memberships.keys():
                                    host.memberships[mk] = self.resource.logical_groups[mk]
                                    host.last_update = time.time()
                                    self.resource.update_rack_resource(host)
                elif v.level == "rack":
                    host_group = self.resource.host_groups[np.rack_name]
                    for mk in np.rack_memberships.keys():
                        if np.rack_memberships[mk] == "EX":
                            level = mk.split(:)[0]
                            if level == v.level:
                                if mk not in self.resource.logical_groups.keys():
                                    self.resource.logical_groups[mk] = LogicalGroup(mk)
                                    self.resource.logical_groups[mk].group_type = "EX"
                                if mk not in host_group.memberships.keys():
                                    host_group.memberships[mk] = self.resource.logical_groups[mk]
                                    host_group.last_update = time.time()
                                    self.resource.update_cluster_resource(host_group)
                elif v.level == "cluster":
                    host_group = self.resource.host_groups[np.cluster_name]
                    for mk in np.cluster_memberships.keys():
                        if np.cluster_memberships[mk] == "EX":
                            level = mk.split(:)[0]
                            if level == v.level:
                                if mk not in self.resource.logical_groups.keys():
                                    self.resource.logical_groups[mk] = LogicalGroup(mk)
                                    self.resource.logical_groups[mk].group_type = "EX"
                                if mk not in host_group.memberships.keys():
                                    host_group.memberships[mk] = self.resource.logical_groups[mk]
                                    host_group.last_update = time.time()
                                    self.resource.update_cluster_resource(host_group)

            elif isinstance(v, VM):
                host = self.resource.hosts[np.host_name]

                host.vm_list.append(v.name)  # Use name, not uuid, because uuid is not recoginized later
                host.avail_vCPUs -= v.vCPUs
                host.avail_mem_cap -= v.mem
                host.avail_local_disk_cap -= v.local_volume_size

                for vl in v.vm_list:
                    tnp = self.search.node_placements[vl.node]

                    placement_level = np.get_common_placement(tnp)

                    bandwidth = vl.nw_bandwidth
                    if bandwidth < 0:
                        bandwidth = 0

                    self._update_bandwidth_availability(host, placement_level, bandwidth)

                for voll in v.volume_list:
                    tnp = self.search.node_placements[voll.node]

                    placement_level = np.get_common_placement(tnp)

                    bandwidth = voll.io_bandwidth
                    if bandwidth < 0:
                        bandwidth = 0

                    self._update_bandwidth_availability(host, placement_level, bandwidth)

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

                    bandwidth = vl.io_bandwidth
                    if bandwidth < 0:
                        bandwidth = 0

                    self._update_bandwidth_availability(host, placement_level, bandwidth)

                storage_host.last_cap_update = time.time()

    # NOTE: assume the up-link of spine switch is not used except out-going from datacenter
    # NOTE: what about peer-switches?
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
            for sk in cluster.switches.keys():
                s = cluster.switches[sk]
                if s.switch_type == "spine":
                    for ulk in s.up_links.keys():
                        ul = s.up_links[ulk]
                        ul.avail_nw_bandwidth -= _bandwidth
        
                    s.last_update = time.time()

    def _deduct_host_bandwidth(self, _host, _bandwidth):
        for hsk in _host.switches.keys():
            hs = _host.switches[hsk]
            for ulk in hs.up_links.keys():
                ul = hs.up_links[ulk]
                ul.avail_nw_bandwidth -= _bandwidth

            hs.last_update = time.time()





    
