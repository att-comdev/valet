#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Update Host status, local resources, and metadata 
# - Update Flavor list
#
#################################################################################################################


import time
from copy import deepcopy
import threading

from resource_base import Host
from authentication import Authentication

from compute import Compute
from simulation.compute_simulator import SimCompute


class ComputeManager(threading.Thread):
  
    def __init__(self, _t_id, _t_name, _rsc, _data_lock, _config, _logger):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _rsc

        self.config = _config

        self.logger = _logger

        self.auth = Authentication()
        self.admin_token = None
        self.project_token = None

    def run(self):
        self.logger.info("start " + self.thread_name + " ......")

        if self.config.compute_trigger_freq > 0:
            period_end = time.time() + self.config.compute_trigger_freq

            while self.end_of_process == False:
                time.sleep(1)

                if time.time() > period_end:
                    self._run()
                    period_end = time.time() + self.config.compute_trigger_freq

        else:
            (alarm_HH, alarm_MM) = self.config.compute_trigger_time.split(':')
            last_trigger_year = 0
            last_trigger_mon = 0
            last_trigger_mday = 0
            timeout = False

            while self.end_of_process == False:
                time.sleep(1)

                now = time.localtime()
                if timeout == False and \
                   now.tm_hour >= int(alarm_HH) and now.tm_min >= int(alarm_MM):
                    self._run()

                    timeout = True
                    last_trigger_year = now.tm_year
                    last_trigger_mon = now.tm_mon
                    last_trigger_mday = now.tm_mday

                if now.tm_year > last_trigger_year:
                    timeout = False
                else:
                    if now.tm_mon > last_trigger_mon:
                        timeout = False
                    else:
                        if now.tm_mday > last_trigger_mday:
                            timeout = False

        self.logger.info("exit " + self.thread_name)

    def _run(self):
        self.data_lock.acquire(1)

        triggered_host_updates = self.set_hosts()
        triggered_flavor_updates = self.set_flavors()

        if triggered_host_updates == True or triggered_flavor_updates == True:
            self.logger.info("trigger setting hosts")

            self.resource.update_topology()

        self.data_lock.release()

    def _set_admin_token(self):                                                                  
        self.admin_token = self.auth.get_tenant_token(self.config)
        if self.admin_token == None:                                                             
            self.logger.error(self.auth.status)                                                  
            return False                                                                         
                                                                                                 
        return True                                                                              
                                                                                                 
    def _set_project_token(self):                                                                
        self.project_token = self.auth.get_project_token(self.config, self.admin_token)
        if self.project_token == None:                                                           
            self.logger.error(self.auth.status)                                                  
            return False                                                                         
                                                                                                 
        return True    

    def set_hosts(self):
        hosts = {}
        logical_groups = {}

        compute = None
        if self.config.mode.startswith("sim") == True:
            compute = SimCompute(self.config)
        else:
            if self._set_admin_token() == False or self._set_project_token() == False:               
                return False

            compute = Compute(self.config, self.admin_token, self.project_token)

        status = compute.set_hosts(hosts, logical_groups)
        if status != "success":
            self.logger.error(status)
            return False

        self._check_logical_group_update(logical_groups)
        self._check_host_update(hosts)

        return True

    def _check_logical_group_update(self, _logical_groups):
        for lk in _logical_groups.keys():
            if lk not in self.resource.logical_groups.keys():
                self.resource.logical_groups[lk] = deepcopy(_logical_groups[lk])

                self.resource.logical_groups[lk].last_update = time.time()
                self.logger.warn("new logical group (" + lk + ") added")

        for rlk in self.resource.logical_groups.keys():
            rl = self.resource.logical_groups[rlk]
            if rl.group_type != "EX" and rl.group_type != "AFF":
                if rlk not in _logical_groups.keys():
                    self.resource.logical_groups[rlk].status = "disabled"

                    self.resource.logical_groups[rlk].last_update = time.time()
                    self.logger.warn("logical group (" + rlk + ") removed")

        for lk in _logical_groups.keys():
            lg = _logical_groups[lk]
            rlg = self.resource.logical_groups[lk]
            if lg.group_type != "EX" and lg.group_type != "AFF":
                if self._check_logical_group_metadata_update(lg, rlg) == True:

                    rlg.last_update = time.time()
                    self.logger.warn("logical group (" + lk + ") updated")
         
    def _check_logical_group_metadata_update(self, _lg, _rlg):
        metadata_updated = False

        for mdk in _lg.metadata.keys():
            if mdk not in _rlg.metadata.keys():
                _rlg.metadata[mdk] = _lg.metadata[mdk]
                metadata_updated = True

        for rmdk in _rlg.metadata.keys():
            if rmdk not in _lg.metadata.keys():
                del _rlg.metadata[rmdk]
                metadata_updated = True

        for vm_id in _lg.vm_list:
            if _rlg.exist_vm(vm_id) == False:
                _rlg.vm_list.append(vm_id)

        for rvm_id in _rlg.vm_list:
            if _lg.exist_vm(rvm_id) == False:
                _rlg.vm_list.remove(rvm_id)

        for hk in _lg.vms_per_host.keys():
            if hk not in _rlg.vms_per_host.keys():
                _rlg.vms_per_host[hk] = deepcopy(_lg.vms_per_host[hk])

        for rhk in _rlg.vms_per_host.keys():
            if rhk not in _lg.vms_per_host.keys():
                del _rlg.vms_per_host[rhk]

    def _check_host_update(self, _hosts):
        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = Host(hk)
                self.resource.hosts[new_host.name] = new_host

                new_host.last_update = time.time()
                self.logger.warn("new host (" + new_host.name + ") added")

        for rhk, rhost in self.resource.hosts.iteritems():
            if rhk not in _hosts.keys():
                if "nova" in rhost.tag:
                    rhost.tag.remove("nova")

                    rhost.last_update = time.time()
                    self.logger.warn("host (" + rhost.name + ") disabled")

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            if self._check_host_config_update(host, rhost) == True:
                rhost.last_update = time.time()

        for hk, h in self.resource.hosts.iteritems():
            if h.clean_memberships() == True:
                h.last_update = time.time()
                self.logger.warn("host (" + h.name + ") updated (delete EX/AFF membership)")

        for hk, host in self.resource.hosts.iteritems():                                                    
            if host.last_update > self.resource.current_timestamp:                               
                self.resource.update_rack_resource(host)

    def _check_host_config_update(self, _host, _rhost):
        topology_updated = False

        if "nova" not in _rhost.tag:
            _rhost.tag.append("nova")
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (tag added)")

        if _host.status != _rhost.status:
            _rhost.status = _host.status
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (status changed)")

        if _host.state != _rhost.state:
            _rhost.state = _host.state
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (state changed)")

        if _host.vCPUs != _rhost.vCPUs or _host.avail_vCPUs != _rhost.avail_vCPUs:
            _rhost.vCPUs = _host.vCPUs
            _rhost.avail_vCPUs = _host.avail_vCPUs
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (CPU updated)")

        if _host.mem_cap != _rhost.mem_cap or _host.avail_mem_cap != _rhost.avail_mem_cap:
            _rhost.mem_cap = _host.mem_cap
            _rhost.avail_mem_cap = _host.avail_mem_cap
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (mem updated)")

        if _host.local_disk_cap != _rhost.local_disk_cap or \
           _host.avail_local_disk_cap != _rhost.avail_local_disk_cap:
            _rhost.local_disk_cap = _host.local_disk_cap
            _rhost.avail_local_disk_cap = _host.avail_local_disk_cap
            topology_updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (local disk space updated)")

        for mk in _host.memberships.keys():
            if mk not in _rhost.memberships.keys():
                _rhost.memberships[mk] = self.resource.logical_groups[mk]
                topology_updated = True
                self.logger.warn("host (" + _rhost.name + ") updated (new membership)")

        for mk in _rhost.memberships.keys():
            m = _rhost.memberships[mk]
            if m.group_type != "EX" and m.group_type != "AFF":
                if mk not in _host.memberships.keys():
                    del _rhost.memberships[mk]
                    topology_updated = True
                    self.logger.warn("host (" + _rhost.name + ") updated (delete membership)")

        for vm_id in _host.vm_list:
            if _rhost.exist_vm(vm_id) == False:
                _rhost.vm_list.append(vm_id)

                # NOTE: do we need this?
                #self.resource.add_vm_to_logical_groups(_rhost, vm_id)

                topology_updated = True
                self.logger.warn("host (" + _rhost.name +") updated (new vm placed)")

        for rvm_id in _rhost.vm_list:
            if rvm_id[2] == "none" or _host.exist_vm(rvm_id) == False:
                _rhost.vm_list.remove(rvm_id)

                self.resource.remove_vm_from_logical_groups(_rhost, rvm_id)

                topology_updated = True
                self.logger.warn("host (" + _rhost.name +") updated (vm removed)")

        return topology_updated

    def set_flavors(self):
        flavors = {}

        compute = None
        if self.config.mode.startswith("sim") == True:
            compute = SimCompute(self.config)
        else:
            if self._set_admin_token() == False or self._set_project_token() == False:
                return False
 
            compute = Compute(self.config, self.admin_token, self.project_token)

        status = compute.set_flavors(flavors)
        if status != "success":
            self.logger.error(status)
            return False
             
        self._check_flavor_update(flavors)

        return True

    def _check_flavor_update(self, _flavors):
        for fk in _flavors.keys():
            if fk not in self.resource.flavors.keys():
                self.resource.flavors[fk] = deepcopy(_flavors[fk])

                self.resource.flavors[fk].last_update = time.time()
                self.logger.warn("new flavor (" + fk + ") added")

        for rfk in self.resource.flavors.keys():
            if rfk not in _flavors.keys():
                self.resource.flavors[rfk].status = "disabled"

                self.resource.flavors[rfk].last_update = time.time()
                self.logger.warn("flavor (" + rfk + ") removed")

        for fk in _flavors.keys():
            f = _flavors[fk]
            rf = self.resource.flavors[fk]

            if self._check_flavor_spec_update(f, rf) == True:
                rf.last_update = time.time()
                self.logger.warn("flavor (" + fk + ") spec updated")

    def _check_flavor_spec_update(self, _f, _rf):
        spec_updated = False

        if _f.vCPUs != _rf.vCPUs or _f.mem_cap != _rf.mem_cap or _f.disk_cap != _rf.disk_cap:
            _rf.vCPUs = _f.vCPUs
            _rf.mem_cap = _f.mem_cap
            _rf.disk_cap = _f.disk_cap
            spec_updated = True

        for sk in _f.extra_specs.keys():
            if sk not in _rf.extra_specs.keys():
                _rf.extra_specs[sk] = _f.extra_specs[sk]
                spec_updated = True
     
        for rsk in _rf.extra_specs.keys():
            if rsk not in _f.extra_specs.keys():
                del _rf.extra_specs[rsk]
                spec_updated = True

        return spec_updated


