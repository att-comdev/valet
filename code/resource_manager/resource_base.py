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

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.root_switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        child_list = []
        for ck in self.resources.keys():
            child_list.append(ck)

        return {'status':self.status, \
                'membership_list':membership_list, \
                'vCPUs':self.vCPUs, \
                'avail_vCPUs':self.avail_vCPUs, \
                'mem':self.mem_cap, \
                'avail_mem':self.avail_mem_cap, \
                'local_disk':self.local_disk_cap, \
                'avail_local_disk':self.avail_local_disk_cap, \
                'switch_list':switch_list, \
                'storage_list':storage_list, \
                'children':child_list, \
                'vm_list':self.vm_list, \
                'volume_list':self.volume_list, \
                'last_update':self.last_update, \
                'last_link_update':self.last_link_update}


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

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        child_list = []
        for ck in self.child_resources.keys():
            child_list.append(ck)

        return {'status':self.status, \
                'host_type':self.host_type, \
                'membership_list':membership_list, \
                'vCPUs':self.vCPUs, \
                'avail_vCPUs':self.avail_vCPUs, \
                'mem':self.mem_cap, \
                'avail_mem':self.avail_mem_cap, \
                'local_disk':self.local_disk_cap, \
                'avail_local_disk':self.avail_local_disk_cap, \
                'switch_list':switch_list, \
                'storage_list':storage_list, \
                'parent':self.parent_resource.name, \
                'children':child_list, \
                'vm_list':self.vm_list, \
                'volume_list':self.volume_list, \
                'last_update':self.last_update, \
                'last_link_update':self.last_link_update}


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

    def get_json_info(self):
        membership_list = []
        for lgk in self.memberships.keys():
            membership_list.append(lgk)

        switch_list = []
        for sk in self.switches.keys():
            switch_list.append(sk)

        storage_list = []
        for shk in self.storages.keys():
            storage_list.append(shk)

        return {'tag':self.tag, 'status':self.status, 'state':self.state, \
                'membership_list':membership_list, \
                'vCPUs':self.vCPUs, \
                'avail_vCPUs':self.avail_vCPUs, \
                'mem':self.mem_cap, \
                'avail_mem':self.avail_mem_cap, \
                'local_disk':self.local_disk_cap, \
                'avail_local_disk':self.avail_local_disk_cap, \
                'switch_list':switch_list, \
                'storage_list':storage_list, \
                'parent':self.host_group.name, \
                'vm_list':self.vm_list, \
                'volume_list':self.volume_list, \
                'last_update':self.last_update, \
                'last_link_update':self.last_link_update}


class LogicalGroup:

    def __init__(self, _name):
        self.name = _name
        self.group_type = "AGGR"         # AGGR, AZ, INTG, EX, or AFF

        self.status = "enabled"

        self.metadata = {}               # any metadata to be matched when placing nodes

        self.vm_list = []                # a list of placed vms, (ochestration_uuid, vm_name, physical_uuid)
        self.volume_list = []            # a list of placed volumes

        self.vms_per_host = {}           # key = host_id, value = a list of placed vms

        self.last_update = 0

    def exist_vm(self, _vm_id):
        exist = False

        for vm_id in self.vm_list:
            if vm_id[1] == _vm_id[1] and vm_id[2] == _vm_id[2]: # same name and uuid
                exist = True
                break

        return exist

    def add_vm(self, _vm_id, _host_id):
        success = False

        if self.exist_vm(_vm_id) == False:
            self.vm_list.append(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF":
                if _host_id not in self.vms_per_host.keys():
                    self.vms_per_host[_host_id] = []

            self.vms_per_host[_host_id].append(_vm_id)

            success = True

        return success

    def remove_vm(self, _vm_id, _host_id):
        success = False

        if self.exist_vm(_vm_id) == True:
            self.vm_list.remove(_vm_id)

            self.vms_per_host[_host_id].remove(_vm_id)

            if self.group_type == "EX" or self.group_type == "AFF":
                if len(self.vms_per_host[_host_id]) == 0:
                    del self.vms_per_host[_host_id]
        
            success = True

        return success

    def get_json_info(self):
        return {'status':self.status, \
                'group_type':self.group_type, \
                'metadata':self.metadata, \
                'vm_list':self.vm_list, \
                'vms_per_host':self.vms_per_host, \
                'last_update':self.last_update}


class Switch: 
    
    def __init__(self, _switch_id):
        self.name = _switch_id
        self.switch_type = "ToR"         # root, spine, ToR, or leaf

        self.status = "enabled"

        self.up_links = {}
        self.down_links = {}             # currently, not used
        self.peer_links = {}

        self.last_update = 0

    def get_json_info(self):
        ulinks = {}
        for ulk, ul in self.up_links.iteritems():
            ulinks[ulk] = ul.get_json_info()

        plinks = {}
        for plk, pl in self.peer_links.iteritems():
            plinks[plk] = pl.get_json_info()

        return {'status':self.status, \
                'switch_type':self.switch_type, \
                'up_links':ulinks, \
                'peer_links':plinks, \
                'last_update':self.last_update}


class Link:

    def __init__(self, _name):
        self.name = _name                # format: source + "-" + target
        self.resource = None             # switch beging connected to

        self.nw_bandwidth = 0            # Mbps
        self.avail_nw_bandwidth = 0

    def get_json_info(self):
        return {'resource':self.resource.name, \
                'bandwidth':self.nw_bandwidth, \
                'avail_bandwidth':self.avail_nw_bandwidth}


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

    def get_json_info(self):
        return {'status':self.status, \
                'class':self.storage_class, \
                'host_list':self.host_list, \
                'disk':self.disk_cap, \
                'avail_disk':self.avail_disk_cap, \
                'volume_list':self.volume_list, \
                'last_update':self.last_update, \
                'last_cap_update':self.last_cap_update}


class Flavor:

    def __init__(self, _name):
        self.name = _name

        self.status = "enabled"

        self.vCPUs = 0
        self.mem_cap = 0
        self.disk_cap = 0

        self.extra_specs = {}

        self.last_update = 0

    def get_json_info(self):
        return {'status':self.status, \
                'vCPUs':self.vCPUs, \
                'mem':self.mem_cap, \
                'disk':self.disk_cap, \
                'extra_specs':self.extra_specs, \
                'last_update':self.last_update}





