#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
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


class AppHandler:

    def __init__(self, _resource, _db, _logger):
        self.apps = {}  # Current app requested, a temporary copy
        #self.scheduled_apps = {} # pending before inserting apps into db until apps are placed in datacenter

        self.resource = _resource
        self.db = _db

        self.logger = _logger

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
            (app_id, app_name, vgroups, vms, vols) = app_topology.set_app_topology(app)
            self.logger.info("application: " + app_name)

            if len(vgroups) == 0 and len(vms) == 0 and len(volumes) == 0:
                self.logger.error(app_topology.status)
                self.status = app_topology.status
                return None
            else:
                new_app = App(app_id, app_name)
                new_app.set_app_components(vgroups, vms, vols)  

                self.apps[app_id] = new_app 

                # For test
                #new_app.print_app_info()

        app_topology.set_optimization_priority()

        return app_topology

    # Add placement of an app
    def add_placement(self, _placement_map, _timestamp):
        for v in _placement_map.keys():
            if self.apps[v.app_uuid].status == "requested":
                self.apps[v.app_uuid].status = "scheduled"
                self.apps[v.app_uuid].timestamp_scheduled = _timestamp

            if isinstance(v, VM):
                self.apps[v.app_uuid].vms[v.uuid]["status"] = "scheduled"
                self.apps[v.app_uuid].vms[v.uuid]["host"] = _placement_map[v]
            elif isinstance(v, Volume):
                self.apps[v.app_uuid].volumes[v.uuid]["status"] = "scheduled"
                self.apps[v.app_uuid].volumes[v.uuid]["host"] = _placement_map[v]
            #else:
                #self.apps[v.app_uuid].vgroups[v.uuid]["status"] = "scheduled"

        # For test
        #for appk in self.apps.keys():
            #self.apps[appk].print_app_info()

    def store_app_placements(self):
        app_list = []
        for appk in self.apps.keys():
            app_list.append(self.apps[appk].get_info_dict())

        self.db.insert("app", app_list)




