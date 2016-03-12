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


import sys, logging

from daemon import Daemon   # Implemented for Python v2.x
from configuration import Config

sys.path.insert(0, '../ostro')
from ostro import Ostro


class OstroDaemon(Daemon):

    def run(self):

        self.logger.info("start logging.")

        ostro = Ostro(config, logger)

        if ostro.bootstrap() == False:
            sys.exit(2)

        ostro.run_ostro()



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


