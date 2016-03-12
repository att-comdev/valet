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
import json

from configuration import Config

sys.path.insert(0, '../ostro')
from ostro import Ostro

sys.path.insert(0, '../db_connect')
from music import Music


class Gateway:

    def __init__(self, _config, _logger):
        self.config = _config

        self.music = Music()

        self.ostro = Ostro(self.config, _logger)

    def bootstrap(self):
        return self.ostro.bootstrap()

    def set_request(self, _k, _request):
        request_graph = open(_request, 'r')
        request_data = request_graph.read()

        data = {
            'stack_id': _k,
            'request': request_data
        }

        self.music.create_row(self.config.db_keyspace, self.config.db_request_table, data)

    def place_app(self):
        (event_list, request_list) = self.ostro.db.get_requests()                                
                                                                                                 
        if len(request_list) > 0:                                                        
            result = self.ostro.place_app(request_list)                                        
            self.ostro.db.put_result(result)

    def get_placements(self):
        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_response_table)
        
        if len(results) > 0:
            self._remove_old_placements(results)

            return results
        else:
            return None

    def _remove_old_placements(self, _results):
        for rowk, row in _results.iteritems():
            stack_id = row['stack_id']
            self.music.delete_row_eventually(self.config.db_keyspace, \
                                             self.config.db_response_table, \
                                             'stack_id', \
                                             stack_id)

    def get_resource_status(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_table)

    def clean_db_tables(self):
        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_resource_table, \
                                                 'site_name', row['site_name'])

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_request_table, \
                                                 'stack_id', row['stack_id'])

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_response_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_response_table, \
                                                 'stack_id', row['stack_id'])

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_event_table, \
                                                 'event_id', row['event_id'])

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_index_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_resource_index_table, \
                                                 'site_name', row['site_name'])

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_index_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_app_index_table, \
                                                 'site_name', row['site_name'])



# Unit test
'''
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

    gw.clean_db_tables()

    if gw.bootstrap() == False:
        print "Error while bootstraping"

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_aggregates.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_exclusivity.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_mix_aggregate_exclusivity.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_mix_affinity_exclusivity.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_affinity.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    time.sleep(1)
    gw.set_request("app_uuid", "./test_inputs/simple_mix_affinity_affinity.json")
    gw.place_app()
    results = gw.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = gw.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)
'''

