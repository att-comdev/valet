#!/bin/python


from valet.engine.optimizer.app_manager.app_topology_base import LEVELS


class Datacenter(object):
    ''' do not consider switch and storage resources at this version '''

    def __init__(self, _name):
        self.name = _name

        self.region_code_list = []

        self.status = "enabled"

        self.memberships = {}            # all available logical groups (e.g., aggregate) in the datacenter

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.resources = {}

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)

        self.last_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        child_list = []
        for ck in self.resources.keys():
            child_list.append(ck)

        return {'status': self.status,
                'name': self.name,
                'region_code_list': self.region_code_list,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'children': child_list,
                'vm_list': self.vm_list,
                'last_update': self.last_update}


class HostGroup(object):
    ''' do not consider switch and storage resources at this version '''

    def __init__(self, _id):
        self.name = _id
        self.host_type = "rack"          # rack or cluster(e.g., power domain, zone)

        self.status = "enabled"

        self.memberships = {}            # all available logical groups (e.g., aggregate) in this group

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.parent_resource = None      # e.g., datacenter
        self.child_resources = {}        # e.g., hosting servers

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)

        self.last_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

    def init_memberships(self):
        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if lg.group_type == "EX" or lg.group_type == "AFF" or lg.group_type == "DIV":
                level = lg.name.split(":")[0]
                if LEVELS.index(level) < LEVELS.index(self.host_type) or self.name not in lg.vms_per_host.keys():
                    del self.memberships[lgk]
            else:
                del self.memberships[lgk]

    def remove_membership(self, _lg):
        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or _lg.group_type == "DIV":
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        if self.status == "enabled":
            return True
        else:
            return False

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        child_list = []
        for ck in self.child_resources.keys():
            child_list.append(ck)

        return {'status': self.status,
                'host_type': self.host_type,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'parent': self.parent_resource.name,
                'children': child_list,
                'vm_list': self.vm_list,
                'last_update': self.last_update}


class Host(object):
    ''' do not consider switch and storage resources at this version '''

    def __init__(self, _name):
        self.name = _name

        self.tag = []                    # mark if this is synch'ed by multiple sources
        self.status = "enabled"
        self.state = "up"

        self.memberships = {}            # logical group (e.g., aggregate) this hosting server is involved in

        self.vCPUs = 0
        self.original_vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.original_mem_cap = 0
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.original_local_disk_cap = 0
        self.avail_local_disk_cap = 0

        self.vCPUs_used = 0
        self.free_mem_mb = 0
        self.free_disk_gb = 0
        self.disk_available_least = 0

        self.host_group = None           # e.g., rack

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)

        self.last_update = 0

    def clean_memberships(self):
        cleaned = False

        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if self.name not in lg.vms_per_host.keys():
                del self.memberships[lgk]
                cleaned = True

        return cleaned

    def remove_membership(self, _lg):
        cleaned = False

        if _lg.group_type == "EX" or _lg.group_type == "AFF" or _lg.group_type == "DIV":
            if self.name not in _lg.vms_per_host.keys():
                del self.memberships[_lg.name]
                cleaned = True

        return cleaned

    def check_availability(self):
        if self.status == "enabled" and self.state == "up" and ("nova" in self.tag) and ("infra" in self.tag):
            return True
        else:
            return False

    def get_uuid(self, _h_uuid):
        uuid = None

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                uuid = vm_id[2]
                break

        return uuid

    def exist_vm_by_h_uuid(self, _h_uuid):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                exist = True
                break

        return exist

    def exist_vm_by_uuid(self, _uuid):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                exist = True
                break

        return exist

    def remove_vm_by_h_uuid(self, _h_uuid):
        success = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        return success

    def remove_vm_by_uuid(self, _uuid):
        success = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        return success

    def update_uuid(self, _h_uuid, _uuid):
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)

        return success

    def update_h_uuid(self, _h_uuid, _uuid):
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)

        return success

    def compute_avail_vCPUs(self, _overcommit_ratio, _standby_ratio):
        self.vCPUs = self.original_vCPUs * _overcommit_ratio * (1.0 - _standby_ratio)

        self.avail_vCPUs = self.vCPUs - self.vCPUs_used

    def compute_avail_mem(self, _overcommit_ratio, _standby_ratio):
        self.mem_cap = self.original_mem_cap * _overcommit_ratio * (1.0 - _standby_ratio)

        used_mem_mb = self.original_mem_cap - self.free_mem_mb

        self.avail_mem_cap = self.mem_cap - used_mem_mb

    def compute_avail_disk(self, _overcommit_ratio, _standby_ratio):
        self.local_disk_cap = self.original_local_disk_cap * _overcommit_ratio * (1.0 - _standby_ratio)

        free_disk_cap = self.free_disk_gb
        if self.disk_available_least > 0:
            free_disk_cap = min(self.free_disk_gb, self.disk_available_least)

        used_disk_cap = self.original_local_disk_cap - free_disk_cap

        self.avail_local_disk_cap = self.local_disk_cap - used_disk_cap

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        return {'tag': self.tag, 'status': self.status, 'state': self.state,
                'membership_list': membership_list,
                'vCPUs': self.vCPUs,
                'original_vCPUs': self.original_vCPUs,
                'avail_vCPUs': self.avail_vCPUs,
                'mem': self.mem_cap,
                'original_mem': self.original_mem_cap,
                'avail_mem': self.avail_mem_cap,
                'local_disk': self.local_disk_cap,
                'original_local_disk': self.original_local_disk_cap,
                'avail_local_disk': self.avail_local_disk_cap,
                'vCPUs_used': self.vCPUs_used,
                'free_mem_mb': self.free_mem_mb,
                'free_disk_gb': self.free_disk_gb,
                'disk_available_least': self.disk_available_least,
                'parent': self.host_group.name,
                'vm_list': self.vm_list,
                'last_update': self.last_update}


