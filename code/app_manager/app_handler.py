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
from os import listdir, stat
from os.path import isfile, join

from app_topology import AppTopology 
from app_topology_base import VM, Volume
from application import App

sys.path.insert(0, '../util')
from util import get_logfile


class AppHandler:

    def __init__(self, _resource, _db, _config, _logger):
        self.resource = _resource
        self.db = _db
        self.config = _config
        self.logger = _logger

        self.apps = {}  # Current app requested, a temporary copy

        self.status = "success"

    # Record application topology
    def add_app(self, _app_data):
        self.apps.clear()

        app_topology = AppTopology(self.resource)

        app_list = None
        try:
            app_list = json.loads(_app_data)
        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while reading app topology")
            self.status = "JSON internal error"
            return None

        for app in app_list:
            #(app_id, app_name, vgroups, vms, vols) = app_topology.set_app_topology(app)
            app_id = app_topology.set_app_topology(app)
            #self.logger.info("application: " + app_name)

            #if len(vgroups) == 0 and len(vms) == 0 and len(volumes) == 0:
            if app_id == None:
                self.logger.error(app_topology.status)
                self.status = app_topology.status
                return None
            else:
                self.logger.info("application: " + app_id[1])

                #new_app = App(app_id, app_name)
                new_app = App(app_id[0], app_id[1])
                #new_app.set_app_components(vgroups, vms, vols)

                #self.apps[app_id] = new_app 
                self.apps[app_id[0]] = new_app 

        app_topology.set_optimization_priority()

        return app_topology

    # Add placement of an app
    def add_placement(self, _placement_map, _timestamp):
        for v in _placement_map.keys():
            if self.apps[v.app_uuid].status == "requested":
                self.apps[v.app_uuid].status = "scheduled"
                self.apps[v.app_uuid].timestamp_scheduled = _timestamp

            if isinstance(v, VM):
                #self.apps[v.app_uuid].vms[v.uuid]["status"] = "scheduled"
                #self.apps[v.app_uuid].vms[v.uuid]["host"] = _placement_map[v]
                self.apps[v.app_uuid].add_vm(v, _placement_map[v])
            elif isinstance(v, Volume):
                #self.apps[v.app_uuid].volumes[v.uuid]["status"] = "scheduled"
                #self.apps[v.app_uuid].volumes[v.uuid]["host"] = _placement_map[v]
                self.apps[v.app_uuid].add_volume(v, _placement_map[v])
            else:
                #self.apps[v.app_uuid].vgroups[v.uuid]["status"] = "scheduled"
                if _placement_map[v] in self.resource.hosts.keys():
                    host = self.resource.hosts[_placement_map[v]]
                    if v.level == "host":
                        self.apps[v.app_uuid].add_vgroup(v, host.name)
                else:
                    hg = self.resource.host_groups[_placement_map[v]]
                    if v.level == hg.host_type:
                        self.apps[v.app_uuid].add_vgroup(v, hg.name)

        self._store_app_placements()

    # Need to store app in Music???
    # Consider rollback and re-placements from history!
    def _store_app_placements(self):
        (app_logfile, mode) = get_logfile(self.config.app_log_loc, \
                                          self.config.max_log_size, \
                                          self.resource.datacenter.name)
        logging = open(self.config.app_log_loc + app_logfile, mode)

        for appk, app in self.apps.iteritems():
            json_logging = app.get_json_info()
            logged_data = json.dumps(json_logging)

            logging.write(logged_data)
            logging.write("\n")

        logging.close()
        #self.db.insert("app", app_list)




