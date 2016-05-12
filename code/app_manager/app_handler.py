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

            stack_id = None
            if "stack_id" in app.keys():
                stack_id = app["stack_id"]
            else:
                stack_id = "none"
            application_name = None
            if "application_name" in app.keys():
                application_name = app["application_name"]
            else:
                application_name = "none"
            action = None
            if "action" in app.keys():
                action = app["action"]
            else:
                action = "any"
 
            if action == "ping":
                self.logger.debug("got ping")
            elif action == "replan":
                re_app = self._regenerate_app_topology(stack_id, app, app_topology)
                if re_app == None:
                    return None

                self.logger.debug("got replan: " + stack_id)

                app_id = app_topology.set_app_topology(re_app)

                if app_id == None:
                    self.logger.error(app_topology.status)
                    self.status = app_topology.status
                    return None

                self.logger.info("replanned  application: " + app_id[1])
            else:
                app_id = app_topology.set_app_topology(app)

                if app_id == None:
                    self.logger.error(app_topology.status)
                    self.status = app_topology.status
                    return None

                self.logger.info("got application: " + app_id[1])

            new_app = App(stack_id, application_name, action)
            self.apps[stack_id] = new_app

        if len(app_topology.vgroups) > 0 or len(app_topology.vms) > 0 or len(app_topology.volumes) > 0:
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

        if self._store_app_placements() == False:
            # TODO: ignore?
            pass

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
            for appk, app in self.apps.iteritems():
                json_info = app.get_json_info()
                if self.db.add_app(appk, json_info) == False:
                    self.logger.error("error while adding app info to MUSIC")
                    return False

            if self.db.update_app_log_index(self.resource.datacenter.name, self.last_log_index) == False:
                self.logger.error("error while updating app log index in MUSIC")
                return False

        return True
   
    def get_vm_info(self, _s_uuid, _h_uuid, _host):
        vm_info = {}

        if _h_uuid != None and _h_uuid != "none" and \
           _s_uuid != None and _s_uuid != "none":
            vm_info = self.db.get_vm_info(_s_uuid, _h_uuid, _host)
            
        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        if _h_uuid != None and _h_uuid != "none" and \
           _s_uuid != None and _s_uuid != "none":
            if self.db.update_vm_info(_s_uuid, _h_uuid) == False:
                return False

        return True

    def _regenerate_app_topology(self, _stack_id, _app, _app_topology):
        re_app = {}
       
        old_app = self.db.get_app_info(_stack_id)
        if old_app == None:
            self.status = "error while getting old_app from MUSIC"
            self.logger.error(self.status)
            return None
        elif len(old_app) == 0:
            self.status = "cannot find the old app in MUSIC"
            self.logger.error(self.status)
            return None

        re_app["action"] = "create"
        re_app["stack_id"] = _stack_id
        
        resources = {}
        diversity_groups = {}
        exclusivity_groups = {}

        if "VMs" in old_app.keys():
            for vmk, vm in old_app["VMs"].iteritems():
                resources[vmk] = {}
                resources[vmk]["name"] = vm["name"] 
                resources[vmk]["type"] = "OS::Nova::Server"
                properties = {}
                properties["flavor"] = vm["flavor"]
                if vm["availability_zone"] != "none":
                    properties["availability_zone"] = vm["availability_zone"]
                resources[vmk]["properties"] = properties

                if len(vm["diversity_groups"]) > 0:
                    for divk, level in vm["diversity_groups"]:
                        div_id = divk + ":" + level
                        if div_id not in diversity_groups.keys():
                            diversity_groups[div_id] = []
                        diversity_groups[div_id].append(vmk)

                if len(vm["exclusivity_groups"]) > 0:
                    for exk, level_name in vm["exclusivity_groups"]:
                        ex_id = exk + ":" + level_name
                        if ex_id not in exclusivity_groups.keys():
                            exclusivity_groups[ex_id] = []
                        exclusivity_groups[ex_id].append(vmk)

                if vmk == _app["orchestration_id"]:
                    _app_topology.candidate_list_map[vmk] = _app["locations"]
                elif vmk in _app["exclusions"]:
                    _app_topology.planned_vm_map[vmk] = vm["host"]
                _app_topology.old_vm_map[vmk] = (vm["host"], \
                                                 float(vm["cpus"]), float(vm["mem"]), float(vm["local_volume"]))
 
        if "VGroups" in old_app.keys():
            for gk, affinity in old_app["VGroups"].iteritems():
                resources[gk] = {}
                resources[gk]["name"] = affinity["name"] 
                #resources[gk]["type"] = "ATT::CloudQoS::ResourceGroup"
                resources[gk]["type"] = "ATT::Valet::GroupAssignment"
                properties = {}
                properties["relationship"] = "affinity"
                properties["level"] = affinity["level"]
                properties["resources"] = []
                for r in affinity["subvgroup_list"]:
                    properties["resources"].append(r)
                resources[gk]["properties"] = properties

                if len(affinity["diversity_groups"]) > 0:
                    for divk, level in affinity["diversity_groups"]:
                        div_id = divk + ":" + level
                        if div_id not in diversity_groups.keys():
                            diversity_groups[div_id] = []
                        diversity_groups[div_id].append(gk)

                if len(affinity["exclusivity_groups"]) > 0:
                    for exk, level_name in affinity["exclusivity_groups"]:
                        ex_id = exk + ":" + level_name
                        if ex_id not in exclusivity_groups.keys():
                            exclusivity_groups[ex_id] = []
                        exclusivity_groups[ex_id].append(gk)
 
        # NOTE: skip pipes in this version

        for div_id, resource_list in diversity_groups.iteritems():
            divk_level = div_id.split(":")
            resources[divk_level[0]] = {}
            #resources[divk_level[0]]["type"] = "ATT::CloudQoS::ResourceGroup"
            resources[divk_level[0]]["type"] = "ATT::Valet::GroupAssignment"
            properties = {}
            properties["relationship"] = "diversity"
            properties["level"] = divk_level[1]
            properties["resources"] = resource_list
            resources[divk_level[0]]["properties"] = properties

        for ex_id, resource_list in exclusivity_groups.iteritems():
            exk_level_name = ex_id.split(":")
            resources[exk_level_name[0]] = {}
            resources[exk_level_name[0]]["name"] = exk_level_name[2]
            #resources[exk_level_name[0]]["type"] = "ATT::CloudQoS::ResourceGroup"
            resources[exk_level_name[0]]["type"] = "ATT::Valet::GroupAssignment"
            properties = {}
            properties["relationship"] = "exclusivity"
            properties["level"] = exk_level_name[1]
            properties["resources"] = resource_list
            resources[exk_level_name[0]]["properties"] = properties

        re_app["resources"] = resources

        return re_app       

