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
        self.app_id = _app_id
        self.app_name = _app_name

        self.request_type = "create"   # create, update, or delete

        self.timestamp_scheduled = 0

        self.vgroups = {}
        self.vms = {}
        self.volumes = {}

        self.status = 'requested'  # Moved to "scheduled" (and then "placed")

    #def set_app_components(self, _vgroups, _vms, _vols):
        #for v_uuid, vm in _vms.iteritems():
            #self._set_vm(vm)
        #for v_uuid, vol in _vols.iteritems():
            #self._set_volume(vol)
        #for v_uuid, vg in _vgroups.iteritems():
            #self._set_vgroup(vg)

    #def _set_vm(self, _vm):
        #self.vms[_vm.uuid] = _vm
        #self.vms[_vm.uuid].status = "requested"

    #def _set_volume(self, _vol):
        #self.volumes[_vol.uuid] = _vol
        #self.volumes[_vol.uuid].status = "requested"

    #def _set_vgroup(self, _vg):
        #self.vgroups[_vg.uuid] = {}
        #self.vgroups[_vg.uuid]["name"] = _vg.name
        ##self.vgroups[_vg.uuid]["status"] = "requested"

    def add_vm(self, _vm, _host_name):
        self.vms[_vm.uuid] = _vm
        self.vms[_vm.uuid].status = "scheduled"
        self.vms[_vm.uuid].host = _host_name

    def add_volume(self, _vol, _host_name):
        self.vms[_vol.uuid] = _vm
        self.vms[_vol.uuid].status = "scheduled"
        self.vms[_vol.uuid].storage_host = _host_name

    def add_vgroup(self, _vg, _host_name):
        self.vms[_vg.uuid] = _vg
        self.vms[_vg.uuid].status = "scheduled"
        self.vms[_vg.uuid].host = _host_name

    def get_json_info(self):
        vms = {}
        for vmk, vm in self.vms.iteritems():
            vms[vmk] = vm.get_json_info()

        vols = {}
        for volk, vol in self.volumes.iteritems():
            vols[volk] = vol.get_json_info()

        vgs = {}
        for vgk, vg in self.vgroups.iteritems():
            vgs[vgk] = vg.get_json_info()

        return {'request_type':self.request_type, \
                'timestamp':self.timestamp_scheduled, \
                'id':self.app_id, \
                'name':self.app_name, \
                'VMs':vms, \
                'Volumes':vols, \
                'VGroups':vgs}




