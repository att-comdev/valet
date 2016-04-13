#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Parse given applications
# - Compute weights of resource requirements against available resources
#
#################################################################################################################


import json
from app_topology_parser import Parser


class AppTopology:

    def __init__(self, _resource, _logger):
        self.vgroups = {}
        self.vms = {}
        self.volumes = {}

        self.resource = _resource
        self.logger = _logger

        self.parser = Parser(self.resource, self.logger)

        self.optimization_priority = None

        self.status = "success"

    # Parse and set each app
    def set_app_topology(self, _app_graph):
        (vgroups, vms, volumes) = self.parser.set_topology(_app_graph)

        if self.parser.action == "ping":
            return (self.parser.stack_id, self.parser.application_name, self.parser.action)

        if len(vgroups) == 0 and len(vms) == 0 and len(volumes) == 0:
            self.status = self.parser.status
            return None

        # Cumulate virtual resources    
        for vgk, vgroup in vgroups.iteritems():
            self.vgroups[vgroup.uuid] = vgroup 
        for vmk, vm in vms.iteritems():
            self.vms[vm.uuid] = vm 
        for volk, vol in volumes.iteritems():
            self.volumes[vol.uuid] = vol

        return (self.parser.stack_id, self.parser.application_name, self.parser.action)

    def set_optimization_priority(self):
        if len(self.vgroups) == 0 and len(self.vms) == 0 and len(self.volumes) == 0:
            return

        app_nw_bandwidth_weight = -1
        if self.resource.nw_bandwidth_avail > 0:
            app_nw_bandwidth_weight = float(self.parser.total_nw_bandwidth) / \
                                      float(self.resource.nw_bandwidth_avail)
        else:
            if self.parser.total_nw_bandwidth > 0:
                app_nw_bandwidth_weight = 1.0
            else:
                app_nw_bandwidth_weight = 0.0

        app_CPU_weight = -1
        if self.resource.CPU_avail > 0:
            app_CPU_weight = float(self.parser.total_CPU) / float(self.resource.CPU_avail)
        else:
            if self.parser.total_CPU > 0:
                app_CPU_weight = 1.0
            else:
                app_CPU_weight = 0.0

        app_mem_weight = -1
        if self.resource.mem_avail > 0:
            app_mem_weight = float(self.parser.total_mem) / float(self.resource.mem_avail)
        else:
            if self.parser.total_mem > 0:
                app_mem_weight = 1.0
            else:
                app_mem_weight = 0.0

        app_local_vol_weight = -1
        if self.resource.local_disk_avail > 0:
            app_local_vol_weight = float(self.parser.total_local_vol) / float(self.resource.local_disk_avail)
        else:
            if self.parser.total_local_vol > 0:
                app_local_vol_weight = 1.0
            else:
                app_local_vol_weight = 0.0

        total_vol_list = []
        for vol_class in self.parser.total_vols.keys():
            total_vol_list.append(self.parser.total_vols[vol_class])

        app_vol_weight = -1
        if self.resource.disk_avail > 0:
            app_vol_weight = float(sum(total_vol_list)) / float(self.resource.disk_avail)
        else:
            if sum(total_vol_list) > 0:
                app_vol_weight = 1.0
            else:
                app_vol_weight = 0.0

        opt = [("bw", app_nw_bandwidth_weight), \
               ("cpu", app_CPU_weight), \
               ("mem", app_mem_weight), \
               ("lvol", app_local_vol_weight), \
               ("vol", app_vol_weight)]

        self.optimization_priority = sorted(opt, key=lambda resource: resource[1], reverse=True)


