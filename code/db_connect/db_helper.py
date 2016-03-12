#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016

#################################################################################################################

#import sys, os
#import json
from cassandra.cqlengine.columns import *
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.usertype import UserType


# "Apps" table definition: 
#     Row key: app_id
#     Column: app_info -->{vms, volumes, vgroups, event}
#     When app_info is changed, insert a new column


class VM(UserType):

    name = Text()
    status = Text()
    uuid = Text()
    affinity_group = Text()
    availability_zone = Text()
    diversity_groups = Map(Text, Text)
    cpu = Integer()
    mem = Integer()
    local_volume = Integer()
    nw = Integer()
    io = Integer()
    vol_links = Map(Text, Integer)
    vm_links = Map(Text, Integer)
    host = Text() 

    #def to_json(self):
        #return {'name':self.name,...}

    #def __repr__(self):
        #return '%s %s %s' % (self.name, ...)

class Volume(UserType):

    name = Text()
    status = Text()
    uuid = Text()
    affinity_group = Text()
    availability_zone = Text()
    diversity_groups = Map(Text, Text)
    vol_class = Text()
    size = Integer()
    io = Integer()
    vm_links = Map(Text, Integer)
    host = Text() 

    #def to_json(self):
        #return {'name':self.name,...}

    #def __repr__(self):
        #return '%s %s %s' % (self.name, ...)

class VGroup(UserType):

    name = Text()
    affinity_group = Text()
    availability_zone = Text()
    diversity_groups = Map(Text, Text)
    level = Text()
    cpu = Integer()
    mem = Integer()
    local_volume = Integer()
    volume = Map(Text, Integer)
    nw = Integer()
    io = Integer()
    vol_links = Map(Text, Integer)
    vm_links = Map(Text, Integer)
    sub_vgroups = List(Text)
    vms = List(Text)
    volumes = List(Text)

    #def to_json(self):
        #return {'name':self.name,...}

    #def __repr__(self):
        #return '%s %s %s' % (self.name, ...)

class AppInfo(UserType):

    vms = Map(Text, UserDefinedType(VM))
    volumes = Map(Text, UserDefinedType(Volume))
    vgroups = Map(Text, UserDefinedType(VGroup))

class Apps(Model):

    app_id = Text(primary_key=True)
    event_time = DateTime(primary_key=True, clustering_order="ASC")
    status = Text()   # status: requested, scheduled, placed, updated, or deleted
    app_name = Text()
    app_info = UserDefinedType(AppInfo)


# "Infras" table definition: 

class InfrastructureInfo(UserType):
    capacity = Double()


class Infrastructures(Model):
    res_type = Text(primary_key=True)
    record_id = TimeUUID(primary_key=True, clustering_order="ASC")  # New record will be append to end
    infr_info = UserDefinedType(InfrastructureInfo)






###############################################
# Utility functions for databse content parsing

# Translate AppInfo to json format
def app_info_to_json(app):
    ret = {}
    ret['event'] = app.app_info.event.to_json()
    
    ret['constraints'] = {}
    for const_id, const_info in app.app_info.constraints.iteritems():
        ret['constraints'][const_id] = const_info.to_json()

    ret['VMs'] = {}
    for vm_id, vm_info in app.app_info.vm_list.iteritems():
        ret['VMs'][vm_id] = vm_info.to_json()

    ret['Pipes'] = {}
    for pipe_id, pipe_info in app.app_info.pipes.iteritems():
        ret['Pipes'][pipe_id] = pipe_info.to_json()

    return ret

