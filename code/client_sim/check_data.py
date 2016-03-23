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

    def get_resource_status(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_table)

    def get_apps(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_table)

    def get_requests(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)

    def get_responses(self):
        return self.music.read_all_rows(self.config.db_keyspace, self.config.db_response_table)


# Unit test
if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    mc = MusicClient(config)

    results = mc.get_requests()
    if results != None:
        print "Requests"
        for rowk, row in results.iteritems():
            placement = json.loads(row['request'])
            print json.dumps(placement, indent=4)

    results = mc.get_responses()
    if results != None:
        print "Responses"
        for rowk, row in results.iteritems():
            placement = json.loads(row['placement'])
            print json.dumps(placement, indent=4)

    results = mc.get_apps()
    if results != None:
        print "Apps"
        for rowk, row in results.iteritems():
            placement = json.loads(row['app'])
            print json.dumps(placement, indent=4)
