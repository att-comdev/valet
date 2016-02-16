#!/bin/python


################################################################################################################ 
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
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

    # Run whenever something changed
    def update_topology(self):
        self._update_topology()

        self._update_logical_groups()

        self._update_compute_avail()
        self._update_storage_avail()
        self._update_nw_bandwidth_avail()

        self.current_timestamp = self._store_topology_updates()

    def _update_topology(self):
        for level in LEVELS:
            for hgk, host_group in self.host_groups.iteritems():
                if host_group.host_type == level and host_group.check_availability() == True:
                    if host_group.last_update > self.current_timestamp:
                        self._update_host_group_topology(host_group)

        if self.datacenter.last_update > self.current_timestamp:
            self._update_datacenter_topology()

    def _update_logical_groups(self):
        for lgk in self.logical_groups.keys():
            lg = self.logical_groups[lgk]

            for hk in lg.vms_per_host.keys():
                if hk in self.hosts.keys():
                    host = self.hosts[hk]
                    if host.check_availability() == False:
                        for vm_id in host.vm_list:
                            if lg.exist_vm(vm_id) == True:
                                lg.vm_list.remove(vm_id)
                        del lg.vms_per_host[hk]
                elif hk in self.host_groups.keys(): 
                    host_group = self.host_groups[hk]
                    if host_group.check_availability() == False:
                        for vm_id in host_group.vm_list:
                            if lg.exist_vm(vm_id) == True:
                                lg.vm_list.remove(vm_id)
                        del lg.vms_per_host[hk]

                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if len(lg.vms_per_host[hk]) == 0:
                        del lg.vms_per_host[hk]

            if len(lg.vms_per_host) == 0 and len(lg.vm_list) == 0 and len(lg.volume_list) == 0:
                del self.logical_groups[lgk]

                self.logger.warn("logical group (" + lgk + ") removed")

        for hk, h in self.hosts.iteritems():
            for lgk in h.memberships.keys():
                if lgk not in self.logical_groups.keys():
                    del h.memberships[lgk]
        for hgk, hg in self.host_groups.iteritems():
            for lgk in hg.memberships.keys():
                if lgk not in self.logical_groups.keys():
                    del hg.memberships[lgk]

    def _update_host_group_topology(self, _host_group):
        _host_group.init_resources()
        del _host_group.vm_list[:]
        del _host_group.volume_list[:]
        _host_group.storages.clear()

        for hk, host in _host_group.child_resources.iteritems():
            if host.check_availability() == True:
                _host_group.vCPUs += host.vCPUs
                _host_group.avail_vCPUs += host.avail_vCPUs
                _host_group.mem_cap += host.mem_cap
                _host_group.avail_mem_cap += host.avail_mem_cap
                _host_group.local_disk_cap += host.local_disk_cap
                _host_group.avail_local_disk_cap += host.avail_local_disk_cap

                for shk, storage_host in host.storages.iteritems():
                    if storage_host.status == "enabled":
                        _host_group.storages[shk] = storage_host

                for vm_id in host.vm_list:
                    _host_group.vm_list.append(vm_id)

                for vol_name in host.volume_list:
                    _host_group.volume_list.append(vol_name)

        _host_group.init_memberships()

        for hk, host in _host_group.child_resources.iteritems():
            if host.check_availability() == True:
                for mk in host.memberships.keys():
                    _host_group.memberships[mk] = host.memberships[mk]

    def _update_datacenter_topology(self):
        self.datacenter.init_resources()
        del self.datacenter.vm_list[:]
        del self.datacenter.volume_list[:]
        self.datacenter.storages.clear()
        self.datacenter.memberships.clear()

        for rk, resource in self.datacenter.resources.iteritems():
            if resource.check_availability() == True:
                self.datacenter.vCPUs += resource.vCPUs
                self.datacenter.avail_vCPUs += resource.avail_vCPUs
                self.datacenter.mem_cap += resource.mem_cap
                self.datacenter.avail_mem_cap += resource.avail_mem_cap
                self.datacenter.local_disk_cap += resource.local_disk_cap
                self.datacenter.avail_local_disk_cap += resource.avail_local_disk_cap

                for shk, storage_host in resource.storages.iteritems():
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

        for shk, storage_host in self.storage_hosts.iteritems():
            if storage_host.status == "enabled":
                self.disk_avail += storage_host.avail_disk_cap

    # Measure from the highest level
    def _update_nw_bandwidth_avail(self):
        self.nw_bandwidth_avail = 0

        level = "leaf"
        for sk, s in self.switches.iteritems():
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
            for hk, h in self.hosts.iteritems():
                if h.status == "enabled" and h.state == "up" and \
                   ("nova" in h.tag) and ("infra" in h.tag):
                    avail_nw_bandwidth_list = []
                    for sk, s in h.switches.iteritems():
                        if s.status == "enabled":
                            for ulk, ul in s.up_links.iteritems():
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)
        elif level == "spine":
            for hgk, hg in self.host_groups.iteritems():
                if hg.host_type == "rack" and hg.status == "enabled":
                    avail_nw_bandwidth_list = []
                    for sk, s in hg.switches.iteritems():
                        if s.status == "enabled":
                            for ulk, ul in s.up_links.iteritems():
                                avail_nw_bandwidth_list.append(ul.avail_nw_bandwidth)
                            # NOTE: peer links?
                    self.nw_bandwidth_avail += min(avail_nw_bandwidth_list)

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

        #return last_ts

    def _store_topology_updates(self):
        last_ts = self.current_timestamp

        for lgk, lg in self.logical_groups.iteritems():
            self.logger.debug("*** logical group name = " + lgk)
            self.logger.debug("group_type = " + lg.group_type)
            
            for mdk, md in lg.metadata.iteritems():
                self.logger.debug("metadata = " + mdk + ", value = " + lg.metadata[mdk])

            for vm_id in lg.vm_list:
                self.logger.debug("vm = " + vm_id[0] + ", " + vm_id[1] + ", " + vm_id[2])

            for hk, vm_list in lg.vms_per_host.iteritems():
                self.logger.debug("host = " + hk)
                for vm_id in vm_list:
                    self.logger.debug("    vm = " + vm_id[0] + ", " + vm_id[1] + ", " + vm_id[2])

        for shk, storage_host in self.storage_hosts.iteritems():
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

        for sk, s in self.switches.iteritems():
            if s.last_update > self.current_timestamp:
                self.logger.debug("*** switch name = " + s.name)
                self.logger.debug("switch update time = " + str(s.last_update))

                self.logger.debug("type = " + s.switch_type)
                self.logger.debug("status = " + s.status)
                for ulk, ul in s.up_links.iteritems():
                    self.logger.debug("up link = " + ul.name + " bandwidth = " + str(ul.avail_nw_bandwidth))
                for plk, pl in s.peer_links.iteritems():
                    self.logger.debug("peer link = " + pl.name + " bandwidth = " + str(pl.avail_nw_bandwidth))

                if s.last_update > last_ts:
                    last_ts = s.last_update

        for hk, host in self.hosts.iteritems():
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

                for mk, m in host.memberships.iteritems():
                    self.logger.debug("host logical group = " + m.name)

                self.logger.debug("host avail vCPUs = " + str(host.avail_vCPUs))
                self.logger.debug("host avail mem = " + str(host.avail_mem_cap))
                self.logger.debug("host avail local disk = " + str(host.avail_local_disk_cap))

                for sk, s in host.switches.iteritems():
                    self.logger.debug("host switch = " + s.name)

                for shk, storage_host in host.storages.iteritems(): 
                    self.logger.debug("storage = " + storage_host.name)

                self.logger.debug("group = " + host.host_group.name)

                for vm_id in host.vm_list:
                    self.logger.debug("hosted vm = " + vm_id[0] + ", " + vm_id[1] + ", " + vm_id[2])

                for vol_name in host.volume_list:
                    self.logger.debug("hosted volume = " + vol_name)

                if host.last_update > last_ts:
                    last_ts = host.last_update
                if host.last_link_update > last_ts:
                    last_ts = host.last_link_update

        for hgk, host_group in self.host_groups.iteritems():
            if host_group.last_update > self.current_timestamp or \
               host_group.last_link_update > self.current_timestamp:
                self.logger.debug("*** host_group name = " + host_group.name)
                self.logger.debug("topology update time = " + str(host_group.last_update))
                self.logger.debug("link update time = " + str(host_group.last_link_update))

                self.logger.debug("type = " + host_group.host_type)

                self.logger.debug("status = " + host_group.status)

                for mk, m in host_group.memberships.iteritems():
                    self.logger.debug("host_group logical group = " + m.name)

                self.logger.debug("avail vCPUs = " + str(host_group.avail_vCPUs))
                self.logger.debug("avail mem = " + str(host_group.avail_mem_cap))
                self.logger.debug("avail local disk = " + str(host_group.avail_local_disk_cap))

                for sk, s in host_group.switches.iteritems():
                    self.logger.debug("switch = " + s.name)

                for shk, storage_host in host_group.storages.iteritems(): 
                    self.logger.debug("storage = " + storage_host.name)

                self.logger.debug("parent resource = " + host_group.parent_resource.name)
                  
                for drk, dr in host_group.child_resources.iteritems():
                    self.logger.debug("child resource = " + dr.name)
                  
                for vm_id in host_group.vm_list:
                    self.logger.debug("hosted vm = " + vm_id[0] + ", " + vm_id[1] + ", " + vm_id[2])

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

            for mk, m in self.datacenter.memberships.iteritems():
                self.logger.debug("datacenter logical group = " + m.name)

            self.logger.debug("datacenter avail vCPUs = " + str(self.datacenter.avail_vCPUs))
            self.logger.debug("datacenter avail mem = " + str(self.datacenter.avail_mem_cap))
            self.logger.debug("datacenter avail local disk = " + str(self.datacenter.avail_local_disk_cap))

            for sk, s in self.datacenter.root_switches.iteritems():
                self.logger.debug("switch = " + s.name)

            for shk, storage_host in self.datacenter.storages.iteritems(): 
                self.logger.debug("storage = " + storage_host.name)

            for rk, r in self.datacenter.resources.iteritems():
                self.logger.debug("child resource = " + r.name)
                  
            for vm_id in self.datacenter.vm_list:
                self.logger.debug("hosted vm = " + vm_id[0] + ", " + vm_id[1] + ", " + vm_id[2])

            for vol_name in self.datacenter.volume_list:
                self.logger.debug("hosted volume = " + vol_name)

            if self.datacenter.last_update > last_ts:
                last_ts = self.datacenter.last_update
            if self.datacenter.last_link_update > last_ts:
                last_ts = self.datacenter.last_link_update

        return last_ts

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

    def add_vm_to_logical_groups(self, _host, _vm_id):
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                lg.add_vm(_vm_id, _host.name)
            else:
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if lgk.split(":")[0] == _host.host_type:
                        lg.add_vm(_vm_id, _host.name)

        if isinstance(_host, Host) and _host.host_group != None:
            self.add_vm_to_logical_groups(_host.host_group, _vm_id)
        elif isinstance(_host, HostGroup) and _host.parent_resource != None:
            self.add_vm_to_logical_groups(_host.parent_resource, _vm_id)

    def remove_vm_from_logical_groups(self, _host, _vm_id):
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                lg.remove_vm(_vm_id, _host.name)
            else:
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if lgk.split(":")[0] == _host.host_type:
                        lg.remove_vm(_vm_id, _host.name)

        if isinstance(_host, Host) and _host.host_group != None:
            self.remove_vm_from_logical_groups(_host.host_group, _vm_id)
        elif isinstance(_host, HostGroup) and _host.parent_resource != None:
            self.remove_vm_from_logical_groups(_host.parent_resource, _vm_id)

    def get_flavor(self, _name):
        flavor = None

        if _name in self.flavors.keys():
            flavor = self.flavors[_name]

        return flavor

    def get_matched_logical_groups(self, _flavor):
        logical_group_list = []

        for gk, group in self.logical_groups.iteritems():
            if self._match_extra_specs(_flavor.extra_specs, group.metadata) == True:
                logical_group_list.append(group)
    
        return logical_group_list

    def _match_extra_specs(self, _specs, _metadata):
        match = True

        for sk in _specs.keys():
            if sk not in _metadata.keys():
                match = False
                break

        return match





