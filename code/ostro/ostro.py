#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Dec. 7, 2015
#
# Functions 
# - Deal with placement requests
# - Run all resource managers (Topology, Compute, Stroage, Network)
#
#################################################################################################################


import threading
import time
import sys
import logging

#from displayer import display_dc_topology, display_app_topology
from optimizer import Optimizer   

sys.path.insert(0, '../resource_manager')
from resource_base import Datacenter
from resource import Resource
from topology_manager import TopologyManager
from compute_manager import ComputeManager
#from test_storage import TestStorage  # TODO
#from network_manager import NetworkManager

sys.path.insert(0, '../app_manager')
from app_handler import AppHandler  

#sys.path.insert(0, '../db_connect')
#from db_connector import DatabaseConnector


class Ostro:

    def __init__(self, _config, _logger):
        self.config = _config

        self.logger = _logger

        self.db = None

        self.resource = None

        self.app_handler = None
        self.optimizer = None

        self.topology = None
        self.compute = None
        #self.storage = None
        #self.network = None

        self.status = "success"

        self.data_lock = threading.Lock()
        self.end_of_process = False

    def run_ostro(self):
        self.logger.info("start Ostro ......")
    
        #if self.config.db_keyspace != "none":
            #self.db = DatabaseConnector(self.config.db_keyspace)

        self.resource = Resource(self.db, self.logger)

        self.app_handler = AppHandler(self.resource, self.db, self.logger)
        self.optimizer = Optimizer(self.resource, self.logger)

        thread_list = []

        if self.config.mode.startswith("sim") == True:
            self.resource.datacenter = Datacenter(self.config.mode)
        else: 
            self.resource.datacenter = Datacenter(self.config.datacenter_name)

        self.topology = TopologyManager(1, "Topology", self.resource, self.data_lock, self.config, self.logger)
        self.compute = ComputeManager(2, "Compute", self.resource, self.data_lock, self.config, self.logger)
        #self.storage = TestStorage(3, "Storage", self.resource, self.data_lock, self.logger)
        #self.network = NetworkManager(3, "Network", self.resource, self.data_lock, self.config, self.logger)

        if self._bootstrap_topology() == False:
            return False

        # For test
        #display_dc_topology(self.resource)

        self.topology.start()
        self.compute.start()
        #self.storage.start()
        #self.network.start()

        thread_list.append(self.topology)
        thread_list.append(self.compute)
        #thread_list.append(self.storage)
        #thread_list.append(self.network)

        test_duration = 100
        test_end = time.time() + test_duration
        while self.end_of_process == False:
            time.sleep(1)

            self.logger.debug("ostro running......")
            if time.time() > test_end:
                self.end_of_process = True

        self.topology.end_of_process = True
        self.compute.end_of_process = True
        #self.storage.end_of_process = True
        #self.network.end_of_process = True

        time.sleep(1)

        for t in thread_list:
            t.join()

        self.logger.info("exit Ostro")

        return True

    def _bootstrap_topology(self):
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

        #self.resource.update_metadata()
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

    def place_app(self, _app_data):
        self.data_lock.acquire(1) 

        # Record the input app topology in memory
        app_topology = self.app_handler.add_app(_app_data)
        if app_topology == None:                                                                 
            self.status = self.app_handler.status
            return None
                 
        # For test                                                                                
        #display_app_topology(app_topology)                                           
                                                                                                 
        # Place application 
        placement_map = self.optimizer.place(app_topology) 
        if placement_map == None:                                                                
            self.status = self.optimizer.status
            return None
        self.resource.update_topology()  
                                                                                                 
        # Once placement is done, update the app info                                            
        self.app_handler.add_placement(placement_map, self.resource.current_timestamp)
        #self.app_handler.store_app_placements()

        self.data_lock.release()

        return placement_map



# Unit test
if __name__ == "__main__":
    logger = logging.getLogger("TestLog")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("../ostro_server/ostro_log/test.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    ostro = Ostro(logger)
    ostro.run_ostro()

    

