#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
#################################################################################################################


# Physical hierarchical layers
# 'cluster' can be used as zone or power domain
LEVELS = ["host", "rack", "cluster"]


# Affinity or Exclusive group
class VGroup:

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.vgroup_type = "AFF"       # affinity (AFF) or exclusivity (EX)
        self.level = None              # host, rack, or cluster

        self.survgroup = None          # where this vgroup belong to 
        self.subvgroup_list = []       # child vgroups

        self.vgroup_list = []          # a list of links to VMs or Volumes

        self.diversity_groups = {}     # cumulative diversity groups over this level. key=name, value=level
        self.availability_zones = {}
        self.host_aggregates = {}      # cumulative aggregates
        self.integrity_zones = {}      # cumulative security zones

        self.vCPUs = 0
        self.mem = 0                   # MB
        self.local_volume_size = 0     # GB
        self.volume_sizes = {}         # key = volume_class_name, value = size
        self.nw_bandwidth = 0          # Mbps
        self.io_bandwidth = 0          # Mbps

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1
        self.volume_weight = -1        # averge of all storage classes
        self.bandwidth_weight = -1

        self.host = None

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup == None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        subvgroup_list = []
        for vg in self.subvgroup_list:
            subvgroup_list.append(vg.uuid)

        link_list = []
        for l in self.vgroup_list:
            link_list.append(l.get_json_info())

        availability_zones = []
        for azk in self.availability_zones.keys():
            availability_zones.append(azk)

        host_aggregates = []
        for hak in self.host_aggregates.keys():
            host_aggregates.append(hak)

        integrity_zones = []
        for ik in self.integrity_zones.keys():
            integrity_zones.append(ik)

        return {'name':self.name, \
                'status':self.status, \
                'vgroup_type':self.vgroup_type, \
                'level':self.level, \
                'survgroup':survgroup_id, \
                'subvgroup_list':subvgroup_list, \
                'link_list':link_list, \
                'diversity_groups':self.diversity_groups, \
                'availability_zones':availability_zones, \
                'host_aggregates':host_aggregates, \
                'integrity_zones':integrity_zones, \
                'cpus':self.vCPUs, \
                'mem':self.mem, \
                'local_volume':self.local_volume_size, \
                'volumes':self.volume_sizes, \
                'nw_bandwidth':self.nw_bandwidth, \
                'io_bandwidth':self.io_bandwidth, \
                'cpu_weight':self.vCPU_weight, \
                'mem_weight':self.mem_weight, \
                'local_volume_weight':self.local_volume_weight, \
                'volume_weight':self.volume_weight, \
                'bandwidth_weight':self.bandwidth_weight, \
                'host':self.host}


class VM:

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.survgroup = None          # VGroup where this vm belongs to

        self.volume_list = []          # a list of links to Volumes
        self.vm_list = []              # a list of links to VMs

        self.diversity_groups = {}
        self.availability_zone = None
        self.host_aggregates = {}
        self.integrity_zones = {}

        self.vCPUs = 0
        self.mem = 0                  # MB
        self.local_volume_size = 0    # GB
        self.nw_bandwidth = 0
        self.io_bandwidth = 0

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1
        self.bandwidth_weight = -1

        self.host = None              # where this vm is placed

    def set_vm_properties(self, _flavor_name, _resource):
        flavor = _resource.get_flavor(_flavor_name)

        if flavor == None:
            return False
        else:
            self.vCPUs = flavor.vCPUs
            self.mem = flavor.mem_cap
            self.local_volume_size = flavor.disk_cap

        if len(flavor.extra_specs) > 0:
            logical_group_list = _resource.get_matched_logical_groups(flavor)

            for lg in logical_group_list:
                if lg.group_type == "AGGR":
                    self.host_aggregates[lg.name] = flavor.extra_specs

        return True

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup == None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        vm_list = []
        for vml in self.vm_list:
            vm_list.append(vml.get_json_info())

        vol_list = []
        for voll in self.volume_list:
            vol_list.append(voll.get_json_info())

        availability_zone = None
        if self.availability_zone == None:
            availability_zone = "none"
        else:
            availability_zone = self.availability_zone

        host_aggregates = []
        for hak in self.host_aggregates.keys():
            host_aggregates.append(hak)

        integrity_zones = []
        for ik in self.integrity_zones.keys():
            integrity_zones.append(ik)

        return {'name':self.name, \
                'status':self.status, \
                'survgroup':survgroup_id, \
                'vm_list':vm_list, \
                'volume_list':vol_list, \
                'diversity_groups':self.diversity_groups, \
                'availability_zones':availability_zone, \
                'host_aggregates':host_aggregates, \
                'integrity_zones':integrity_zones, \
                'cpus':self.vCPUs, \
                'mem':self.mem, \
                'local_volume':self.local_volume_size, \
                'nw_bandwidth':self.nw_bandwidth, \
                'io_bandwidth':self.io_bandwidth, \
                'cpu_weight':self.vCPU_weight, \
                'mem_weight':self.mem_weight, \
                'local_volume_weight':self.local_volume_weight, \
                'bandwidth_weight':self.bandwidth_weight, \
                'host':self.host}


class Volume:

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.volume_class = None

        self.survgroup = None         # where this vm belongs to

        self.vm_list = []             # a list of links to VMs

        self.diversity_groups = {}
        #self.availability_zone = None
        #self.host_aggregates = {}
        #self.integrity_zones = {}

        self.volume_size = 0          # GB
        self.io_bandwidth = 0       

        self.volume_weight = -1 
        self.bandwidth_weight = -1

        self.storage_host = None

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup == None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        volume_class = None
        if self.volume_class == None:
            volume_class = "none"
        else:
            volume_class = self.volume_class

        vm_list = []
        for vml in self.vm_list:
            vm_list.append(vml.get_json_info())

        return {'name':self.name, \
                'status':self.status, \
                'class':volume_class, \
                'survgroup':survgroup_id, \
                'vm_list':vm_list, \
                'diversity_groups':self.diversity_groups, \
                'volume':self.volume_size, \
                'io_bandwidth':self.io_bandwidth, \
                'volume_weight':self.volume_weight, \
                'bandwidth_weight':self.bandwidth_weight, \
                'host':self.storage_host}


class VGroupLink:

    def __init__(self, _n):
        self.node = _n                # target VM or Volume
        self.nw_bandwidth = 0
        self.io_bandwidth = 0

    def get_json_info(self):
        return {'target':self.node.uuid, \
                'nw_bandwidth':self.nw_bandwidth, \
                'io_bandwidth':self.io_bandwidth}


class VMLink:

    def __init__(self, _n):
        self.node = _n                # target VM
        self.nw_bandwidth = 0         # Mbps

    def get_json_info(self):
        return {'target':self.node.uuid, \
                'nw_bandwidth':self.nw_bandwidth}


class VolumeLink:

    def __init__(self, _n):
        self.node = _n                # target Volume
        self.io_bandwidth = 0         # Mbps

    def get_json_info(self):
        return {'target':self.node.uuid, \
                'io_bandwidth':self.io_bandwidth}



