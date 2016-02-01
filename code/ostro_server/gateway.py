#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
#
# Functions 
# - Handle user requests
#
#################################################################################################################


import sys
import json
import logging
import time

sys.path.insert(0, '../ostro')
from ostro import Ostro


class Gateway:

    def __init__(self, _config, _logger):
        self.config = _config
        self.logger = _logger
        self.logger.info("start logging.")

        self.ostro = Ostro(self.config, self.logger)

    def start_ostro(self):
        return self.ostro.run_ostro()

    # Return json format
    def get_json_format(self, _status_type, _status_message, _placement_map):
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

    # Place an app based on the topology file, wrapper of place_app
    def place_app_file(self, _topology_file):
        app_graph = open(_topology_file, 'r')
        app_data = app_graph.read()
        if app_data == None:
            return self.get_json_format("error", "topology file not found!", None)

        return self.place_app(app_data)

    # Place an app based on the app_data(a string serialization of json). 
    def place_app(self, _app_data):
        self.logger.info("start app placement")

        result = None
    
        start_time = time.time()
        placement_map = self.ostro.place_app(_app_data)
        end_time = time.time()

        if placement_map == None:
            result = self.get_json_format("error", self.ostro.status, None)
        else:
            result = self.get_json_format("ok", "success", placement_map)
            
        self.logger.info("total running time of place_app = " + str(end_time - start_time) + " sec")
        self.logger.info("done app placement")        

        return result

    def print_tester(self):
        return self.get_json_format("test", "test", {})



# Unit test
if __name__ == '__main__':
    # Logger 
    logger = logging.getLogger("TestLog")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("./ostro_log/test.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    gw = Gateway(logger)
    gw.start_ostro()
    #time.sleep(1)
    result1 = gw.place_app_file("./test_app_inputs/affinity.json")
    print result1
    result2 = gw.place_app_file("./test_app_inputs/io_affinity.json")
    print result2


