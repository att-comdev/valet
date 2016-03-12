#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
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


class OstroDaemon(Daemon):

    def run(self):
        try:
            # Create a gateway (a list of RPC functions) with db keyspace
            gateway = Gateway(config, logger)

            # Create RPC server
            #rpc_server = AsyncXMLRPCServer(("localhost", 8002), SimpleXMLRPCRequestHandler)
            rpc_server = SimpleXMLRPCServer((config.rpc_server_ip, config.rpc_server_port))
            rpc_server.register_introspection_functions()
            rpc_server.register_instance(gateway)

            # Run the RPC server as a thread
            rpc_server_thread = threading.Thread(target=rpc_server.serve_forever)
            rpc_server_thread.start()

            # Start Ostro threads
            if gateway.start_ostro() == False:
                sys.exit(2)

            #while True:
                #time.sleep(1)

        except:
            e = sys.exc_info()[0]
            self.logger.error(e)
            sys.exit(2)



if __name__ == "__main__":
    # Configuration
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Ostro: " + config_status
        sys.exit(2)

    # Logger 
    logger = logging.getLogger(config.logger_name)
    if config.logging_level == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(config.logging_loc)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Start daemon process
    daemon = OstroDaemon(config.process, logger)

    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "Usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)


