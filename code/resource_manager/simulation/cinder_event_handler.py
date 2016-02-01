#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Dec. 7, 2015
#
# Functions 
# - Manage cinder storage events to update storage resources
# 
# TODO:
# - Include Cinder AZ
# - Integrate Ceph beackend
# - Capture where backends and pools are hosted (which host or rack?)
#################################################################################################################


import time
from copy import deepcopy
import threading

from resource_base import StorageHost


class TestStorage(threading.Thread):
  
    def __init__(self, _thread_id, _thread_name, _resource, _data_lock, _logger):
        threading.Thread.__init__(self)

        self.thread_id = _thread_id
        self.thread_name = _thread_name
        self.resource = _resource
        self.data_lock = _data_lock

        self.logger = _logger

        self.end_of_process = False

    def run(self):
        self.logger.info("start " + self.thread_name + " ......")

        test_fire = 2
        test_end = time.time() + test_fire
        while self.end_of_process == False:
            time.sleep(1)

            if time.time() > test_end:
                self.data_lock.acquire(1)
                if self.set_storages() == True:
                    self.logger.debug("storage updated")
                    self.resource.update_topology()
                self.data_lock.release()

                test_end = time.time() + test_fire

        self.logger.info("exit " + self.thread_name)

    def set_storages(self):
        storage_hosts = {}

        for h_num in range(0, 16):
            storage_host = StorageHost("sh-1-" + str(h_num))
            storage_host.status = "enabled"
            storage_host.storage_class = "1"

            host_name = "cirrus2"
            if h_num < 9:
                host_name += ("0" + str(h_num+1))
            else:
                host_name += str(h_num+1)
            storage_host.host_list.append(host_name)

            storage_host.disk_cap = 700 
            storage_host.avail_disk_cap = 700
 
            storage_hosts[storage_host.name] = storage_host

        self._check_update(storage_hosts)

        return True

    def _check_update(self, _storage_hosts):
        for shk in _storage_hosts.keys():                                                                 
            if shk not in self.resource.storage_hosts.keys():                                             
                new_storage_host = deepcopy(_storage_hosts[shk])                                                  
                self.resource.storage_hosts[new_storage_host.name] = new_storage_host
 
                new_storage_host.last_update = time.time()                                               
                #self.resource.last_update = new_storage_host.last_update 

                self.logger.warn("new storage (" + new_storage_host.name + ") added")
        
        # Note: This may issue a problem
        for rshk in self.resource.storage_hosts.keys():                                                   
            if rshk not in _storage_hosts.keys():                                                         
                storage_host = self.resource.storage_hosts[rshk]  
                storage_host.status = "disabled" 
                                               
                storage_host.last_update = time.time()                                                   
                #self.resource.last_update = storage_host.last_update

                self.logger.warn("storage (" + storage_host.name + ") disabled")
                                                                                                 
        for shk in _storage_hosts.keys():                                                                 
            storage_host = _storage_hosts[shk]                                                                    
            rstorage_host = self.resource.storage_hosts[shk]
                                                      
            (topology_updated, capacity_updated) = self._check_storage_host_update(storage_host, rstorage_host)
            if topology_updated == True:
                rstorage_host.last_update = time.time()
                #self.resource.last_update = rstorage_host.last_update
            if capacity_updated == True:                                                  
                rstorage_host.last_cap_update = time.time()
                #self.resource.last_update = rstorage_host.last_cap_update

        # Recursively update
        for shk in self.resource.storage_hosts.keys():
            storage_host = self.resource.storage_hosts[shk]
            if storage_host.last_update > self.resource.current_timestamp:
                self._update_host_resource(storage_host)
  
    def _check_storage_host_update(self, _storage_host, _rstorage_host):
        updated = False
        capacity_updated = False

        if _rstorage_host.status == "disabled":
            _rstorage_host.status == "enabled"
            updated = True
            self.logger.warn("storage (" + _rstorage_host.name + ") enabled")

        if _storage_host.storage_class != _rstorage_host.storage_class:
            _rstorage_host.storage_class = _storage_host.storage_class
            updated = True
            self.logger.warn("storage (" + _rstorage_host.name + ") updated (storage class)")

        for host_name in _storage_host.host_list:
            exist = False
            for rhost_name in _rstorage_host.host_list:
                if host_name == rhost_name:
                    exist = True
                    break
            if exist == False:
                _rstorage_host.host_list.append(host_name)
                updated = True
                self.logger.warn("storage (" + _rstorage_host.name + ") updated (new host)")

        for rhost_name in _rstorage_host.host_list:
            exist = False
            for host_name in _storage_host.host_list:
                if rhost_name == host_name:
                    exist = True
                    break
            if exist == False:
                _rstorage_host.host_list.remove(rhost_name)
                updated = True
                self.logger.warn("storage (" + _rstorage_host.name + ") updated (removed from host)")

        if _storage_host.disk_cap != _rstorage_host.disk_cap or \
           _storage_host.avail_disk_cap != _rstorage_host.avail_disk_cap:
            _rstorage_host.disk_cap = _storage_host.disk_cap
            _rstorage_host.avail_disk_cap = _storage_host.avail_disk_cap
            capacity_updated = True
            self.logger.warn("storage (" + _rstorage_host.name + ") updated (capacity)")

        return (updated, capacity_updated)

    def _update_host_resource(self, _storage_host):
        for host_name in _storage_host.host_list:
            host = self.resource.hosts[host_name]
            if _storage_host.name not in host.storages.keys():
                if _storage_host.status == "enabled":
                    host.storages[_storage_host.name] = _storage_host
                    host.last_update = time.time()
                    self.resource.update_switch_resource(host)
            else:
                if _storage_host.status == "disabled":
                    del host.storages[_storage_host.name]
                    host.last_update = time.time()
                    self.resource.update_switch_resource(host)

        


