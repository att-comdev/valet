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

        self.logger.debug("done init datacenter, resource, app_handler, optimizer, resource managers")

    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)

        while self.end_of_process == False:
            time.sleep(1)

            if self.config.db_keyspace != "none":
                (event_list, request_list) = self.db.get_requests()

                if len(event_list) > 0:
                    pass

                if len(request_list) > 0:
                    self.place_app(request_list)

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

            # NOTE: currently topology relies on hosts naming convention
            if self._set_topology() == False:
                return False

            self.resource.update_topology()

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
        self.data_lock.acquire(1) 

        self.logger.info("--- start app placement ---")

        result = None

        start_time = time.time()
        placement_map = self._place_app(_app_data)
        end_time = time.time()

        if placement_map == None:
            result = self._get_json_results("error", self.status, placement_map)

            self.logger.debug("error while placing the following app(s)")
            for appk in result.keys():
                self.logger.debug("    app uuid = " + appk)
        else:
            result = self._get_json_results("ok", "success", placement_map)

            self.logger.debug("successful placement decision")

        self.db.put_result(result)

        self.logger.info("stat: total running time of place_app = " + str(end_time - start_time) + " sec")
        self.logger.info("--- done app placement ---")

        self.data_lock.release()

    def _place_app(self, _app_data):
        app_topology = self.app_handler.add_app(_app_data)
        if app_topology == None:                                                                 
            self.status = self.app_handler.status

            self.logger.debug("error while register requested apps:" + self.status)

            return None
                 
        placement_map = self.optimizer.place(app_topology) 
        if placement_map == None: 
            self.status = self.optimizer.status

            self.logger.debug("error while optimizing app placement:" + self.status)

            return None

        if len(placement_map) > 0:
            resource_status = self.resource.update_topology()  

            self.app_handler.add_placement(placement_map, self.resource.current_timestamp)

        return placement_map

    def _get_json_results(self, _status_type, _status_message, _placement_map):
        result = {}

        if _status_type != "error":
            applications = {}
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

    

