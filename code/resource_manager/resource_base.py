#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
#################################################################################################################


import sys

sys.path.insert(0, '../app_manager')
from app_topology_base import LEVELS


class Datacenter:

    def __init__(self, _name):
        self.name = _name

        self.status = "enabled"

        self.memberships = {}            # all available logical groups (e.g., aggregate) in the datacenter

        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB
        self.avail_local_disk_cap = 0

        self.root_switches = {}
        self.storages = {}

        self.resources = {}

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.volume_list = []            # a list of placed volumes

        self.last_update = 0
        self.last_link_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0  
        self.avail_mem_cap = 0
        self.local_disk_cap = 0 
        self.avail_local_disk_cap = 0


# Data container for rack or cluster
class HostGroup: 
    
    def __init__(self, _id):
        self.name = _id
        self.host_type = "rack"          # rack or cluster(e.g., power domain, zone)

        self.status = "enabled"

        self.memberships = {}            # all available logical groups (e.g., aggregate) in this group

        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB
        self.avail_local_disk_cap = 0

        self.switches = {}               # ToRs
        self.storages = {} 

        self.parent_resource = None      # e.g., datacenter
        self.child_resources = {}        # e.g., hosting servers

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.volume_list = []            # a list of placed volumes

        self.last_update = 0
        self.last_link_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0  
        self.avail_mem_cap = 0
        self.local_disk_cap = 0 
        self.avail_local_disk_cap = 0

    def init_memberships(self):
        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if lg.group_type == "EX" or lg.group_type == "AFF":
                level = lg.name.split(":")[0]
                if LEVELS.index(level) < LEVELS.index(self.host_type):
                    del self.memberships[lgk]
                else:
                    if self.name not in lg.vms_per_host.keys():
                        del self.memberships[lgk]
            else:
                del self.memberships[lgk]

    def check_availability(self):
        if self.status == "enabled":
            return True
        else:
            return False


class Host:

    def __init__(self, _name):
        self.name = _name

        self.tag = []                    # mark if this is synch'ed by multiple sources
        self.status = "enabled"
        self.state = "up"

        self.memberships = {}            # logical group (e.g., aggregate) this hosting server is involved in

        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0                 # MB
        self.avail_mem_cap = 0
        self.local_disk_cap = 0          # GB, ephemeral
        self.avail_local_disk_cap = 0
     
        self.switches = {}               # leaf
        self.storages = {} 

        self.host_group = None           # e.g., rack

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.volume_list = []            # a list of placed volumes

        self.last_update = 0
        self.last_link_update = 0

    def clean_memberships(self):
        cleaned = False

        for lgk in self.memberships.keys():
            lg = self.memberships[lgk]
            if lg.group_type == "EX" or lg.group_type == "AFF":
                if self.name not in lg.vms_per_host.keys():
                    del self.memberships[lgk]

                    cleaned = True
    
        return cleaned

    def check_availability(self):
        if self.status == "enabled" and self.state == "up" and \
           ("nova" in self.tag) and ("infra" in self.tag):
            return True
        else:
            return False

    def exist_vm(self, _vm_id):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[1] == _vm_id[1] and vm_id[2] == _vm_id[2]: # same name and uuid
                exist = True
                break

        return exist


class LogicalGroup:

    def __init__(self, _name):
        self.name = _name
        self.group_type = "AGGR"         # AGGR, AZ, INTG, EX, or AFF

        self.metadata = {}               # any metadata to be matched when placing nodes

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.volume_list = []            # a list of placed volumes

        self.vms_per_host = {}           # key = host_id, value = a list of placed vms

        #self.last_update = 0

    def exist_vm(self, _vm_id):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[1] == _vm_id[1] and vm_id[2] == _vm_id[2]: # same name and uuid
                exist = True
                break

        return exist

    def add_vm(self, _vm_id, _host_id):
        if self.exist_vm(_vm_id) == False:
            self.vm_list.append(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF":
                if _host_id not in self.vms_per_host.keys():
                    self.vms_per_host[_host_id] = []

            self.vms_per_host[_host_id].append(_vm_id)

    def remove_vm(self, _vm_id, _host_id):
        if self.exist_vm(_vm_id) == True:
            self.vm_list.remove(_vm_id)

            self.vms_per_host[_host_id].remove(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF":
                if len(self.vms_per_host[_host_id]) == 0:
                    del self.vms_per_host[_host_id]


class Switch: 
    
    def __init__(self, _switch_id):
        self.name = _switch_id
        self.switch_type = "ToR"         # root, spine, ToR, or leaf

        self.status = "enabled"

        self.up_links = {}
        self.down_links = {}             # currently, not used
        self.peer_links = {}

        self.last_update = 0


class Link:

    def __init__(self, _name):
        self.name = _name                # format: source + "-" + target
        self.resource = None             # switch beging connected to

        self.nw_bandwidth = 0            # Mbps
        self.avail_nw_bandwidth = 0


# TODO: storage backend, pool, or physical storage? 
class StorageHost: 

    def __init__(self, _name):
        self.name = _name                
        self.storage_class = None        # tiering, e.g., platinum, gold, silver 
  
        self.status = None
        self.host_list = []  

        self.disk_cap = 0                # GB
        self.avail_disk_cap = 0

        self.volume_list = []            # list of volume names placed in this host

        self.last_update = 0
        self.last_cap_update = 0


class Flavor:

    def __init__(self, _name):
        self.name = _name

        self.vCPUs = 0
        self.mem_cap = 0
        self.disk_cap = 0

        self.extra_specs = {}




