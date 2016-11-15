#!/bin/python

# Modified: Sep. 22, 2016


import logging
from logging.handlers import RotatingFileHandler
import os
import sys

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


def verify_dirs(list_of_dirs):
    for d in list_of_dirs:
        try:
            if not os.path.exists(d):
                os.makedirs(d)
        except OSError:
            print("Error while verifying: " + d)
            sys.exit(2)


if __name__ == "__main__":
    ''' configuration '''
    # Configuration
    print("load configuration...")
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print(config_status)
        sys.exit(2)

    ''' verify directories '''
    print("verify directories...")
    dirs_list = [config.logging_loc, config.resource_log_loc, config.app_log_loc, os.path.dirname(config.process)]
    verify_dirs(dirs_list)

    ''' logger '''
    print("build logger...")
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
    print("call daemon with command '%s'..." % config.command)

    # Start daemon process
    daemon = OstroDaemon(config.priority, config.process, logger)

    exit_code = 0
    if config.command == 'start':
        logger.info("start ostro...")
        daemon.start()
    elif config.command == 'stop':
        logger.info("stop ostro...")
        daemon.stop()
    elif config.command == 'restart':
        logger.info("restart ostro...")
        daemon.restart()
    elif config.command == 'status':
        logger.info("status ostro...")
        exit_code = int(daemon.status())
    else:
        print("Unknown command: %s" % config.command)
        print("Usage: %s start|stop|restart" % sys.argv[0])
        exit_code = 2

    sys.exit(exit_code)
