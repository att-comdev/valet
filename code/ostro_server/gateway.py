#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Handle user requests
#
#################################################################################################################


import sys
import logging
import time

from configuration import Config

sys.path.insert(0, '../ostro')
from ostro import Ostro


class Gateway:

    def __init__(self, _config, _logger):
        self.config = _config
        self.logger = _logger

        self.ostro = Ostro(self.config, self.logger)


# Unit test
if __name__ == '__main__':
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

    gw = Gateway(config, logger)
    if gw.ostro.bootstrap() == False:
        print "Error while bootstraping"

    time.sleep(1)
    result1 = gw.ostro.place_app_file("./test_inputs/simple_aggregates.json")
    print result1
    time.sleep(1)
    result2 = gw.ostro.place_app_file("./test_inputs/simple_exclusivity.json")
    print result2
    time.sleep(1)
    result3 = gw.ostro.place_app_file("./test_inputs/simple_mix_aggregate_exclusivity.json")
    print result3
    time.sleep(1)
    result4 = gw.ostro.place_app_file("./test_inputs/simple_mix_affinity_exclusivity.json")
    print result4
    time.sleep(1)
    result5 = gw.ostro.place_app_file("./test_inputs/simple_affinity.json")
    print result5
    time.sleep(1)
    result6 = gw.ostro.place_app_file("./test_inputs/simple_mix_affinity_affinity.json")
    print result6


