#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
#
# Functions 
# - Create deamon process that starts RPC server and Ostro
#
#################################################################################################################


import sys, os, time, logging
import threading
import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from daemon import Daemon   # Implemented for Python v2.x
from gateway import Gateway
from configuration import Config


class AsyncXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer): pass

if __name__ == "__main__":
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Ostro: " + config_status
        sys.exit(2)

    logger = logging.getLogger(config.logger_name)
    if config.logging_level == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(config.logging_loc)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    try:
        gateway = Gateway(config, logger)

        #rpc_server = AsyncXMLRPCServer(("localhost", 8002), SimpleXMLRPCRequestHandler)
        rpc_server = SimpleXMLRPCServer((config.rpc_server_ip, config.rpc_server_port))
        rpc_server.register_introspection_functions()
        rpc_server.register_instance(gateway)
            
        rpc_server_thread = threading.Thread(target=rpc_server.serve_forever)
        rpc_server_thread.start()

        if gateway.start_ostro() == False:
            sys.exit(2)

        #while True:
            #time.sleep(1)

    except:
        e = sys.exc_info()[0]
        logger.error(e)
        sys.exit(2)


