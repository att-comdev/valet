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
import json

from resource_base import Datacenter, HostGroup, Host, LogicalGroup, Flavor, Switch, Link, StorageHost

sys.path.insert(0, '../app_manager')
from app_topology_base import LEVELS

sys.path.insert(0, '../util')
from util import get_last_logfile


class Resource:

    def __init__(self, _db, _config, _logger):
        self.db = _db

        self.config = _config
        self.logger = _logger

        # Resource data
        self.datacenter = None
        if self.config.mode.startswith("sim") == True:
            self.datacenter = Datacenter(self.config.mode)
        else:
            self.datacenter = Datacenter(self.config.datacenter_name)
        self.host_groups = {}
        self.hosts = {}
        self.switches = {}
        self.storage_hosts = {}

        # Metadata
        self.logical_groups = {}
        self.flavors = {}

        self.current_timestamp = 0
        self.last_log_index = 0

        # Resource status aggregation
        self.CPU_avail = 0
        self.mem_avail = 0
        self.local_disk_avail = 0
        self.disk_avail = 0
        self.nw_bandwidth_avail = 0

    def bootstrap_from_db(self, _resource_status):
        logical_groups = _resource_status["logical_groups"]
        for lgk, lg in logical_groups.iteritems():
            logical_group = LogicalGroup(lgk)
            logical_group.group_type = lg["group_type"]
            logical_group.status = lg["status"]
            logical_group.metadata = lg["metadata"]
            logical_group.vm_list = lg["vm_list"]
            logical_group.volume_list = lg["volume_list"]
            logical_group.vms_per_host = lg["vms_per_host"]

            self.logical_groups[lgk] = logical_group

        if len(self.logical_groups) > 0:
            self.logger.debug("logical_groups loaded")
        else:
            self.logger.warn("no logical_groups")

        flavors = _resource_status["flavors"]
        for fk, f in flavors.iteritems():
            flavor = Flavor(fk)
            flavor.flavor_id = f["flavor_id"] 
            flavor.status = f["status"] 
            flavor.vCPUs = f["vCPUs"]
            flavor.mem_cap = f["mem"]
            flavor.disk_cap = f["disk"]
            flavor.extra_specs = f["extra_specs"]

            self.flavors[fk] = flavor

        if len(self.flavors) > 0:
            self.logger.debug("flavors loaded")
        else:
            self.logger.error("fail loading flavors")
            return False

        switches = _resource_status["switches"]
        for sk, s in switches.iteritems():
            switch = Switch(sk)
            switch.switch_type = s["switch_type"]
            switch.status = s["status"]

            self.switches[sk] = switch

        if len(self.switches) > 0:
            self.logger.debug("switches loaded")
        else:
            self.logger.error("fail loading switches")
            return False

        for sk, s in switches.iteritems():
            switch = self.switches[sk]

            up_links = {}
            uls = s["up_links"]
            for ulk, ul in uls.iteritems():
                ulink = Link(ulk)
                ulink.resource = self.switches[ul["resource"]]
                ulink.nw_bandwidth = ul["bandwidth"]
                ulink.avail_nw_bandwidth = ul["avail_bandwidth"]

                up_links[ulk] = ulink

            switch.up_links = up_links

            peer_links = {}
            pls = s["peer_links"]
            for plk, pl in pls.iteritems():
                plink = Link(plk)
                plink.resource = self.switches[pl["resource"]]
                plink.nw_bandwidth = pl["bandwidth"]
                plink.avail_nw_bandwidth = pl["avail_bandwidth"]

                peer_links[plk] = plink

            switch.peer_links = peer_links

        self.logger.debug("switch links loaded")

        # TODO: storage_hosts

        hosts = _resource_status["hosts"]
        for hk, h in hosts.iteritems():
            host = Host(hk)
            host.tag = h["tag"]
            host.status = h["status"]
            host.state = h["state"]
            host.vCPUs = h["vCPUs"]
            host.original_vCPUs = h["original_vCPUs"]
            host.avail_vCPUs = h["avail_vCPUs"]
            host.mem_cap = h["mem"]
            host.original_mem_cap = h["original_mem"]
            host.avail_mem_cap = h["avail_mem"]
            host.local_disk_cap = h["local_disk"]
            host.original_local_disk_cap = h["original_local_disk"]
            host.avail_local_disk_cap = h["avail_local_disk"]
            host.vCPUs_used = h["vCPUs_used"]
            host.free_mem_mb = h["free_mem_mb"]
            host.free_disk_gb = h["free_disk_gb"]
            host.disk_available_least = h["disk_available_least"]
            host.vm_list = h["vm_list"]
            host.volume_list = h["volume_list"]

            for lgk in h["membership_list"]:
                host.memberships[lgk] = self.logical_groups[lgk]

            for sk in h["switch_list"]:
                host.switches[sk] = self.switches[sk]

            # TODO: host.storages

            self.hosts[hk] = host
                
        if len(self.hosts) > 0:
            self.logger.debug("hosts loaded")
        else:
            self.logger.error("fail loading hosts")
            return False

        host_groups = _resource_status["host_groups"]
        for hgk, hg in host_groups.iteritems():
            host_group = HostGroup(hgk)
            host_group.host_type = hg["host_type"]
            host_group.status = hg["status"]
            host_group.vCPUs = hg["vCPUs"]
            host_group.original_vCPUs = hg["original_vCPUs"]
            host_group.avail_vCPUs = hg["avail_vCPUs"]
            host_group.mem_cap = hg["mem"]
            host_group.original_mem_cap = hg["original_mem"]
            host_group.avail_mem_cap = hg["avail_mem"]
            host_group.local_disk_cap = hg["local_disk"]
            host_group.original_local_disk_cap = hg["original_local_disk"]
            host_group.avail_local_disk_cap = hg["avail_local_disk"]
            host_group.vm_list = hg["vm_list"]
            host_group.volume_list = hg["volume_list"]

            for lgk in hg["membership_list"]:
                host_group.memberships[lgk] = self.logical_groups[lgk]

            for sk in hg["switch_list"]:
                host_group.switches[sk] = self.switches[sk]

            # TODO: host.storages

            self.host_groups[hgk] = host_group

        if len(self.host_groups) > 0:
            self.logger.debug("host_groups loaded")
        else:
            self.logger.error("fail loading host_groups")
            return False

        dc = _resource_status["datacenter"]
        self.datacenter.name = dc["name"]
        self.datacenter.region_code_list = dc["region_code_list"]
        self.datacenter.status = dc["status"]
        self.datacenter.vCPUs = dc["vCPUs"]
        self.datacenter.original_vCPUs = dc["original_vCPUs"]
        self.datacenter.avail_vCPUs = dc["avail_vCPUs"]
        self.datacenter.mem_cap = dc["mem"]
        self.datacenter.original_mem_cap = dc["original_mem"]
        self.datacenter.avail_mem_cap = dc["avail_mem"]
        self.datacenter.local_disk_cap = dc["local_disk"]
        self.datacenter.original_local_disk_cap = dc["original_local_disk"]
        self.datacenter.avail_local_disk_cap = dc["avail_local_disk"]
        self.datacenter.vm_list = dc["vm_list"]
        self.datacenter.volume_list = dc["volume_list"]

        for lgk in dc["membership_list"]:
            self.datacenter.memberships[lgk] = self.logical_groups[lgk]

        for sk in dc["switch_list"]:
            self.datacenter.root_switches[sk] = self.switches[sk]

        # TODO: host.storages

        for ck in dc["children"]:
            if ck in self.host_groups.keys():
                self.datacenter.resources[ck] = self.host_groups[ck]
            elif ck in self.hosts.keys():
                self.datacenter.resources[ck] = self.hosts[ck]
  
        if len(self.datacenter.resources) > 0:
            self.logger.debug("datacenter loaded")
        else:
            self.logger.error("fail loading datacenter")
            return False

        hgs = _resource_status["host_groups"]
        for hgk, hg in hgs.iteritems():
            host_group = self.host_groups[hgk]

            pk = hg["parent"]
            if pk == self.datacenter.name:
                host_group.parent_resource = self.datacenter
            elif pk in self.host_groups.keys():
                host_group.parent_resource = self.host_groups[pk]

            for ck in hg["children"]:
                if ck in self.hosts.keys():
                    host_group.child_resources[ck] = self.hosts[ck]
                elif ck in self.host_groups.keys():
                    host_group.child_resources[ck] = self.host_groups[ck]
        
        self.logger.debug("host_groups'layout loaded")

        hs = _resource_status["hosts"]
        for hk, h in hs.iteritems():
            host = self.hosts[hk]

            pk = h["parent"]
            if pk == self.datacenter.name:
                host.host_group = self.datacenter
            elif pk in self.host_groups.keys():
                host.host_group = self.host_groups[pk]
           
        self.logger.debug("hosts'layout loaded")

        self._update_compute_avail()
        self._update_storage_avail()
        self._update_nw_bandwidth_avail()
         
        self.logger.debug("resource availability updated")

        return True

    # Run whenever changed
    def update_topology(self):
        self._update_topology()
        #self._update_logical_groups()

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

    def _update_host_group_topology(self, _host_group):
        _host_group.init_resources()
        del _host_group.vm_list[:]
        del _host_group.volume_list[:]
        _host_group.storages.clear()

        for hk, host in _host_group.child_resources.iteritems():
            if host.check_availability() == True:
                _host_group.vCPUs += host.vCPUs
                _host_group.original_vCPUs += host.original_vCPUs
                _host_group.avail_vCPUs += host.avail_vCPUs
                _host_group.mem_cap += host.mem_cap
                _host_group.original_mem_cap += host.original_mem_cap
                _host_group.avail_mem_cap += host.avail_mem_cap
                _host_group.local_disk_cap += host.local_disk_cap
                _host_group.original_local_disk_cap += host.original_local_disk_cap
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
                self.datacenter.original_vCPUs += resource.original_vCPUs
                self.datacenter.avail_vCPUs += resource.avail_vCPUs
                self.datacenter.mem_cap += resource.mem_cap
                self.datacenter.original_mem_cap += resource.original_mem_cap
                self.datacenter.avail_mem_cap += resource.avail_mem_cap
                self.datacenter.local_disk_cap += resource.local_disk_cap
                self.datacenter.original_local_disk_cap += resource.original_local_disk_cap
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

    def _update_logical_groups(self):
        for lgk in self.logical_groups.keys():
            lg = self.logical_groups[lgk]

            for hk in lg.vms_per_host.keys():
                '''
                if hk in self.hosts.keys():
                    host = self.hosts[hk]
                    if host.check_availability() == False:
                        for vm_id in host.vm_list:
                            if lg.exist_vm(vm_id) == True:
                                lg.vm_list.remove(vm_id)
                        del lg.vms_per_host[hk]
                        lg.last_update = time.time()
                elif hk in self.host_groups.keys(): 
                    host_group = self.host_groups[hk]
                    if host_group.check_availability() == False:
                        for vm_id in host_group.vm_list:
                            if lg.exist_vm(vm_id) == True:
                                lg.vm_list.remove(vm_id)
                        del lg.vms_per_host[hk]
                        lg.last_update = time.time()
                '''
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if len(lg.vms_per_host[hk]) == 0:
                        del lg.vms_per_host[hk]
                        lg.last_update = time.time()

            '''
            if len(lg.vms_per_host) == 0 and len(lg.vm_list) == 0 and len(lg.volume_list) == 0:
                self.logical_groups[lgk].status = "disabled"

                self.logical_groups[lgk].last_update = time.time()
                self.logger.warn("logical group (" + lgk + ") removed")
            '''

        for hk, h in self.hosts.iteritems():
            for lgk in h.memberships.keys():
                if lgk not in self.logical_groups.keys():
                    del h.memberships[lgk]

        for hgk, hg in self.host_groups.iteritems():
            for lgk in hg.memberships.keys():
                if lgk not in self.logical_groups.keys():
                    del hg.memberships[lgk]

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

    def _store_topology_updates(self):
        last_update_time = self.current_timestamp

        flavor_updates = {}
        logical_group_updates = {}
        storage_updates = {}
        switch_updates = {}
        host_updates = {}
        host_group_updates = {}
        datacenter_update = None

        for fk, flavor in self.flavors.iteritems():
            if flavor.last_update > self.current_timestamp:
                flavor_updates[fk] = flavor.get_json_info()    

                last_update_time = flavor.last_update

        for lgk, lg in self.logical_groups.iteritems():
            if lg.last_update > self.current_timestamp:
                logical_group_updates[lgk] = lg.get_json_info()   

                last_update_time = lg.last_update

        for shk, storage_host in self.storage_hosts.iteritems():
            if storage_host.last_update > self.current_timestamp or \
               storage_host.last_cap_update > self.current_timestamp:
                storage_updates[shk] = storage_host.get_json_info()

                if storage_host.last_update > self.current_time_stamp:
                    last_update_time = storage_host.last_update
                if storage_host.last_cap_update > self.current_timestamp:
                    last_update_time = storage_host.last_cap_update

        for sk, s in self.switches.iteritems():
            if s.last_update > self.current_timestamp:
                switch_updates[sk] = s.get_json_info()

                last_update_time = s.last_update

        for hk, host in self.hosts.iteritems():
            if host.last_update > self.current_timestamp or host.last_link_update > self.current_timestamp:
                host_updates[hk] = host.get_json_info()

                if host.last_update > self.current_timestamp:
                    last_update_time = host.last_update
                if host.last_link_update > self.current_timestamp:
                    last_update_time = host.last_link_update

        for hgk, host_group in self.host_groups.iteritems():
            if host_group.last_update > self.current_timestamp or \
               host_group.last_link_update > self.current_timestamp:
                host_group_updates[hgk] = host_group.get_json_info()

                if host_group.last_update > self.current_timestamp:
                    last_update_time = host_group.last_update
                if host_group.last_link_update > self.current_timestamp:
                    last_update_time = host_group.last_link_update

        if self.datacenter.last_update > self.current_timestamp or \
           self.datacenter.last_link_update > self.current_timestamp:
            datacenter_update = self.datacenter.get_json_info()

            if self.datacenter.last_update > self.current_timestamp:
                last_update_time = self.datacenter.last_update
            if self.datacenter.last_link_update > self.current_timestamp:
                last_update_time = self.datacenter.last_link_update

        (resource_logfile, last_index, mode) = get_last_logfile(self.config.resource_log_loc, \
                                                                self.config.max_log_size, \
                                                                self.config.max_num_of_logs, \
                                                                self.datacenter.name, \
                                                                self.last_log_index)
        self.last_log_index = last_index

        logging = open(self.config.resource_log_loc + resource_logfile, mode)
  
        json_logging = {}
        json_logging['timestamp'] = last_update_time

        if len(flavor_updates) > 0:
            json_logging['flavors'] = flavor_updates
        if len(logical_group_updates) > 0:
            json_logging['logical_groups'] = logical_group_updates
        if len(storage_updates) > 0:
            json_logging['storages'] = storage_updates
        if len(switch_updates) > 0:
            json_logging['switches'] = switch_updates
        if len(host_updates) > 0:
            json_logging['hosts'] = host_updates
        if len(host_group_updates) > 0:
            json_logging['host_groups'] = host_group_updates
        if datacenter_update != None:
            json_logging['datacenter'] = datacenter_update

        logged_data = json.dumps(json_logging)

        logging.write(logged_data)
        logging.write("\n")

        logging.close()

        self.logger.info("log: resource status timestamp in " + resource_logfile)

        if self.db != None:
            self.db.update_resource_status(self.datacenter.name, json_logging)
            self.db.update_resource_log_index(self.datacenter.name, self.last_log_index)

        return last_update_time

    def update_rack_resource(self, _host):   
        rack = _host.host_group 
       
        if rack != None:
            rack.last_update = time.time()                                                         
                                                                                                 
            if isinstance(rack, HostGroup):                                                           
                self.update_cluster_resource(rack)

    def update_cluster_resource(self, _rack):
        cluster = _rack.parent_resource

        if cluster != None:
            cluster.last_update = time.time()
                                                                                                 
            if isinstance(cluster, HostGroup):
                self.datacenter.last_update = time.time()

    def add_vm_to_logical_groups(self, _host, _vm_id, _logical_groups_of_vm):
        for lgk in _host.memberships.keys():
            if lgk in _logical_groups_of_vm:            
                lg = self.logical_groups[lgk]

                if isinstance(_host, Host):
                    if lg.add_vm(_vm_id, _host.name) == True:
                        lg.last_update = time.time()
                elif isinstance(_host, HostGroup):
                    if lg.group_type == "EX" or lg.group_type == "AFF":
                        if lgk.split(":")[0] == _host.host_type:
                            if lg.add_vm(_vm_id, _host.name) == True:
                                lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group != None:
            self.add_vm_to_logical_groups(_host.host_group, _vm_id, _logical_groups_of_vm)
        elif isinstance(_host, HostGroup) and _host.parent_resource != None:
            self.add_vm_to_logical_groups(_host.parent_resource, _vm_id, _logical_groups_of_vm)

    def remove_vm_from_logical_groups(self, _host, _vm_id):
        for lgk in _host.memberships.keys():
            lg = self.logical_groups[lgk]

            if isinstance(_host, Host):
                if lg.remove_vm(_vm_id, _host.name) == True:
                    lg.last_update = time.time()
            elif isinstance(_host, HostGroup):
                if lg.group_type == "EX" or lg.group_type == "AFF":
                    if lgk.split(":")[0] == _host.host_type:
                        if lg.remove_vm(_vm_id, _host.name) == True:
                            lg.last_update = time.time()

        if isinstance(_host, Host) and _host.host_group != None:
            self.remove_vm_from_logical_groups(_host.host_group, _vm_id)
        elif isinstance(_host, HostGroup) and _host.parent_resource != None:
            self.remove_vm_from_logical_groups(_host.parent_resource, _vm_id)

    def get_flavor(self, _name):
        flavor = None

        if _name in self.flavors.keys():
            if self.flavors[_name].status == "enabled":
                flavor = self.flavors[_name]

        return flavor





