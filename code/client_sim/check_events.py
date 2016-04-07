#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
#
#################################################################################################################


import sys
import time
import json, simplejson
import operator


from configuration import Config

sys.path.insert(0, '../db_connect')
from music import Music


class Event:

    def __init__(self, _id):
        self.event_id = _id
        self.exchange = None
        self.method = None
        self.args = {}


class MusicClient:

    def __init__(self, _config):
        self.config = _config

        self.music = Music()

    def set_event(self, _k, _m, _event):
        args = open(_event, 'r')
        args_data = args.read()

        args_data = args_data.replace("'", '"')

        data = {
            'timestamp': str(_k),
            'exchange': 'nova',
            'method': _m,
            'args': args_data
        }

        print "set event = ", _k

        self.music.create_row(self.config.db_keyspace, self.config.db_event_table, data)

    def get_events(self):
        event_list = []

        events = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)  
        if len(events) > 0:                                                           
            # Update resource status                                                             
            # Delete each row once done                                                          

            for rowk, row in events.iteritems():
                event_id = row['timestamp']
                exchange = row['exchange']
                method = row['method']
                args_data = row['args']

                print "event_id=",event_id
                print "exchange=",exchange 
                print "method=",method 

                if exchange != "nova":
                    self.delete_event(event_id)
                    continue

                #method == 'build_instance'
                #method == 'terminate_instance'
                if method != 'object_action' and method != 'build_and_run_instance':
                    self.delete_event(event_id)
                    continue

                if len(args_data) == 0:
                    self.delete_event(event_id)
                    continue

                #args_data = args_data.replace("'", '"')
                args_data = args_data.replace('"{', '{')
                args_data = args_data.replace('}"', '}')
                args_data = args_data.replace("None", '"none"')
                args_data = args_data.replace("False", '"false"')
                args_data = args_data.replace("True", '"true"')
                args_data = args_data.replace('_"none"', "_none")
                args_data = args_data.replace('_"false"', "_false")
                args_data = args_data.replace('_"true"', "_true")

                #args = simplejson.loads(row['args'])
                try:
                    args = json.loads(args_data)
                except (ValueError, KeyError, TypeError):
                    print "error while decoding to JSON for event_id = ", event_id
                    continue

                if method == 'object_action':
                    if 'objinst' in args.keys():
                        objinst = args['objinst']
                        if 'nova_object.name' in objinst.keys():
                            nova_object_name = objinst['nova_object.name']
                            if nova_object_name == 'Instance':
                                if 'nova_object.changes' in objinst.keys():
                                    change_list = objinst['nova_object.changes']
                                    change_data = objinst['nova_object.data']
                                    if 'vm_state' in change_list:
                                        if 'vm_state' in change_data.keys():
                                            if change_data['vm_state'] == 'deleted' or \
                                               change_data['vm_state'] == 'active':
                                                e = Event(event_id)
                                                e.exchange = exchange
                                                e.method = method
                                                e.args = args
                                                event_list.append(e)
                                            else:
                                                self.delete_event(event_id)
                                        else:
                                            self.delete_event(event_id)
                                    else:
                                        self.delete_event(event_id)
                                else:
                                    self.delete_event(event_id)
                            elif nova_object_name == 'ComputeNode':
                                if 'nova_object.changes' in objinst.keys():
                                    e = Event(event_id)
                                    e.exchange = exchange
                                    e.method = method
                                    e.args = args
                                    event_list.append(e)
                                else:
                                    self.delete_event(event_id)
                            else:
                                self.delete_event(event_id)
                        else:
                            self.delete_event(event_id)
                    else:
                        self.delete_event(event_id)

                elif method == 'build_and_run_instance':
                    if 'filter_properties' not in args.keys():
                        self.delete_event(event_id)
                        continue
                    else:
                        filter_properties = args['filter_properties']
                        if 'scheduler_hints' not in filter_properties.keys():
                            self.delete_event(event_id)
                            continue

                    if 'instance' not in args.keys():
                        self.delete_event(event_id)
                        continue
                    else:
                        instance = args['instance']
                        if 'nova_object.data' not in instance.keys():
                            self.delete_event(event_id)
                            continue

                    '''
                    if 'node' not in args.keys():
                        self.delete_event(event_id)
                        continue
                    '''

                    e = Event(event_id)
                    e.exchange = exchange
                    e.method = method
                    e.args = args
                    event_list.append(e)

        event_list.sort(key=operator.attrgetter('event_id'))       
 
        return event_list

    def delete_event(self, _event_id):
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_event_table, \
                                         'timestamp', _event_id)

    def get_data(self, e):
        print "key = ", e.event_id 

        if e.method == 'object_action':
            change_list = e.args['objinst']['nova_object.changes']
            change_data = e.args['objinst']['nova_object.data']

            object_name = e.args['objinst']['nova_object.name']
            if object_name == 'Instance':
                uuid = None
                host = None
                vcpus = -1
                mem = -1
                root = -1
                ephemeral = -1
                swap = -1
                disk_gb = 0
                vm_state = None               

                if 'uuid' in change_data.keys():
                    uuid = change_data['uuid']
                    print "uuid=",uuid

                if 'host' in change_data.keys():
                    host = change_data['host']
                    print "host=", host

                if 'vcpus' in change_data.keys():
                    vcpus = float(change_data['vcpus'])
                    print "vcpus=",vcpus

                if 'memory_mb' in change_data.keys():
                    mem = float(change_data['memory_mb'])
                    print "mem=",mem

                if 'root_gb' in change_data.keys():
                    root = float(change_data['root_gb'])
                    print "root=",root

                if 'ephemeral_gb' in change_data.keys():
                    ephemeral = float(change_data['ephemeral_gb'])
                    print "ephemeral=",ephemeral

                if 'flavor' in change_data.keys():
                    flavor = change_data['flavor']
                    if 'nova_object.data' in flavor.keys():
                        flavor_data = flavor['nova_object.data']
                        if 'swap' in flavor_data.keys():
                            swap = float(flavor_data['swap'])

                vm_state = change_data['vm_state']
                print "vm_state=",vm_state

                if uuid == None or uuid == "none" or \
                   host == None or host == "none" or \
                   vcpus == -1 or mem == -1 or root == -1 or ephemeral == -1 or swap == -1:
                    print "error: data missing in event"
                else:
                    disk_gb = root + ephemeral + swap/float(1024)
                    print "disk=",disk_gb

            elif object_name == 'ComputeNode':
                host = None
                status = "enabled"
                vcpus = -1
                vcpus_used = -1
                mem = -1
                free_mem = -1
                local_disk = -1
                free_local_disk = -1
                disk_available_least = -1      

                if 'host' in change_data.keys():
                    host = change_data['host']
                    print "host=", host

                if 'deleted' in change_list and 'deleted' in change_data.keys():
                    if change_data['deleted'] == "true" or change_data['deleted'] == True:
                        status = "disabled"
                    print "status=",status

                if 'vcpus' in change_list and 'vcpus' in change_data.keys():
                    vcpus = change_data['vcpus']
                    print "vcpus=",vcpus

                if 'vcpus_used' in change_list and 'vcpus_used' in change_data.keys():
                    vcpus_used = change_data['vcpus_used']
                    print "vcpus_used=",vcpus_used

                if 'memory_mb' in change_list and 'memory_mb' in change_data.keys():
                    mem = change_data['memory_mb']
                    print "mem=",mem

                '''
                if 'memory_mb_used' in change_list:
                    print "mem_used=", change_data['memory_mb_used']
                '''

                if 'free_ram_mb' in change_list and 'free_ram_mb' in change_data.keys():
                    free_mem = change_data['free_ram_mb']
                    print "free_mem=",free_mem

                if 'local_gb' in change_list and 'local_gb' in change_data.keys():
                    local_disk = change_data['local_gb']
                    print "disk=",local_disk

                '''
                if 'local_gb_used' in change_list:
                    print "disk_used=", change_data['local_gb_used']
                '''

                if 'free_disk_gb' in change_list and 'free_disk_gb' in change_data.keys():
                    free_local_disk = change_data['free_disk_gb']
                    print "free_disk=",free_local_disk

                if 'disk_available_least' in change_list and 'disk_available_least' in change_data.keys():
                    disk_available_least = change_data['disk_available_least']
                    print "disk_available_least=",disk_available_least

                '''
                if 'running_vms' in change_list:
                    print "running_vms=", change_data['running_vms']
                '''

                if host == None or host == "none":
                    print "error: data missing in event"

        elif e.method == 'build_and_run_instance':
            heat_resource_name = None 
            heat_resource_uuid = None 
            heat_root_stack_id = None
            heat_stack_name = None
            uuid = None
           
            if 'heat_resource_name' in e.args['filter_properties']['scheduler_hints'].keys(): 
                heat_resource_name = e.args['filter_properties']['scheduler_hints']['heat_resource_name'] 
                print "heat_resource_name=",heat_resource_name
            if 'heat_resource_uuid' in e.args['filter_properties']['scheduler_hints'].keys(): 
                heat_resource_uuid = e.args['filter_properties']['scheduler_hints']['heat_resource_uuid'] 
                print "heat_resource_uuid=",heat_resource_uuid
            if 'heat_root_stack_id' in e.args['filter_properties']['scheduler_hints'].keys(): 
                heat_root_stack_id = e.args['filter_properties']['scheduler_hints']['heat_root_stack_id'] 
                print "heat_stack_id=",heat_root_stack_id
            if 'heat_stack_name' in e.args['filter_properties']['scheduler_hints'].keys(): 
                heat_stack_name = e.args['filter_properties']['scheduler_hints']['heat_stack_name']
                print "heat_stack_name=",heat_stack_name

            if 'uuid' in e.args['instance']['nova_object.data'].keys(): 
                uuid = e.args['instance']['nova_object.data']['uuid'] 
                print "uuid=",uuid

            if heat_resource_name == None or heat_resource_name == "none" or \
               heat_resource_uuid == None or heat_resource_uuid == "none" or \
               heat_root_stack_id == None or heat_root_stack_id == "none" or \
               heat_stack_name == None or heat_stack_name == "none" or \
               uuid == None or uuid == "none":
                print "error: data missing in event"
            

