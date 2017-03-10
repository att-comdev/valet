#!/bin/python


class App(object):

    def __init__(self, _app_id, _app_name, _action):
        self.app_id = _app_id
        self.app_name = _app_name

        self.request_type = _action   # create, replan, migrate, or ping

        self.timestamp_scheduled = 0

        self.vgroups = {}
        self.vms = {}

        self.status = 'requested'  # Moved to "scheduled" (and then "placed")

    def add_vm(self, _vm, _host_name, _status):
        self.vms[_vm.uuid] = _vm
        self.vms[_vm.uuid].status = _status
        self.vms[_vm.uuid].host = _host_name

    def add_vgroup(self, _vg, _host_name):
        self.vgroups[_vg.uuid] = _vg
        self.vgroups[_vg.uuid].status = "scheduled"
        self.vgroups[_vg.uuid].host = _host_name

    def get_json_info(self):
        vms = {}
        for vmk, vm in self.vms.iteritems():
            vms[vmk] = vm.get_json_info()

        vgs = {}
        for vgk, vg in self.vgroups.iteritems():
            vgs[vgk] = vg.get_json_info()

        return {'action': self.request_type,
                'timestamp': self.timestamp_scheduled,
                'stack_id': self.app_id,
                'name': self.app_name,
                'VMs': vms,
                'VGroups': vgs}

    def log_in_info(self):
        return {'action': self.request_type,
                'timestamp': self.timestamp_scheduled,
                'stack_id': self.app_id,
                'name': self.app_name}
