#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
#
# Functions 
# - Parse given applications
# - Compute weights of resource requirements against available resources
#
#################################################################################################################


import json
from app_topology_parser import Parser


class AppTopology:

    def __init__(self, _resource):
        self.vgroups = {}
        self.vms = {}
        self.volumes = {}

        self.resource = _resource
        self.parser = Parser(self.resource)

        self.optimization_priority = None

        self.status = "success"

    # Parse and set each app
    def set_app_topology(self, _app_graph):
        (vgroups, vms, volumes) = self.parser.set_topology(_app_graph)

        if len(vgroups) == 0 and len(vms) == 0 and len(volumes) == 0:
            self.status = self.parser.status
            return (None, None, {}, {}, {})
    
        for vgk in vgroups.keys():
            vgroup = vgroups[vgk]
            self.vgroups[vgroup.uuid] = vgroup 
        for vmk in vms.keys():
            vm = vms[vmk]
            self.vms[vm.uuid] = vm 
        for volk in volumes.keys():
            vol = volumes[volk]
            self.volumes[vol.uuid] = vol

        return (self.parser.stack_id, self.parser.application_name, vgroups, vms, volumes)

    def set_optimization_priority(self):
        app_nw_bandwidth_weight = -1
        if self.resource.nw_bandwidth_avail > 0:
            app_nw_bandwidth_weight = float(self.parser.total_nw_bandwidth) / \
                                      float(self.resource.nw_bandwidth_avail)
        else:
            app_nw_bandwidth_weight = 1.0

        app_CPU_weight = -1
        if self.resource.CPU_avail > 0:
            app_CPU_weight = float(self.parser.total_CPU) / float(self.resource.CPU_avail)
        else:
            app_CPU_weight = 1.0

        app_mem_weight = -1
        if self.resource.mem_avail > 0:
            app_mem_weight = float(self.parser.total_mem) / float(self.resource.mem_avail)
        else:
            app_mem_weight = 1.0

        app_local_vol_weight = -1
        if self.resource.local_disk_avail > 0:
            app_local_vol_weight = float(self.parser.total_local_vol) / float(self.resource.local_disk_avail)
        else:
            app_local_vol_weight = 1.0

        total_vol_list = []
        for vol_class in self.parser.total_vols.keys():
            if self.parser.total_vols[vol_class] > 0:
                total_vol_list.append(self.parser.total_vols[vol_class])

        app_vol_weight = -1
        if self.resource.disk_avail > 0:
            app_vol_weight = float(sum(total_vol_list)) / float(self.resource.disk_avail)
        else:
            app_vol_weight = 1.0

        opt = [("bw", app_nw_bandwidth_weight), \
               ("cpu", app_CPU_weight), \
               ("mem", app_mem_weight), \
               ("lvol", app_local_vol_weight), \
               ("vol", app_vol_weight)]

        self.optimization_priority = sorted(opt, key=lambda resource: resource[1], reverse=True)


