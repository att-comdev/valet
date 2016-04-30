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

    def get_resource_status(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_table)

    def get_apps(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_table)


if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    eg = EventGenerator(config)
    
    time.sleep(5)
    '''
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
    '''
    eg.set_event(time.time(), "object_action", "./test_events/object_action_compute_1.json")
    #time.sleep(1)
    '''
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_reflesh_1.json")
    time.sleep(1)
    eg.set_event(time.time(), "object_action", "./test_events/object_action_instance_2.json")
    time.sleep(1)
    eg.set_event(time.time(), "service_update", "./test_events/service_update_1.json")
    time.sleep(1)
    '''

    time.sleep(5)

    status = eg.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    apps = eg.get_apps()
    print "Applications"
    for rowk, row in apps.iteritems():
        app = json.loads(row['app'])
        print json.dumps(app, indent=4)
    

    remain_events = eg.music.read_all_rows(config.db_keyspace, config.db_event_table)
    if len(remain_events) > 0:
        print "Remained events"
        for rowk, row in remain_events.iteritems():
            event_id = row['timestamp']
            exchange = row['exchange']
            method = row['method']

            print "event_id=",event_id
            print "exchange=",exchange
            print "method=",method
    else:
        print "No remained events"


