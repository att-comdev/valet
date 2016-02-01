#!/bin/python


################################################################################################################ 
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Dec. 7, 2015
#
# Functions 
# - Keep the latest resource status in memory (topology and metadata)
# - Store updated resources into Cassandra database
#
################################################################################################################ 


import sys
import time

from resource_base import HostGroup, Host

sys.path.insert(0, '../app_manager')
from app_topology_base import LEVELS


class Resource:

    def __init__(self, _db, _logger):
        self.current_timestamp = 0
        #self.current_metadata_timestamp = 0

        # Resource data
        self.datacenter = None
        self.host_groups = {}
        self.hosts = {}
        self.switches = {}
        self.storage_hosts = {}

        # Metadata
        self.logical_groups = {}
        self.flavors = {}

        self.CPU_avail = 0
        self.mem_avail = 0
        self.local_disk_avail = 0
        self.disk_avail = 0
        self.nw_bandwidth_avail = 0

        self.db = _db
        self.logger = _logger

    #def update_metadata(self):
        #self.current_metadata_timestamp = self._store_metadata_updates()

    def update_topology(self):
        self._update_topology()

        self._update_compute_avail()
        self._update_storage_avail()
        self._update_nw_bandwidth_avail()

        self.current_timestamp = self._store_topology_updates()

    #def _store_metadata_updates(self):
        #last_ts = self.current_metadata_timestamp

        #for fk in self.flavors.keys():
            #flavor = self.flavors[fk]
            #if flavor.last_update > self.current_metadata_timestamp:
                #self.logger.debug("*** flavor name = " + flavor.name)
                #self.logger.debug("metadata update time = " + str(flavor.last_update))

                #self.logger.debug("vCPUs = " + str(flavor.vCPUs))
                #self.logger.debug("mem = " + str(flavor.mem_cap))
                #self.logger.debug("local disk = " + str(flavor.disk_cap))

                #if flavor.last_update > last_ts:
                    #last_ts = flavor.last_update

        #for hk in self.hosts.keys():
            #host = self.hosts[hk]
            #if host.last_metadata_update > self.current_metadata_timestamp:
                #self.logger.debug("*** host name = " + host.name)
                #self.logger.debug("metadata update time = " + str(host.last_metadata_update))

                #self.logger.debug("host zone = " + host.zone)
                #self.logger.debug("host exclusive = " + host.exclusive)
                #aggregates = ""
                #for ak in host.aggregates.keys():
                    #aggregates += ak + ','
                #self.logger.debug("host aggregate = " + aggregates)

                #if host.last_metadata_update > last_ts:
                    #last_ts = host.last_metadata_update

        #for hgk in self.host_groups.keys():
            #host_group = self.host_groups[hgk]
            #if host_group.last_metadata_update > self.current_metadata_timestamp:
                #self.logger.debug("*** host_group name = " + host_group.name)
                #self.logger.debug("metadata update time = " + str(host_group.last_metadata_update))

                #self.logger.debug("group exclusive = " + host_group.exclusive)

                #if host_group.last_metadata_update > last_ts:
                    #last_ts = host_group.last_metadata_update

        #return last_ts

    def _store_topology_updates(self):
        last_ts = self.current_timestamp

        for shk in self.storage_hosts.keys():
            storage_host = self.storage_hosts[shk]
            if storage_host.last_update > self.current_timestamp or \
               storage_host.last_cap_update > self.current_timestamp:
                self.logger.debug("*** storage host name = " + storage_host.name)
                self.logger.debug("topology update time = " + str(storage_host.last_update))
                self.logger.debug("cap update time = " + str(storage_host.last_cap_update))

                self.logger.debug("storage host status = " + storage_host.status)
                self.logger.debug("storage host class = " + storage_host.storage_class)

                self.logger.debug("storage host avail disk = " + str(storage_host.avail_disk_cap))

                for vol_name in storage_host.volume_list:
                    self.logger.debug("hosted volume = " + vol_name)

                if storage_host.last_update > last_ts:
                    last_ts = storage_host.last_update
                if storage_host.last_cap_update > last_ts:
                    last_ts = storage_host.last_cap_update

        for sk in self.switches.keys():
            s = self.switches[sk]
            if s.last_update > self.current_timestamp:
                self.logger.debug("*** switch name = " + s.name)
                self.logger.debug("switch update time = " + str(s.last_update))

                self.logger.debug("type = " + s.switch_type)
                self.logger.debug("status = " + s.status)
                for ulk in s.up_links.keys():
                    ul = s.up_links[ulk]
                    self.logger.debug("up link = " + ul.name + " bandwidth = " + str(ul.avail_nw_bandwidth))
                for plk in s.peer_links.keys():
                    pl = s.peer_links[plk]
                    self.logger.debug("peer link = " + pl.name + " bandwidth = " + str(pl.avail_nw_bandwidth))

                if s.last_update > last_ts:
                    last_ts = s.last_update

        for hk in self.hosts.keys():
            host = self.hosts[hk]
            if host.last_update > self.current_timestamp or host.last_link_update > self.current_timestamp:
                self.logger.debug("*** host name = " + host.name)
                self.logger.debug("topology update time = " + str(host.last_update))
                self.logger.debug("link update time = " + str(host.last_link_update))

                host_tag_list = ""
                for t in host.tag:
                    host_tag_list += t + ","
                self.logger.debug("host tag = " + host_tag_list)
                self.logger.debug("host status = " + host.status)
                self.logger.debug("host state = " + host.state)

                for mk in host.memberships.keys():
                    m = self.logical_groups[mk]
                    self.logger.debug("host logical group = " + m.name)

                self.logger.debug("host avail vCPUs = " + str(host.avail_vCPUs))
                self.logger.debug("host avail mem = " + str(host.avail_mem_cap))
                self.logger.debug("host avail local disk = " + str(host.avail_local_disk_cap))

                for sk in host.switches.keys():
                    s = self.switches[sk]
                    self.logger.debug("host switch = " + s.name)

                for shk in host.storages.keys(): 
                    storage_host = self.storage_hosts[shk]
                    self.logger.debug("storage = " + storage_host.name)

                self.logger.debug("group = " + host.host_group.name)

                for vm_name in host.vm_list:
                    self.logger.debug("hosted vm = " + vm_name)

                for vol_name in host.volume_list:
                    self.logger.debug("hosted volume = " + vol_name)

                if host.last_update > last_ts:
                    last_ts = host.last_update
                if host.last_link_update > last_ts:
                    last_ts = host.last_link_update

        for hgk in self.host_groups.keys():
            host_group = self.host_groups[hgk]
            if host_group.last_update > self.current_timestamp or \
               host_group.last_link_update > self.current_timestamp:
                self.logger.debug("*** host_group name = " + host_group.name)
                self.logger.debug("topology update time = " + str(host_group.last_update))
                self.logger.debug("link update time = " + str(host_group.last_link_update))

                self.logger.debug("type = " + host_group.host_type)

                self.logger.debug("status = " + host_group.status)

                for mk in host_group.memberships.keys():
                    m = self.logical_groups[mk]
                    self.logger.debug("host_group logical group = " + m.name)

                self.logger.debug("avail vCPUs = " + str(host_group.avail_vCPUs))
                self.logger.debug("avail mem = " + str(host_group.avail_mem_cap))
                self.logger.debug("avail local disk = " + str(host_group.avail_local_disk_cap))

                for sk in host_group.switches.keys():
                    s = self.switches[sk] 
                    self.logger.debug("switch = " + s.name)

                for shk in host_group.storages.keys(): 
                    storage_host = self.storage_hosts[shk]
                    self.logger.debug("storage = " + storage_host.name)

                self.logger.debug("parent resource = " + host_group.parent_resource.name)
                  
                for drk in host_group.child_resources.keys():
                    dr = host_group.child_resources[drk]
                    self.logger.debug("child resource = " + dr.name)
                  
                for vm_name in host_group.vm_list:
                    self.logger.debug("hosted vm = " + vm_name)

                for vol_name in host_group.volume_list:
                    self.logger.debug("hosted volume = " + vol_name)

                if host_group.last_update > last_ts:
                    last_ts = host_group.last_update
                if host_group.last_link_update > last_ts:
                    last_ts = host_group.last_link_update

        if self.datacenter.last_update > self.current_timestamp or \
           self.datacenter.last_link_update > self.current_timestamp:
            self.logger.debug("*** datacenter name = " + self.datacenter.name)
            self.logger.debug("topology update time = " + str(self.datacenter.last_update))
            self.logger.debug("topology link update time = " + str(self.datacenter.last_link_update))

            for mk in self.datacenter.memberships.keys():
                m = self.logical_groups[mk]
                self.logger.debug("datacenter logical group = " + m.name)

            self.logger.debug("datacenter avail vCPUs = " + str(self.datacenter.avail_vCPUs))
            self.logger.debug("datacenter avail mem = " + str(self.datacenter.avail_mem_cap))
            self.logger.debug("datacenter avail local disk = " + str(self.datacenter.avail_local_disk_cap))

            for sk in self.datacenter.root_switches.keys():
                s = self.switches[sk]
                self.logger.debug("switch = " + s.name)

            for shk in self.datacenter.storages.keys(): 
                storage_host = self.storage_hosts[shk]
                self.logger.debug("storage = " + storage_host.name)

            for rk in self.datacenter.resources.keys():
                r = self.datacenter.resources[rk]
                self.logger.debug("child resource = " + r.name)
                  
            for vm_name in self.datacenter.vm_list:
                self.logger.debug("hosted vm = " + vm_name)

            for vol_name in self.datacenter.volume_list:
                self.logger.debug("hosted volume = " + vol_name)

            if self.datacenter.last_update > last_ts:
                last_ts = self.datacenter.last_update
            if self.datacenter.last_link_update > last_ts:
                last_ts = self.datacenter.last_link_update

        return last_ts

    def _update_topology(self):
        for level in LEVELS:
            for hgk in self.host_groups.keys():
                host_group = self.host_groups[hgk]
                if host_group.host_type == level:
                    if host_group.check_availability() == True:
                        if host_group.last_update > self.current_timestamp:
                            self._update_host_group_topology(host_group)

        if self.datacenter.last_update > self.current_timestamp:
            self._update_datacenter_topology()

    def _update_host_group_topology(self, _host_group):
        _host_group.init_resources()
        del _host_group.vm_list[:]
        del _host_group.volume_list[:]
        _host_group.storages.clear()

        for hk in _host_group.child_resources.keys():
            host = _host_group.child_resources[hk]
            if host.check_availability() == True:
                _host_group.vCPUs += host.vCPUs
                _host_group.avail_vCPUs += host.avail_vCPUs
                _host_group.mem_cap += host.mem_cap
                _host_group.avail_mem_cap += host.avail_mem_cap
                _host_group.local_disk_cap += host.local_disk_cap
                _host_group.avail_local_disk_cap += host.avail_local_disk_cap

                for shk in host.storages.keys():
                    storage_host = host.storages[shk]
                    if storage_host.status == "enabled":
                        _host_group.storages[shk] = storage_host

                for vm_name in host.vm_list:
                    _host_group.vm_list.append(vm_name)

                for vol_name in host.volume_list:
                    _host_group.volume_list.append(vol_name)

        _host_group.memberships.init_memberships()

        for hk in _host_group.child_resources.keys():
            host = _host_group.child_resources[hk]
            if host.check_availability() == True:
                for mk in host.memberships.keys():
                    _host_group.memberships[mk] = host.memberships[mk]

    def _update_datacenter_topology(self):
        self.datacenter.init_resources()
        del self.datacenter.vm_list[:]
        del self.datacenter.volume_list[:]
        self.datacenter.storages.clear()
        self.datacenter.memberships.clear()

        for rk in self.datacenter.resources.keys():
            resource = self.datacenter.resources[rk]
            if resource.check_availability() == True:
                self.datacenter.vCPUs += resource.vCPUs
                self.datacenter.avail_vCPUs += resource.avail_vCPUs
                self.datacenter.mem_cap += resource.mem_cap
                self.datacenter.avail_mem_cap += resource.avail_mem_cap
                self.datacenter.local_disk_cap += resource.local_disk_cap
                self.datacenter.avail_local_disk_cap += resource.avail_local_disk_cap

                for shk in resource.storages.keys():
                    storage_host = resource.storages[shk]
                    if storage_host.status == "enabled":
                        self.datacenter.storages[shk] = storage_host

                for vm_name in resource.vm_list:
                    self.datacenter.vm_list.append(vm_name)

                for vol_name in resource.volume_list:
                    self.datacenter.volume_list.append(vol_name)

                for mk in resource.memberships.keys():
                    self.datacenter.memberships[mk] = resource.memberships[mk]

    def _update_compute_avail(self):
        self.CPU_avail = self.datacenter.avail_vCPUs
        self.mem_avail = self.datacenter.avail_mem_cap
        self.local_disk_avail = self.datacenter.avail_local_disk_cap

    def _update_storage_avail(self):
        self.disk_avail = 0

        for shk in self.storage_hosts.keys():
            storage_host = self.storage_hosts[shk]
            if storage_host.status == "enabled":
                self.disk_avail += storage_host.avail_disk_cap

    # Measure from the highest level
    def _update_nw_bandwidth_avail(self):
        self.nw_bandwidth_avail = 0

        level = "leaf"
        for sk in self.switches.keys():
            s = self.switches[sk]
            if s.status == "enabled":
                if level == "leaf": 
                    if s.switch_type == "ToR" or s.switch_type == "spine":
                        level = s.switch_type
                elif level == "ToR":
                    if s.switch_type == "spine":
                        level = s.switch_type
   
        if level == "leaf":
            self.nw_bandwidth_avail = sys.maxint
        elif level == "ToR":
            for hk in self.hosts.keys():
                h = self.hosts[hk]
                if h.status == "enabled" and h.state == "up" and \
                   ("nova" in h.tag) and ("infra" in h.tag):
                    avail_nw_bandwidth_list = []
                    for sk in h.switches.keys():
                        s = h.switches[sk]
                        if s.status == "enabled":
                            for ulk in s.up_links.keys():
                                ul = s.up_links[ulk]
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)
        elif level == "spine":
            for hgk in self.host_groups.keys():
                hg = self.host_groups[hgk]
                if hg.host_type == "rack" and hg.status == "enabled":
                    avail_nw_bandwidth_list = []
                    for sk in hg.switches.keys():
                        s = hg.switches[sk]
                        if s.status == "enabled":
                            for ulk in s.up_links.keys():
                                ul = s.up_links[ulk]
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                            # NOTE: peer links?
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)

    def update_rack_resource(self, _host):   
        rack = _host.host_group 
        rack.last_update = time.time()                                                         
                                                                                                 
        if isinstance(rack, HostGroup):                                                           
            self.update_cluster_resource(rack)

    def update_cluster_resource(self, _rack):
        cluster = _rack.parent_resource
        cluster.last_update = time.time()
                                                                                                 
        if isinstance(cluster, HostGroup):
            self.datacenter.last_update = time.time()

    def get_flavor(self, _name):
        flavor = None

        if _name in self.flavors.keys():
            flavor = self.flavors[_name]

        return flavor

    def get_logical_groups_for_aggregate(self, _flavor):
        group_names = []

        match = True
        for gk in self.logical_groups.keys():
            group = self.logical_groups[gk]
            if group.group_type == "AGGR":
                for sk in _flavor.extra_specs.keys():
                    if sk not in group.metadata.keys():
                        match = False
                        break
            else:
                match = False

            if match == True:
                group_names.append(gk)

        return group_names


    #def set_vm_capacity(self, _vm):
        #exist = False
                                                              
        #for fk in self.flavors.keys():
            #flavor = self.flavors[fk]                                                                   
            #if _vm.flavor == fk:                                                     
                #_vm.vCPUs = flavor.vCPUs                                                      
                #_vm.mem = flavor.mem_cap                                                     
                #_vm.local_volume_size = flavor.disk_cap
 
                #exist = True  
                #break

        #if exist == False:
            #return False                                                                         
                                                                                                 
        #return True






