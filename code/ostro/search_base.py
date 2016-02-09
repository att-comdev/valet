#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
#################################################################################################################


import sys

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, Volume, LEVELS


class Resource:

    def __init__(self):
        self.host_name = None               # key of this data structure
        self.host_memberships = {}          # key=((level:)name), value=type
        self.host_avail_vCPUs = 0
        self.host_avail_mem = 0
        self.host_avail_local_disk = 0
        self.host_avail_switches = {}       # all mapped switches to host 
        self.host_avail_storages = {}       # all mapped storage_resources to host
        self.host_num_of_placed_vms = 0

        self.rack_name = None               # where this host is located
        self.rack_memberships = {}          # key=((level:)name), value=type
        self.rack_avail_vCPUs = 0
        self.rack_avail_mem = 0
        self.rack_avail_local_disk = 0 
        self.rack_avail_switches = {}       # all mapped switches to rack
        self.rack_avail_storages = {}       # all mapped storage_resources to rack
        self.rack_num_of_placed_vms = 0

        self.cluster_name = None            # where this host and rack are located
        self.cluster_memberships = {}       # key=((level:)name), value=type
        self.cluster_avail_vCPUs = 0
        self.cluster_avail_mem = 0
        self.cluster_avail_local_disk = 0 
        self.cluster_avail_switches = {}    # all mapped switches to cluster
        self.cluster_avail_storages = {}    # all mapped storage_resources to cluster
        self.cluster_num_of_placed_vms = 0

        self.storage = None                 # selected best storage for volume among host_avail_storages

        self.sort_base = 0                  # order to place

    def get_common_placement(self, _resource):
        level = None

        if self.cluster_name != _resource.cluster_name:
            level = "cluster"
        else:
            if self.rack_name != _resource.rack_name:
                level = "rack"
            else:
                if self.host_name != _resource.host_name:
                    level = "host"
                else:
                    level = "ANY"

        return level

    def get_resource_name(self, _level):
        name = "unknown"

        if _level == "cluster":
            name = self.cluster_name
        elif _level == "rack":
            name = self.rack_name
        elif _level == "host":
            name = self.host_name

        return name

    def get_memberships(self, _level):
        memberships = None

        if _level == "cluster":
            memberships = self.cluster_memberships
        elif _level == "rack":
            memberships = self.rack_memberships
        elif _level == "host":
            memberships = self.host_memberships

        return memberships

    def get_num_of_placed_vms(self, _level):
        num_of_vms = 0

        if _level == "cluster":
            num_of_vms = self.cluster_num_of_placed_vms
        elif _level == "rack":
            num_of_vms = self.rack_num_of_placed_vms
        elif _level == "host":
            num_of_vms = self.host_num_of_placed_vms

        return num_of_vms

    def get_avail_resources(self, _level):
        avail_vCPUs = 0
        avail_mem = 0
        avail_local_disk = 0

        if _level == "cluster":
            avail_vCPUs = self.cluster_avail_vCPUs
            avail_mem = self.cluster_avail_mem
            avail_local_disk = self.cluster_avail_local_disk
        elif _level == "rack":
            avail_vCPUs = self.rack_avail_vCPUs
            avail_mem = self.rack_avail_mem
            avail_local_disk = self.rack_avail_local_disk
        elif _level == "host":
            avail_vCPUs = self.host_avail_vCPUs
            avail_mem = self.host_avail_mem
            avail_local_disk = self.host_avail_local_disk

        return (avail_vCPUs, avail_mem, avail_local_disk)

    def get_avail_storages(self, _level):
        avail_storages = None

        if _level == "cluster":
            avail_storages = self.cluster_avail_storages
        elif _level == "rack":
            avail_storages = self.rack_avail_storages
        elif _level == "host":
            avail_storages = self.host_avail_storages

        return avail_storages

    def get_avail_switches(self, _level):
        avail_switches = None

        if _level == "cluster":
            avail_switches = self.cluster_avail_switches
        elif _level == "rack":
            avail_switches = self.rack_avail_switches
        elif _level == "host":
            avail_switches = self.host_avail_switches

        return avail_switches


# where Volume will be placed
class StorageResource:

    def __init__(self):
        self.storage_name = None 
        self.storage_class = None
        self.storage_avail_disk = 0

        self.sort_base = 0


class SwitchResource:

    def __init__(self):
        self.switch_name = None
        self.switch_type = None
        self.avail_bandwidths = []          # out-bound bandwidths

        self.sort_base = 0


class Node:

    def __init__(self):
        self.node = None                    # VM, Volume, or VGroup

        self.sort_base = -1

    def get_all_links(self):
        link_list = []

        if isinstance(self.node, VM):
            for vml in self.node.vm_list:
                link_list.append(vml)
            for voll in self.node.volume_list:
                link_list.append(voll)
        elif isinstance(self.node, Volume):
            for vml in self.node.vm_list:   # vml is VolumeLink
                link_list.append(vml)
        elif isinstance(self.node, VGroup):
            for vgl in self.node.vgroup_list:
                link_list.append(vgl)

        return link_list

    def get_bandwidth_of_link(self, _link):
        bandwidth = 0

        if isinstance(self.node, VGroup) or isinstance(self.node, VM):
            if isinstance(_link.node, VM):
                bandwidth = _link.nw_bandwidth
            elif isinstance(_link.node, Volume):
                bandwidth = _link.io_bandwidth
        else:
            bandwidth = _link.io_bandwidth

        return bandwidth

    def get_common_diversity(self, _diversity_groups):
        common_level = "ANY"

        for dk in self.node.diversity_groups.keys():
            if dk in _diversity_groups.keys():
                level = self.node.diversity_groups[dk]
                if common_level != "ANY":
                    if LEVELS.index(level) > LEVELS.index(common_level):
                        common_level = level
                else:
                    common_level = level

        return common_level

    def get_exclusivity_id(self):
        exc_id = None

        if isinstance(self.node, VGroup) and self.node.vgroup_type == "EX":
            exc_id = self.node.level + ":" + self.node.name

        return exc_id

    def get_parent_exclusivity_id(self):
        exc_id = None

        if self.node.survgroup != None:
            n = Node()
            n.node = self.node.survgroup
            exc_id = n.get_exclusivity_id()
            if exc_id == None:
                exc_id = n.get_parent_exclusivity_id()

        return exc_id


def compute_reservation(_level, _placement_level, _bandwidth):
    reservation = 0

    if _placement_level != "ANY":
        diff = LEVELS.index(_placement_level) - LEVELS.index(_level) + 1
        if diff > 0:
            reservation = _bandwidth * diff * 2

    return reservation    





