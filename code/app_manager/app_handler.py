#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Keep the current application requested
# - Store the placement into database
#
#################################################################################################################


import sys
import json

from app_topology import AppTopology 
from app_topology_base import VM, Volume
from application import App

sys.path.insert(0, '../util')
from util import get_last_logfile


class AppHandler:

    def __init__(self, _resource, _db, _config, _logger):
        self.resource = _resource
        self.db = _db
        self.config = _config
        self.logger = _logger

        self.apps = {}  # Current app requested, a temporary copy

        self.last_log_index = 0

        self.status = "success"

    # Record application topology
    def add_app(self, _app_data):
        self.apps.clear()

        '''
        if len(self.apps) > 0:
            self.logger.error("cannot clear prior requested apps")
        '''

        app_topology = AppTopology(self.resource, self.logger)

        for app in _app_data:
            self.logger.debug("parse app")

            app_id = app_topology.set_app_topology(app)

            if app_id == None:
                self.logger.error(app_topology.status)
                self.status = app_topology.status
                return None
            else:
                self.logger.info("application: " + app_id[1] + " with action = " + app_id[2])

                new_app = App(app_id[0], app_id[1], app_id[2])

                self.apps[app_id[0]] = new_app

        if len(app_topology.vgroups) > 0 or \
           len(app_topology.vms) > 0 or \
           len(app_topology.volumes) > 0:
            self.logger.debug("virtual resources are captured")

        app_topology.set_optimization_priority()

        return app_topology

    # Add placement of an app
    def add_placement(self, _placement_map, _timestamp):
        for v in _placement_map.keys():
            if self.apps[v.app_uuid].status == "requested":
                self.apps[v.app_uuid].status = "scheduled"
                self.apps[v.app_uuid].timestamp_scheduled = _timestamp

            if isinstance(v, VM):
                self.apps[v.app_uuid].add_vm(v, _placement_map[v])
            elif isinstance(v, Volume):
                self.apps[v.app_uuid].add_volume(v, _placement_map[v])
            else:
                if _placement_map[v] in self.resource.hosts.keys():
                    host = self.resource.hosts[_placement_map[v]]
                    if v.level == "host":
                        self.apps[v.app_uuid].add_vgroup(v, host.name)
                else:
                    hg = self.resource.host_groups[_placement_map[v]]
                    if v.level == hg.host_type:
                        self.apps[v.app_uuid].add_vgroup(v, hg.name)

        self._store_app_placements()

    def _store_app_placements(self):
        (app_logfile, last_index, mode) = get_last_logfile(self.config.app_log_loc, \
                                                           self.config.max_log_size, \
                                                           self.config.max_num_of_logs, \
                                                           self.resource.datacenter.name, \
                                                           self.last_log_index)
        self.last_log_index = last_index

        # TODO: error handling

        logging = open(self.config.app_log_loc + app_logfile, mode)

        for appk, app in self.apps.iteritems():
            json_log = app.log_in_info()
            log_data = json.dumps(json_log)

            logging.write(log_data)
            logging.write("\n")

        logging.close()

        self.logger.info("log: app placement timestamp in " + app_logfile)

        if self.db != None:
            self.db.update_app_log_index(self.resource.datacenter.name, self.last_log_index)
   
            for appk, app in self.apps.iteritems():
                json_info = app.get_json_info()
                self.db.add_app(appk, json_info)

    def get_vm_info(self, _s_uuid, _h_uuid, _host):
        vm_info = {}

        if _h_uuid != None and _h_uuid != "none" and \
           _s_uuid != None and _s_uuid != "none":
            vm_info = self.db.get_vm_info(_s_uuid, _h_uuid, _host)
            
        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        if _h_uuid != None and _h_uuid != "none" and \
           _s_uuid != None and _s_uuid != "none":
            self.db.update_vm_info(_s_uuid, _h_uuid)











