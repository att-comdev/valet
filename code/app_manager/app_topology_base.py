#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015
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

        self.vgroup_type = "AFF"       # affinity (AFF) or exclusivity (EX)
        self.level = None              # host, rack, or cluster

        self.survgroup = None          # where this vgroup belong to 
        self.subvgroup_list = []       # child vgroups

        self.vgroup_list = []          # a list of links to VMs or Volumes

        self.diversity_groups = {}     # cumulative diversity groups over this level. key=name, value=level
        #self.availability_zones = []
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


class VM:

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.survgroup = None          # VGroup where this vm belongs to

        self.volume_list = []          # a list of links to Volumes
        self.vm_list = []              # a list of links to VMs

        self.diversity_groups = {}
        #self.availability_zone = None
        self.host_aggregates = {}
        self.integrity_zones = {}

        self.vCPUs = -1
        self.mem = -1                 # MB
        self.local_volume_size = -1   # GB
        self.nw_bandwidth = 0
        self.io_bandwidth = 0

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1
        self.bandwidth_weight = -1

        self.host = None              # where this vm is placed

    def set_vm_cap_properties(self, _flavor_name, _resource):
        flavor = _resource.get_flavor(_flavor_name)

        if flavor == None:
            return False
        else:
            self.vCPUs = flavor.vCPUs
            self.mem = flavor.mem_cap
            self.local_volume_size = flavor.disk_cap

        if len(flavor.extra_specs) > 0:
            logical_group_names = _resource.get_logical_groups_for_aggregate(flavor)

            for gk in logical_group_names:
                self.host_aggregates[gk] = flavor.extra_specs

        return True


class Volume:

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.volume_class = None

        self.survgroup = None         # where this vm belongs to

        self.vm_list = []             # a list of links to VMs

        self.diversity_groups = {}
        #self.availability_zone = None
        #self.host_aggregates = {}
        self.integrity_zones = {}

        self.volume_size = -1         # GB
        self.io_bandwidth = 0       

        self.volume_weight = -1 
        self.bandwidth_weight = -1

        self.storage_host = None


class VGroupLink:

    def __init__(self, _n):
        self.node = _n                # target VM or Volume
        self.nw_bandwidth = 0
        self.io_bandwidth = 0


class VMLink:

    def __init__(self, _n):
        self.node = _n                # target VM
        self.nw_bandwidth = -1        # Mbps


class VolumeLink:

    def __init__(self, _n):
        self.node = _n                # target Volume
        self.io_bandwidth = -1        # Mbps



