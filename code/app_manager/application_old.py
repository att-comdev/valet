#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung, Mengsong Zou
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
#################################################################################################################


import sys
import json

from app_topology_base import VM, Volume 


class App:

    def __init__(self, _app_id, _app_name):
        self.timestamp_scheduled = 0

        self.app_id = _app_id
        self.app_name = _app_name

        self.vgroups = {}
        self.vms = {}
        self.volumes = {}

        self.status = 'requested'  # Moved to "scheduled" and then "placed", finally inserted to db

    def set_app_components(self, _vgroups, _vms, _vols):
        for v_uuid in _vms.keys():
            vm = _vms[v_uuid]
            self._set_vm(vm)
        for v_uuid in _vols.keys():
	    vol = _vols[v_uuid]
            self._set_volume(vol)
        for v_uuid in _vgroups.keys():
            vg = _vgroups[v_uuid]
            self._set_vgroup(vg)

    def _set_vm(self, _vm):
        self.vms[_vm.uuid] = {}
        self.vms[_vm.uuid]["name"] = _vm.name
        self.vms[_vm.uuid]["status"] = "requested"
        self.vms[_vm.uuid]["uuid"] = "none"

        if _vm.survgroup != None:
            self.vms[_vm.uuid]["parent_group"] = _vm.survgroup.uuid
        else:
            self.vms[_vm.uuid]["parent_group"] = "none"
        #if _vm.availability_zone != None:
            #self.vms[_vm.uuid]["availability_zone"] = _vm.availability_zone
        #else:
            #self.vms[_vm.uuid]["availability_zone"] = "none"
        #self.vms[_vm.uuid]["host_aggregate"] = _vm.host_aggregate
        self.vms[_vm.uuid]["diversity_groups"] = {}
        for dgk in _vm.diversity_groups.keys():
            self.vms[_vm.uuid]["diversity_groups"][dgk] = _vm.diversity_groups[dgk]

        self.vms[_vm.uuid]["cpu"] = _vm.vCPUs
        self.vms[_vm.uuid]["mem"] = _vm.mem
        self.vms[_vm.uuid]["lvol"] = _vm.local_volume_size
        self.vms[_vm.uuid]["nw"] = _vm.nw_bandwidth
        self.vms[_vm.uuid]["io"] = _vm.io_bandwidth

        self.vms[_vm.uuid]["vol_links"] = {}
        for vol_link in _vm.volume_list:
            self.vms[_vm.uuid]["vol_links"][vol_link.node.uuid] = vol_link.io_bandwidth 
        self.vms[_vm.uuid]["vm_links"] = {}
        for vm_link in _vm.vm_list:
            self.vms[_vm.uuid]["vm_links"][vm_link.node.uuid] = vm_link.nw_bandwidth
 
        self.vms[_vm.uuid]["host"] = "none"

    def _set_volume(self, _vol):
        self.volumes[_vol.uuid] = {}
        self.volumes[_vol.uuid]["name"] = _vol.name
        self.volumes[_vol.uuid]["status"] = "requested"
        self.volumes[_vol.uuid]["uuid"] = "none"

        if _vol.survgroup != None:
            self.volumes[_vol.uuid]["parent_group"] = _vol.survgroup.uuid
        else:
            self.volumes[_vol.uuid]["parent_group"] = "none"
        #if _vol.availability_zone != None:
            #self.volumes[_vol.uuid]["availability_zone"] = _vol.availability_zone
        #else:
            #self.volumes[_vol.uuid]["availability_zone"] = "none"
        #self.volumes[_vol.uuid]["host_aggregate"] = _vol.host_aggregate
        self.volumes[_vol.uuid]["diversity_groups"] = {}
        for dgk in _vol.diversity_groups.keys():
            self.volumes[_vol.uuid]["diversity_groups"][dgk] = _vol.diversity_groups[dgk]

        if _vol.volume_class != None:
            self.volumes[_vol.uuid]["class"] = _vol.volume_class
        else:
            self.volumes[_vol.uuid]["class"] = "none"

        self.volumes[_vol.uuid]["size"] = _vol.volume_size
        self.volumes[_vol.uuid]["io"] = _vol.io_bandwidth

        self.volumes[_vol.uuid]["vm_links"] = {}
        for vm_link in _vol.vm_list:
            self.volumes[_vol.uuid]["vm_links"][vm_link.node.uuid] = vm_link.io_bandwidth 

        self.volumes[_vol.uuid]["host"] = "none"

    def _set_vgroup(self, _vg):
        self.vgroups[_vg.uuid] = {}
        self.vgroups[_vg.uuid]["name"] = _vg.name
        #self.vgroups[_vg.uuid]["status"] = "requested"

        if _vg.survgroup != None:
            self.vgroups[_vg.uuid]["parent_group"] = _vg.survgroup.uuid
        else:
            self.vgroups[_vg.uuid]["parent_group"] = "none"
        #if _vg.availability_zone != None:
            #self.vgroups[_vg.uuid]["availability_zone"] = _vg.availability_zone
        #else:
            #self.vgroups[_vg.uuid]["availability_zone"] = "none"
        #self.vgroups[_vg.uuid]["host_aggregate"] = _vg.host_aggregate
        self.vgroups[_vg.uuid]["diversity_groups"] = {}
        for dgk in _vg.diversity_groups.keys():
            self.vgroups[_vg.uuid]["diversity_groups"][dgk] = _vg.diversity_groups[dgk]

        self.vgroups[_vg.uuid]["level"] = _vg.level

        self.vgroups[_vg.uuid]["cpu"] = _vg.vCPUs
        self.vgroups[_vg.uuid]["mem"] = _vg.mem
        self.vgroups[_vg.uuid]["lvol"] = _vg.local_volume_size
        self.vgroups[_vg.uuid]["nw"] = _vg.nw_bandwidth
        self.vgroups[_vg.uuid]["io"] = _vg.io_bandwidth
        self.vgroups[_vg.uuid]["vol"] = {}
        for ck in _vg.volume_sizes.keys():
            self.vgroups[_vg.uuid]["vol"][ck] = _vg.volume_sizes[ck]

        self.vgroups[_vg.uuid]["vol_links"] = {}
        self.vgroups[_vg.uuid]["vm_links"] = {}
        for v_link in _vg.vgroup_list:
            if isinstance(v_link.node, Volume):
                self.vgroups[_vg.uuid]["vol_links"][v_link.node.uuid] = v_link.io_bandwidth
            elif isinstance(v_link.node, VM): 
                self.vgroups[_vg.uuid]["vm_links"][v_link.node.uuid] = v_link.nw_bandwidth

        self.vgroups[_vg.uuid]["subvgroups"] = []
        self.vgroups[_vg.uuid]["vms"] = []
        self.vgroups[_vg.uuid]["volumes"] = []
        for svg in _vg.subvgroup_list:
            if isinstance(svg, VM):
                self.vgroups[_vg.uuid]["vms"].append(svg.uuid)
                self._set_vm(svg)
            elif isinstance(svg, Volume):
                self.vgroups[_vg.uuid]["volumes"].append(svg.uuid)
                self._set_volume(svg)
            else:
                self.vgroups[_vg.uuid]["subvgroups"].append(svg.uuid)
                self._set_vgroup(svg)

    # Delete the existing placement 
    #def del_placement(self):
        #for vm, vm_info in self.vms.iteritems():
            #vm_info['host'] = "none"

    def get_info_dict(self):
        return {'VMs':self.vms, \
                'Volumes':self.volumes, \
                'VGroups':self.vgroups, \
                'Name':self.app_name, \
                'ID':self.app_id, \
                'Status':self.status}

    def print_app_info(self):
        print "[TRACE] application = ", self.app_name
        print "Status: ", self.status 
        print "VGroups: ",json.dumps(self.vgroups, indent=2)
        print "VMs: ",json.dumps(self.vms, indent=2)
        print "Volumes: ",json.dumps(self.volumes, indent=2)



