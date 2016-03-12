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
#from test_storage import TestStorage  
#from network_manager import NetworkManager

sys.path.insert(0, '../app_manager')
from app_handler import AppHandler  

sys.path.insert(0, '../music_interface')
from music import Music


class Ostro:

    def __init__(self, _config, _logger):
        self.config = _config

        self.logger = _logger

        self.db = None
        if self.config.db_keyspace != "none":
            self.db = self._init_db()

        self.resource = Resource(self.config, self.logger)

        self.app_handler = AppHandler(self.resource, self.config, self.logger)

        self.optimizer = Optimizer(self.resource, self.logger)

        self.data_lock = threading.Lock()
        self.thread_list = []

        self.topology = TopologyManager(1, "Topology", self.resource, self.data_lock, self.config, self.logger)
        self.compute = ComputeManager(2, "Compute", self.resource, self.data_lock, self.config, self.logger)
        #self.storage = TestStorage(3, "Storage", self.resource, self.data_lock, self.logger)
        #self.network = NetworkManager(3, "Network", self.resource, self.data_lock, self.config, self.logger)

        self.status = "success"

        self.end_of_process = False

    # TODO: error checking
    def _init_db(self):
        db = Music(self.config.db_keyspace)

        db.create_keyspace(self.config.db_keyspace)

        kwargs = {
            'keyspace': self.config.db_keyspace,
            'table': self.config.db_request_table_name,
            'schema': {
                'stack_id': 'text',
                'request': 'text',
                'PRIMARY KEY': '(stack_id)'
            }
        }
        db.create_table(**kwargs)

        kwargs = {
            'keyspace': self.config.db_keyspace,
            'table': self.config.db_reponse_table_name,
            'schema': {
                'stack_id': 'text',
                'placement': 'text',
                'PRIMARY KEY': '(stack_id)'
            }
        }
        db.create_table(**kwargs)

        kwargs = {
            'keyspace': self.config.db_keyspace,
            'table': self.config.db_resource_table_name,
            'schema': {
                'update_id': 'text',
                'resource_update': 'text',
                'PRIMARY KEY': '(update_id)'
            }
        }
        db.create_table(**kwargs)

        kwargs = {
            'keyspace': self.config.db_keyspace,
            'table': 'resource_status',
            'schema': {
                'site_name': 'text',
                'resource': 'text',
                'PRIMARY KEY': '(site_name)'
            }
        }
        db.create_table(**kwargs)

        return db

    def run_ostro(self):
        self.logger.info("start Ostro ......")

        self.topology.start()
        self.compute.start()
        #self.storage.start()
        #self.network.start()

        self.thread_list.append(self.topology)
        self.thread_list.append(self.compute)
        #self.thread_list.append(self.storage)
        #self.thread_list.append(self.network)

        while self.end_of_process == False:
            time.sleep(1)

            self.logger.debug("ostro running......")

            self._get_requests()

        self.topology.end_of_process = True
        self.compute.end_of_process = True
        #self.storage.end_of_process = True
        #self.network.end_of_process = True

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
        if self._set_topology() == False:
            return False

        if self._set_hosts() == False:
            return False

        #if self._set_network_topology() == False:
            #return False

        #if self._set_storages() == False:
            #return False

        if self._set_flavors() == False:
            return False

        resource_status = self.resource.update_topology()  
        
        self.db.create_row('resource_status', values=resource_status)

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

    #def _set_storages(self):
        #if self.storage.set_storages() == False:
            #self.status = "OpenStack (Cinder) internal error"
            #return False

        #return True

    #def _set_network_topology(self):                                                
        #if self.network.set_network_topology() == False:
            #self.status = "Tegu interanl error"                                          
            #return False                                                                         
                                                                                                 
        #return True 

    def _set_flavors(self):
        if self.compute.set_flavors() == False:     
            self.status = "OpenStack (Nova) internal error"
            return False                                                                        
                                                                                                 
        return True

    def _get_requests(self):
        resource_updates = self.db.read_all_rows(self.config.db_resource_table_name)
        #if len(resource_updates) > 0:
            # Update resource status
            # Delete each row once done

        requests = self.db.read_all_rows(self.config.db_request_table_name)
        #if len(requests) > 0:
            # Place applications

    # Place an app based on the topology file, wrapper of place_app
    def place_app_file(self, _topology_file):
        app_graph = open(_topology_file, 'r')
        app_data = app_graph.read()
        if app_data == None:
            return self._get_json_format("error", "topology file not found!", None)

        return self.place_app(app_data)

    # Place an app based on the app_data(a string serialization of json). 
    def place_app(self, _app_data):
        self.logger.info("start app placement")

        result = None

        start_time = time.time()
        placement_map = self._place_app(_app_data)
        end_time = time.time()

        if placement_map == None:
            result = self._get_json_format("error", self.ostro.status, None)
        else:
            result = self._get_json_format("ok", "success", placement_map)

        self.logger.info("total running time of place_app = " + str(end_time - start_time) + " sec")
        self.logger.info("done app placement")

        return result

    def _place_app(self, _app_data):
        self.data_lock.acquire(1) 

        # Record the input app topology in memory
        app_topology = self.app_handler.add_app(_app_data)
        if app_topology == None:                                                                 
            self.status = self.app_handler.status
            return None
                 
        # Place application 
        placement_map = self.optimizer.place(app_topology) 
        if placement_map == None:                                                                
            self.status = self.optimizer.status
            return None
        self.resource.update_topology()  
                                                                                                 
        # Once placement is done, update the app info                                            
        self.app_handler.add_placement(placement_map, self.resource.current_timestamp)

        self.data_lock.release()

        return placement_map

    # Return json format
    def _get_json_format(self, _status_type, _status_message, _placement_map):
        resources = {}
        result = None

        if _status_type != "error":
            for v in _placement_map.keys():
                host = _placement_map[v]
                #resource_property = {"availability_zone":host}
                resource_property = {"host":host}
                properties = {"properties":resource_property}
                resources[v.uuid] = properties

        result = json.dumps({"status":{"type":_status_type, "message":_status_message}, \
                             "resources":resources}, indent=4, separators=(',', ':'))

        return result


# Unit test

    