class LogicalGroup(object):

    def __init__(self, _name):
        self.name = _name
        self.group_type = "AGGR"         # AGGR, AZ, INTG, EX, DIV, or AFF

        self.status = "enabled"

        self.metadata = {}               # any metadata to be matched when placing nodes

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)

        self.vms_per_host = {}           # key = host_id, value = a list of placed vms

        self.last_update = 0

    def exist_vm_by_h_uuid(self, _h_uuid):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                exist = True
                break

        return exist

    def exist_vm_by_uuid(self, _uuid):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                exist = True
                break

        return exist

    def update_uuid(self, _h_uuid, _uuid, _host_id):
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[0] == _h_uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)
            if _host_id in self.vms_per_host.keys():
                self.vms_per_host[_host_id].append(vm_id)

        return success

    def update_h_uuid(self, _h_uuid, _uuid, _host_id):
        success = False

        vm_name = "none"
        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                vm_name = vm_id[1]
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[2] == _uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if success is True:
            vm_id = (_h_uuid, vm_name, _uuid)
            self.vm_list.append(vm_id)
            if _host_id in self.vms_per_host.keys():
                self.vms_per_host[_host_id].append(vm_id)

        return success

    def add_vm_by_h_uuid(self, _vm_id, _host_id):
        success = False

        if self.exist_vm_by_h_uuid(_vm_id[0]) is False:
            self.vm_list.append(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF" or self.group_type == "DIV":
                if _host_id not in self.vms_per_host.keys():
                    self.vms_per_host[_host_id] = []
            self.vms_per_host[_host_id].append(_vm_id)

            success = True

        return success

    def remove_vm_by_h_uuid(self, _h_uuid, _host_id):
        success = False

        for vm_id in self.vm_list:
            if vm_id[0] == _h_uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[0] == _h_uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if self.group_type == "EX" or self.group_type == "AFF" or self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def remove_vm_by_uuid(self, _uuid, _host_id):
        success = False

        for vm_id in self.vm_list:
            if vm_id[2] == _uuid:
                self.vm_list.remove(vm_id)
                success = True
                break

        if _host_id in self.vms_per_host.keys():
            for host_vm_id in self.vms_per_host[_host_id]:
                if host_vm_id[2] == _uuid:
                    self.vms_per_host[_host_id].remove(host_vm_id)
                    success = True
                    break

        if self.group_type == "EX" or self.group_type == "AFF" or self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def clean_none_vms(self, _host_id):
        success = False

        blen = len(self.vm_list)
        self.vm_list = [v for v in self.vm_list if v[2] != "none"]
        alen = len(self.vm_list)
        if alen != blen:
            success = True

        if _host_id in self.vms_per_host.keys():
            blen = len(self.vms_per_host[_host_id])
            self.vms_per_host[_host_id] = [v for v in self.vms_per_host[_host_id] if v[2] != "none"]
            alen = len(self.vm_list)
            if alen != blen:
                success = True

        if self.group_type == "EX" or self.group_type == "AFF" or self.group_type == "DIV":
            if (_host_id in self.vms_per_host.keys()) and len(self.vms_per_host[_host_id]) == 0:
                del self.vms_per_host[_host_id]

        return success

    def get_json_info(self):
        return {'status': self.status,
                'group_type': self.group_type,
                'metadata': self.metadata,
                'vm_list': self.vm_list,
                'vms_per_host': self.vms_per_host,
                'last_update': self.last_update}


class Flavor(object):

    def __init__(self, _name):
        self.name = _name
        self.flavor_id = None

        self.status = "enabled"

        self.vCPUs = 0
        self.mem_cap = 0        # MB
        self.disk_cap = 0       # including ephemeral (GB) and swap (MB)

        self.extra_specs = {}

        self.last_update = 0

    def get_json_info(self):
        return {'status': self.status,
                'flavor_id': self.flavor_id,
                'vCPUs': self.vCPUs,
                'mem': self.mem_cap,
                'disk': self.disk_cap,
                'extra_specs': self.extra_specs,
                'last_update': self.last_update}
