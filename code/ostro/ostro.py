#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Deal with placement requests
# - Run all resource managers (Topology, Compute, Stroage, Network)
#
#################################################################################################################


import threading
import sys
import time
import json

from optimizer import Optimizer

sys.path.insert(0, '../resource_manager')
from resource import Resource
from topology_manager import TopologyManager
from compute_manager import ComputeManager

sys.path.insert(0, '../app_manager')
from app_handler import AppHandler
from app_topology_base import VM, Volume

sys.path.insert(0, '../db_connect')
from music_handler import MusicHandler

class Ostro:

    def __init__(self, _config, _logger):
        self.config = _config

        self.logger = _logger

        self.db = None
        if self.config.db_keyspace != "none":
            self.db = MusicHandler(self.config, self.logger)
            if self.db.init_db() == False:
                self.logger.error("error while initializing MUSIC database")
            else:
                self.logger.debug("done init music")

        self.resource = Resource(self.db, self.config, self.logger)

        self.app_handler = AppHandler(self.resource, self.db, self.config, self.logger)

        self.optimizer = Optimizer(self.resource, self.logger)

        self.data_lock = threading.Lock()
        self.thread_list = []

        self.topology = TopologyManager(1, "Topology", self.resource, self.data_lock, self.config, self.logger)
        self.compute = ComputeManager(2, "Compute", self.resource, self.data_lock, self.config, self.logger)

        self.status = "success"

        self.end_of_process = False

        #self.logger.debug("done init datacenter, resource, app_handler, optimizer, resource managers")

    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)

        # For monitoring test
        duration = 30.0
        expired = time.time() + duration
        while self.end_of_process == False:
            time.sleep(1)

            if self.config.db_keyspace != "none":
                event_list = self.db.get_events()
                if event_list == None:
                    self.logger.error("error while getting events from MUSIC")
                    break

                if len(event_list) > 0:
                    #self.logger.debug("got " + str(len(event_list)) + " events")
                    if self.handle_events(event_list) == False:
                        break

                request_list = self.db.get_requests()
                if request_list == None:
                    self.logger.error("error while getting requests from MUSIC")
                    break

                if len(request_list) > 0:
                    if self.place_app(request_list) == False:
                        break

            current = time.time()
            if current > expired:
                self.logger.debug("test: ostro running ......")
                expired = current + duration

        self.topology.end_of_process = True
        self.compute.end_of_process = True

        for t in self.thread_list:
            t.join()

        self.logger.info("exit Ostro")

    def stop_ostro(self):
        self.end_of_process = True
       
        while len(self.thread_list) > 0:
            time.sleep(1)
            for t in self.thread_list:
                if not t.is_alive():
                    self.thread_list.remove(t)

    def bootstrap(self):
        self.logger.info("--- start bootstrap ---")

        resource_status = self.db.get_resource_status(self.resource.datacenter.name)
        if resource_status == None:
            self.logger.error("error while getting resource status from MUSIC")
            return False

        if len(resource_status) > 0:
            self.logger.info("bootstrap from db")

            if self.resource.bootstrap_from_db(resource_status) == False:
                return False            

        else:
            self.logger.info("bootstrap from OpenStack")

            if self._set_hosts() == False:
                return False

            if self._set_flavors() == False:
                return False

            if self._set_topology() == False:
                return False

            if self.resource.update_topology() == False:
                pass

        self.logger.info("--- done bootstrap ---")

        return True

    def _set_topology(self):
        if self.topology.set_topology() == False:
            self.status = "datacenter configuration error"
            return False
            
        self.logger.debug("done topology bootstrap")

        return True

    def _set_hosts(self):
        if self.compute.set_hosts() == False:
            self.status = "OpenStack (Nova) internal error"
            return False
            
        self.logger.debug("done hosts & groups bootstrap")

        return True

    def _set_flavors(self):
        if self.compute.set_flavors() == False:     
            self.status = "OpenStack (Nova) internal error"
            return False                                                                        
                                                                                                 
        self.logger.debug("done flavors bootstrap")

        return True

    def place_app(self, _app_data):
        self.data_lock.acquire() 

        start_time = time.time()

        query_request_list = []
        placement_request_list = []
        for req in _app_data:
            if req["action"] == "query":
                query_request_list.append(req)
            else:
                placement_request_list.append(req)

        if len(query_request_list) > 0:
            self.logger.info("--- start query ---")

            query_results = self._query(query_request_list)

            result = self._get_json_results("query", "ok", self.status, query_results)

            if self.db.put_result(result) == False:
                self.logger.error("error while inserting placement result into MUSIC")
                self.data_lock.release()
                return False

            self.logger.info("--- done query ---")

        if len(placement_request_list) > 0:
            self.logger.info("--- start app placement ---")

            result = None

            placement_map = self._place_app(placement_request_list)

            if placement_map == None:
                result = self._get_json_results("placement", "error", self.status, placement_map)

                '''
                self.logger.debug("error while placing the following app(s)")
                for appk in result.keys():
                    self.logger.debug("    app uuid = " + appk)
                '''
            else:
                result = self._get_json_results("placement", "ok", "success", placement_map)

                #self.logger.debug("successful placement decision")

            if self.db.put_result(result) == False:
                self.logger.error("error while inserting placement result into MUSIC")
                self.data_lock.release()
                return False

            self.logger.info("--- done app placement ---")

        end_time = time.time()

        self.logger.info("stat: total running time of request = " + str(end_time - start_time) + " sec")

        self.data_lock.release()

        return True

    def _query(self, _query_list):
        query_results = {}

        for q in _query_list:
            if "type" in q.keys():
                if q["type"] == "group_vms":
                    if "parameters" in q.keys():
                        params = q["parameters"]
                        if "group_name" in params.keys():
                            vm_list = self._get_vms_from_logical_group(params["group_name"])
                            query_results[q["stack_id"]] = vm_list
                        else:
                            self.status = "unknown paramenter in query"
                            self.logger.debug(self.status)
                            query_results[q["stack_id"]] = None
                    else:
                        self.status = "no parameters in query"
                        self.logger.debug(self.status)
                        query_results[q["stack_id"]] = None
                else:
                    self.status = "unknown query type"
                    self.logger.debug(self.status)
                    query_results[q["stack_id"]] = None
            else: 
                self.status = "no type in query"
                self.logger.debug(self.status)
                query_results[q["stack_id"]] = None
 
        return query_results

    def _get_vms_from_logical_group(self, _group_name):
        vm_list = []

        vm_id_list = []
        for lgk, lg in self.resource.logical_groups.iteritems():
            if lg.group_type == "EX" or lg.group_type == "AFF":
                lg_id = lgk.split(":")
                if lg_id[1] == _group_name:
                    vm_id_list = lg.vm_list
                    break

        for vm_id in vm_id_list:
            if vm_id[2] != "none":
                vm_list.append(vm_id[2])

        return vm_list

    def _place_app(self, _app_data):
        app_topology = self.app_handler.add_app(_app_data)
        if app_topology == None:                                                                 
            self.status = self.app_handler.status
            self.logger.debug("error while register requested apps: " + self.status)
            return None
                 
        placement_map = self.optimizer.place(app_topology) 
        if placement_map == None: 
            self.status = self.optimizer.status
            self.logger.debug("error while optimizing app placement: " + self.status)
            return None

        if len(placement_map) > 0:
            if self.resource.update_topology() == False:
                pass 

            self.app_handler.add_placement(placement_map, self.resource.current_timestamp)

            if len(app_topology.exclusion_list_map) > 0 and len(app_topology.planned_vm_map) > 0:
                for vk in app_topology.planned_vm_map.keys():
                    if vk in placement_map.keys():
                        del placement_map[vk]
    
        return placement_map

    def handle_events(self, _event_list):
        self.data_lock.acquire() 

        #self.logger.info("--- start event handling ---")

        resource_updated = False

        for e in _event_list:
            if e.host != None and e.host != "none":
                if self._check_host(e.host) == False:
                    self.logger.warn("--- host (" + e.host + ") related to this event not exists")
                    continue

            if e.method == "build_and_run_instance":         # VM is created (from stack)
                self.logger.debug("--- got build_and_run event")
                if self.db.put_uuid(e) == False:
                    self.logger.error("error while inserting uuid into MUSIC")
                    self.data_lock.release()
                    return False         

            elif e.method == "object_action":
                if e.object_name == 'Instance':              # VM became active or deleted
                    orch_id = self.db.get_uuid(e.uuid)  
                    if orch_id == None:
                        self.logger.error("error while getting orchestration ids from MUSIC")
                        self.data_lock.release()
                        return False

                    if e.vm_state == "active": 
                        self.logger.debug("--- got instance_active event")
                        vm_info = self.app_handler.get_vm_info(orch_id[1], orch_id[0], e.host)
                        if vm_info == None:
                            self.logger.error("error while getting app info from MUSIC")
                            self.data_lock.release()
                            return False

                        if len(vm_info) == 0:
                            '''
                            h_uuid == None or "none" because vm is not created by stack
                            or, stack not found because vm is created by the other stack
                            '''
                            self.logger.warn("no vm_info found in app placement record")
                            self._add_vm_to_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)
                        else:
                            if "planned_host" in vm_info.keys() and vm_info["planned_host"] != e.host:
                                '''
                                vm is activated in the different host
                                '''
                                self.logger.warn("vm activated in the different host")
                                self._add_vm_to_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)
                                
                                self._remove_vm_from_host(e.uuid, orch_id[0], \
                                                          vm_info["planned_host"], \
                                                          float(vm_info["cpus"]), \
                                                          float(vm_info["mem"]), \
                                                          float(vm_info["local_volume"]))

                                self._remove_vm_from_logical_groups(e.uuid, orch_id[0], vm_info["planned_host"])
                            else:
                                '''
                                found vm in the planned host, 
                                possibly the vm deleted in the host while batch cleanup
                                '''
                                if self._check_h_uuid(orch_id[0], e.host) == False:
                                    self.logger.debug("planned vm was deleted")
                                    if self._check_uuid(e.uuid, e.host) == True:
                                        self._update_h_uuid_in_host(orch_id[0], e.uuid, e.host)
                                        self._update_h_uuid_in_logical_groups(orch_id[0], e.uuid, e.host)
                                else:
                                    self.logger.debug("vm activated as planned")
                                    self._update_uuid_in_host(orch_id[0], e.uuid, e.host)
                                    self._update_uuid_in_logical_groups(orch_id[0], e.uuid, e.host)
                        
                        resource_updated = True
                    
                    elif e.vm_state == "deleted":
                        self.logger.debug("--- got instance_delete event")

                        self._remove_vm_from_host(e.uuid, orch_id[0], e.host, e.vcpus, e.mem, e.local_disk)
                        self._remove_vm_from_logical_groups(e.uuid, orch_id[0], e.host)

                        if self.app_handler.update_vm_info(orch_id[1], orch_id[0]) == False:
                            self.logger.error("error while updating app in MUSIC")
                            self.data_lock.release()
                            return False

                        resource_updated = True
                    
                    else:
                        self.logger.warn("unknown vm_state = " + e.vm_state)

                elif e.object_name == 'ComputeNode':     # Host resource is updated
                    self.logger.debug("--- got compute event")
                    # NOTE: what if host is disabled?
                    if self.resource.update_host_resources(e.host, e.status, \
                                                           e.vcpus, e.vcpus_used, \
                                                           e.mem, e.free_mem, \
                                                           e.local_disk, e.free_local_disk, \
                                                           e.disk_available_least) == True:
                        self.resource.update_host_time(e.host)
                        
                        resource_updated = True
                    
                else:
                    self.logger.warn("unknown object_name = " + e.object_name)
            else:
                self.logger.warn("unknown event method = " + e.method)

        if resource_updated == True:
            if self.resource.update_topology() == False:
                pass

        for e in _event_list:
            #self.logger.debug("delete event = " + e.event_id)
            if self.db.delete_event(e.event_id) == False:
                self.logger.error("critical error while deleting event")
                self.data_lock.release()
                return False
            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.vm_state == "deleted":
                        #self.logger.debug("delete uuid")
                        if self.db.delete_uuid(e.uuid) == False:
                            self.data_lock.release()
                            return False

        #self.logger.info("--- done event handling ---")

        self.data_lock.release()

        return True

    def _add_vm_to_host(self, _uuid, _h_uuid, _host_name, _vcpus, _mem, _local_disk):
        vm_id = None
        if _h_uuid == None: 
            vm_id = ("none", "none", _uuid)
        else:
            vm_id = (_h_uuid, "none", _uuid)

        self.resource.add_vm_to_host(_host_name, vm_id, _vcpus, _mem, _local_disk)
        self.resource.update_host_time(_host_name)

    def _remove_vm_from_host(self, _uuid, _h_uuid, _host_name, _vcpus, _mem, _local_disk):
        if self._check_h_uuid(_h_uuid, _host_name) == True:
            self.resource.remove_vm_by_h_uuid_from_host(_host_name, _h_uuid, _vcpus, _mem, _local_disk)
            self.resource.update_host_time(_host_name)
        else:
            if self._check_uuid(_uuid, _host_name) == True:
                self.resource.remove_vm_by_uuid_from_host(_host_name, _uuid, _vcpus, _mem, _local_disk)
                self.resource.update_host_time(_host_name)

    def _remove_vm_from_logical_groups(self, _uuid, _h_uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if _h_uuid != None and _h_uuid != "none":
            self.resource.remove_vm_by_h_uuid_from_logical_groups(host, _h_uuid)
        else:
            self.resource.remove_vm_by_uuid_from_logical_groups(host, _uuid)

    def _check_host(self, _host_name):
        exist = False

        for hk in self.resource.hosts.keys():
            if hk == _host_name:
                exist = True
                break

        return exist

    def _check_h_uuid(self, _h_uuid, _host_name):
        if _h_uuid == None or _h_uuid == "none":
            return False

        host = self.resource.hosts[_host_name]

        return host.exist_vm_by_h_uuid(_h_uuid)

    def _check_uuid(self, _uuid, _host_name):
        if _uuid == None or _uuid == "none":
            return False

        host = self.resource.hosts[_host_name]

        return host.exist_vm_by_uuid(_uuid)

    def _update_uuid_in_host(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if host.update_uuid(_h_uuid, _uuid) == True:
            self.resource.update_host_time(_host_name)
        else:
            self.logger.warn("fail to update uuid in host = " + host.name)

    def _update_h_uuid_in_host(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]
        if host.update_h_uuid(_h_uuid, _uuid) == True:
            self.resource.update_host_time(_host_name)
        
    def _update_uuid_in_logical_groups(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]

        self.resource.update_uuid_in_logical_groups(_h_uuid, _uuid, host)
        
    def _update_h_uuid_in_logical_groups(self, _h_uuid, _uuid, _host_name):
        host = self.resource.hosts[_host_name]

        self.resource.update_h_uuid_in_logical_groups(_h_uuid, _uuid, host)

    def _get_json_results(self, _request_type, _status_type, _status_message, _map):
        result = {}

        if _request_type == "query":
            for qk, qr in _map.iteritems():
                query_result = {}

                query_status ={}
                if qr == None:
                    query_status['type'] = "error"
                else:
                    query_status['type'] = "ok"
                query_status['message'] = _status_message

                query_result['status'] = query_status
                if qr != None:
                    query_result['resources'] = qr

                result[qk] = query_result

        else:
            if _status_type != "error":
                applications = {}
                for v in _map.keys():
                    if isinstance(v, VM) or isinstance(v, Volume):
                        resources = None
                        if v.app_uuid in applications.keys():
                            resources = applications[v.app_uuid]
                        else:
                            resources = {}
                            applications[v.app_uuid] = resources

                        host = _map[v]
                        resource_property = {"host":host}
                        properties = {"properties":resource_property}
                        resources[v.uuid] = properties

                for appk, app_resources in applications.iteritems():
                    app_result = {}
                    app_status ={}

                    app_status['type'] = _status_type
                    app_status['message'] = _status_message

                    app_result['status'] = app_status
                    app_result['resources'] = app_resources

                    result[appk] = app_result

                for appk, app in self.app_handler.apps.iteritems():
                    if app.request_type == "ping":
                        app_result = {}
                        app_status ={}

                        app_status['type'] = _status_type
                        app_status['message'] = "ping"

                        app_result['status'] = app_status
                        app_result['resources'] = {"ip":self.config.ip}

                        result[appk] = app_result

            else:
                for appk in self.app_handler.apps.keys():
                    app_result = {}
                    app_status ={}

                    app_status['type'] = _status_type
                    app_status['message'] = _status_message

                    app_result['status'] = app_status
                    app_result['resources'] = {}

                    result[appk] = app_result

        return result


# Unit test

    

