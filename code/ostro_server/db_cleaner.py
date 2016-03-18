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

from configuration import Config

sys.path.insert(0, '../db_connect')
from music import Music


class DBCleaner:

    def __init__(self, _config):
        self.config = _config

        self.music = Music()

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

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_table)
        if len(results) > 0:
            for rowk, row in results.iteritems():
                self.music.delete_row_eventually(self.config.db_keyspace, \
                                                 self.config.db_app_table, \
                                                 'stack_id', row['stack_id'])

    def check_db_tables(self):
        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_table)
        if len(results) > 0:
            print "resource table not cleaned "
        else:
            print "resource table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)
        if len(results) > 0:
            print "request table not cleaned "
        else:
            print "request table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_response_table)
        if len(results) > 0:
            print "response table not cleaned "
        else:
            print "response table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)
        if len(results) > 0:
            print "event table not cleaned "
        else:
            print "event table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_resource_index_table)
        if len(results) > 0:
            print "resource log index table not cleaned "
        else:
            print "resource log index table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_index_table)
        if len(results) > 0:
            print "app log index table not cleaned "
        else:
            print "app log index table cleaned"

        results = self.music.read_all_rows(self.config.db_keyspace, self.config.db_app_table)
        if len(results) > 0:
            print "app log table not cleaned "
        else:
            print "app log table cleaned"


if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Ostro: " + config_status
        sys.exit(2)

    c = DBCleaner(config)
    c.clean_db_tables()
    c.check_db_tables()

