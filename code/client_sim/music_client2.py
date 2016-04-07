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
import json


from configuration import Config

sys.path.insert(0, '../db_connect')
from music import Music


class MusicClient:

    def __init__(self, _config):
        self.config = _config

        self.music = Music()

    def set_request(self, _k, _request):
        request_graph = open(_request, 'r')
        request_data = request_graph.read()

        data = {
            'stack_id': _k,
            'request': request_data
        }

        print "test: request_data = ", request_data

        self.music.create_row(self.config.db_keyspace, self.config.db_request_table, data)

    def get_placements(self):
        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_response_table)
        
        if len(results) > 0:
            #self._remove_old_placements(results)

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

    def get_apps(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_table)


# Unit test
if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    mc = MusicClient(config)

    time.sleep(5)
    mc.set_request("app_uuid100", "./test_inputs/complex_mix_affinity_diversity.json")
    time.sleep(5)
    results = mc.get_placements()
    if results != None:
        print "Placement result"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)
    status = mc.get_resource_status()
    print "Resource status"
    for rowk, row in status.iteritems():
        resource = json.loads(row['resource'])
        print json.dumps(resource, indent=4)

    apps = mc.get_apps()
    print "Applications"
    for rowk, row in apps.iteritems():
        app = json.loads(row['app'])
        print json.dumps(app, indent=4)