# Unit test
if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    mc = MusicClient(config)
    
    remain_events = mc.music.read_all_rows(config.db_keyspace, config.db_event_table) 
    if len(remain_events) > 0:
        print "Remained events"                                                           
        for rowk, row in remain_events.iteritems():
            event_id = row['timestamp']
            exchange = row['exchange']
            method = row['method']

            print "event_id=",event_id
            print "exchange=",exchange 
            print "method=",method 
    else:
        print "No remained events"

    time.sleep(5)
    mc.set_event(time.time(), "object_class_action", "./test_events/object_class_action_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "build_and_run_instance", "./test_events/build_and_run_instance_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_instance_0.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_instance_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_device_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_compute_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_instance_reflesh_1.json")
    time.sleep(1)
    mc.set_event(time.time(), "object_action", "./test_events/object_action_instance_2.json")
    time.sleep(1)
    mc.set_event(time.time(), "service_update", "./test_events/service_update_1.json")
    time.sleep(1)

    event_list = mc.get_events()
    for e in event_list:
        mc.get_data(e)

    remain_events = mc.music.read_all_rows(config.db_keyspace, config.db_event_table) 
    if len(remain_events) > 0:
        print "Remained events"                                                           
        for rowk, row in remain_events.iteritems():
            event_id = row['timestamp']
            exchange = row['exchange']
            method = row['method']

            print "event_id=",event_id
            print "exchange=",exchange 
            print "method=",method               


