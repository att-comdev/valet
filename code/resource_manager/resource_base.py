#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Dec. 7, 2015
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

        self.vm_list = []                # a list of placed vm names
        self.volume_list = []            # a list of placed volume names

        self.last_update = 0
        self.last_link_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0  
        self.avail_mem_cap = 0
        self.local_disk_cap = 0 
        self.avail_local_disk_cap = 0


# Information of rack or cluster
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

        self.vm_list = []                # a list of placed vm names
        self.volume_list = []            # a list of placed volume names

        self.last_update = 0
        #self.last_metadata_update = 0
        self.last_link_update = 0

    def init_resources(self):
        self.vCPUs = 0
        self.avail_vCPUs = 0
        self.mem_cap = 0  
        self.avail_mem_cap = 0
        self.local_disk_cap = 0 
        self.avail_local_disk_cap = 0

    def init_memberships(self):
        for mk in self.memberships.keys():
            m = self.memberships[mk]:
            if m.group_type == "EX":
                level = m.name.split(":")[0]
                if LEVELS.index(level) < LEVELS.index(self.host_type):
                    del self.memberships[mk]
                else:
                    if len(self.vm_list) == 0:
                        del self.memberships[mk]
            else:
                del self.memberships[mk]

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

        self.vCPUs = -1
        self.avail_vCPUs = -1
        self.mem_cap = -1                # MB
        self.avail_mem_cap = -1
        self.local_disk_cap = -1         # GB, ephemeral
        self.avail_local_disk_cap = -1
     
        self.switches = {}               # leaf
        self.storages = {} 

        self.host_group = None           # e.g., rack

        self.vm_list = []                # a list of placed vm names
        self.volume_list = []            # a list of placed volume names

        self.last_update = 0
        #self.last_metadata_update = 0
        self.last_link_update = 0

    def check_availability(self):
        if self.status == "enabled" and self.state == "up" and \
           ("nova" in self.tag) and ("infra" in self.tag):
            return True
        else:
            return False


class LogicalGroup:

    def __init__(self, _name):
        self.name = _name
        self.group_type = "AGGR"         # AGGR, AZ, INTG, or EX

        self.metadata = {}               # any metadata to be matched when placing nodes


class Switch: 
    
    def __init__(self, _switch_id):
        self.name = _switch_id
        self.switch_type = "ToR"         # root, spine, ToR, or leaf

        self.status = "enabled"

        self.up_links = {}
        #self.down_links = {}
        self.peer_links = {}

        self.last_update = 0


class Link:

    def __init__(self, _name):
        self.name = _name                # format: source + "-" + target
        self.resource = None             # switch beging connected to

        self.nw_bandwidth = -1           # Mbps
        self.avail_nw_bandwidth = -1


# TODO: storage backend, pool, or physical storage? 
class StorageHost: 

    def __init__(self, _name):
        self.name = _name                
        self.storage_class = None        # tiering, e.g., platinum, gold, silver 
  
        self.status = None
        #self.timestamp = 0
        #self.protocoal = None
        self.host_list = []  
        #self.vendor = None
        #self.backend_name = None 

        self.disk_cap = -1               # GB
        self.avail_disk_cap = -1

        #self.iops = -1
        #self.avail_iops = -1

        self.volume_list = []            # list of volume names placed in this host

        self.last_update = 0
        self.last_cap_update = 0


class Flavor:

    def __init__(self, _name):
        self.name = _name

        self.vCPUs = -1
        self.mem_cap = -1
        self.disk_cap = -1

        self.extra_specs = {}

        #self.last_update = 0



