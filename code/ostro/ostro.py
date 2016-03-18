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

sys.path.insert(0, '../db_connect')
from music_handler import MusicHandler


class Ostro:

    def __init__(self, _config, _logger):
        self.config = _config

        self.logger = _logger

        self.db = None
        if self.config.db_keyspace != "none":
            self.db = MusicHandler(self.config, self.logger)
            self.db.init_db()

        self.resource = Resource(self.db, self.config, self.logger)

        self.app_handler = AppHandler(self.resource, self.db, self.config, self.logger)

        self.optimizer = Optimizer(self.resource, self.logger)

        self.data_lock = threading.Lock()
        self.thread_list = []

        self.topology = TopologyManager(1, "Topology", self.resource, self.data_lock, self.config, self.logger)
        self.compute = ComputeManager(2, "Compute", self.resource, self.data_lock, self.config, self.logger)

        self.status = "success"

        self.end_of_process = False

    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)

        while self.end_of_process == False:
            time.sleep(1)

            #self.logger.debug("ostro running......")

            if self.config.db_keyspace != "none":
                (event_list, request_list) = self.db.get_requests()

                if len(event_list) > 0:
                    pass

                if len(request_list) > 0:
                    result = self.place_app(request_list)
                    self.db.put_result(result)

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
        if self._set_hosts() == False:
            return False

        if self._set_flavors() == False:
            return False

        # NOTE: currently topology relies on hosts naming convention
        if self._set_topology() == False:
            return False

        self.resource.update_topology()

        return True

    def _set_topology(self):
        if self.topology.set_topology() == False:
            self.status = "Datacenter configuration error"
            return False

        return True

    def _set_hosts(self):
        if self.compute.set_hosts() == False:
            self.status = "OpenStack (Nova) internal error"
            return False

        return True

    def _set_flavors(self):
        if self.compute.set_flavors() == False:     
            self.status = "OpenStack (Nova) internal error"
            return False                                                                        
                                                                                                 
        return True

    def place_app(self, _app_data):
        self.logger.info("--- start app placement ---")

        result = None

        start_time = time.time()
        (stack_id, placement_map) = self._place_app(_app_data)
        end_time = time.time()

        if len(placement_map) == 0:
            result = self._get_json_results("error", self.status, stack_id, placement_map)
            self.logger.error("error while placing app = " + stack_id)
        else:
            result = self._get_json_results("ok", "success", stack_id, placement_map)

        self.logger.info("total running time of place_app = " + str(end_time - start_time) + " sec")
        self.logger.info("--- done app placement ---")

        return result

    def _place_app(self, _app_data):
        self.data_lock.acquire(1) 

        (stack_id, app_topology) = self.app_handler.add_app(_app_data)
        if app_topology == None:                                                                 
            self.status = self.app_handler.status
            return (stack_id, {})
                 
        (stack_id, placement_map) = self.optimizer.place(app_topology) 
        if len(placement_map) == 0: 
            self.status = self.optimizer.status
            return (stack_id, placement_map)

        resource_status = self.resource.update_topology()  

        self.app_handler.add_placement(placement_map, self.resource.current_timestamp)

        self.data_lock.release()

        return (stack_id, placement_map)

    def _get_json_results(self, _status_type, _status_message, _stack_id, _placement_map):
        applications = {}
        result = {}

        if _status_type != "error":
            for v in _placement_map.keys():
                resources = None
                if v.app_uuid in applications.keys():
                    resources = applications[v.app_uuid]
                else:
                    resources = {}
                    applications[v.app_uuid] = resources

                host = _placement_map[v]
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
        else:
            app_result = {}
            app_status ={}

            app_status['type'] = _status_type
            app_status['message'] = _status_message

            app_result['status'] = app_status
            app_result['resources'] = {}

            result[_stack_id] = app_result

        return result


# Unit test

    

