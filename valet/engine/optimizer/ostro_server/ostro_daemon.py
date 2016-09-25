#!/bin/python

# Modified: Sep. 16, 2016


from configuration import Config
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from daemon import Daemon   # implemented for Python v2.7
from valet.engine.optimizer.ostro.ostro import Ostro

''' for unit test '''
'''
sys.path.insert(0, '../ostro')
from ostro import Ostro
'''


class OstroDaemon(Daemon):

    def run(self):

        self.logger.info("##### Valet Engine is launched #####")

        ostro = Ostro(config, logger)

        if ostro.bootstrap() is False:
            sys.exit(2)

        ostro.run_ostro()


if __name__ == "__main__":
    ''' configuration '''
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

    if config.mode.startswith("sim"):
        try:
            if not os.path.exists(config.eval_log_loc):
                os.makedirs(config.eval_log_loc)
        except OSError:
            print("Error while evaluation log dir")
            sys.exit(2)

    ''' logger '''
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = RotatingFileHandler(config.logging_loc + config.logger_name + ".log",
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

    ''' launch daemon process '''
    daemon = OstroDaemon(config.priority, config.process, logger)

    exit_code = 0

    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        elif sys.argv[1] == 'status':
            exit_code = int(daemon.status())
        else:
            print("Unknown command")
            exit_code = 2
    else:
        print("Usage: %s start|stop|restart" % sys.argv[0])
        exit_code = 2
    sys.exit(exit_code)
