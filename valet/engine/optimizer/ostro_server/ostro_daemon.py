#!/bin/python

# Modified: Sep. 22, 2016


import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from valet.engine.config import register_conf
from valet.engine.optimizer.ostro.ostro import Ostro
from valet.engine.optimizer.ostro_server.configuration import Config
from valet.engine.optimizer.ostro_server.daemon import Daemon   # implemented for Python v2.7


class OstroDaemon(Daemon):

    def run(self):

        self.logger.info("##### Valet Engine is launched #####")

        ostro = Ostro(config, logger)

        if ostro.bootstrap() is False:
            self.logger.error("ostro bootstrap failed")
            sys.exit(2)

        ostro.run_ostro()


if __name__ == "__main__":
    ''' configuration '''
    # Configuration
    register_conf()
    config = Config()
    config_status = config.configure()

    if config_status != "success":
        print(config_status)
        sys.exit(2)

    ''' create logging directories '''
    try:
        if not os.path.exists(config.logging_loc):
            os.makedirs(config.logging_loc)
    except OSError:
        print("Error while Ostro log dir")
        sys.exit(2)

    try:
        if not os.path.exists(config.resource_log_loc):
            os.makedirs(config.resource_log_loc)
    except OSError:
        print("Error while resource log dir")
        sys.exit(2)

    try:
        if not os.path.exists(config.app_log_loc):
            os.makedirs(config.app_log_loc)
    except OSError:
        print("Error while app log dir")
        sys.exit(2)

    ''' logger '''
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = RotatingFileHandler(config.logging_loc + config.logger_name,
                                      mode='a',
                                      maxBytes=config.max_main_log_size,
                                      backupCount=2,
                                      encoding=None,
                                      delay=0)
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger(config.logger_name)
    if config.logging_level == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    # Start daemon process
    daemon = OstroDaemon(config.priority, config.process, logger)

    exit_code = 0

    if config.command == 'start':
        daemon.start()
    elif config.command == 'stop':
        daemon.stop()
    elif config.command == 'restart':
        daemon.restart()
    elif config.command == 'status':
        exit_code = int(daemon.status())
    else:
        print("Unknown command: %s" % config.command)
        print("Usage: %s start|stop|restart" % sys.argv[0])
        exit_code = 2

    sys.exit(exit_code)
