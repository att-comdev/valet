#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
#
#################################################################################################################


import sys
import time
import json, simplejson
import operator


from configuration import Config

sys.path.insert(0, '../db_connect')
from music import Music


class EventGenerator:

    def __init__(self, _config):
        self.config = _config

        self.music = Music()

    def set_event(self, _k, _m, _event):
        args = open(_event, 'r')
        args_data = args.read()

        args_data = args_data.replace("'", '"')

        data = {
            'timestamp': str(_k),
            'exchange': 'nova',
            'method': _m,
            'args': args_data
        }

        print "set event = ", _k

        self.music.create_row(self.config.db_keyspace, self.config.db_event_table, data)


if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    eg = EventGenerator(config)
    
    time.sleep(5)
    eg.set_event(time.time(), "object_class_action", "./test_events/object_class_action_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "build_and_run_instance", "./test_events/build_and_run_instance_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_0.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_device_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_compute_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_reflesh_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_2.json")
    time.sleep(1)
    eg.set_event(time.time(), "service_update", "./test_events/service_update_1.json")
    time.sleep(1)



