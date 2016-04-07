#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
#
#################################################################################################################


class Event:

    def __init__(self, _id):
        self.event_id = _id
        self.exchange = None
        self.method = None
        self.args = {}

        # For object_action event
        self.change_list = []
        self.change_data = {}
        self.object_name = None

        # For object_action and Instance object
        self.vm_state = None

        # For object_action and ComputeNode object
        self.status = "enabled"
        self.vcpus_used = -1
        self.free_mem = -1                                                                    
        self.free_local_disk = -1                                                             
        self.disk_available_least = -1

        # Common between Instance and ComputeNode
        self.host = None
        self.vcpus = -1
        self.mem = -1
        self.local_disk = 0

        # For build_and_run_instance
        self.heat_resource_name = None                                                            
        self.heat_resource_uuid = None                                                            
        self.heat_root_stack_id = None                                                            
        self.heat_stack_name = None

        # Common data
        self.uuid = None

    def set_data(self):
        if self.method == 'object_action':
            self.change_list = e.args['objinst']['nova_object.changes']
            self.change_data = e.args['objinst']['nova_object.data']
            self.object_name = e.args['objinst']['nova_object.name']

            if self.object_name == 'Instance':
                if 'uuid' in self.change_data.keys():
                    self.uuid = self.change_data['uuid']

                if 'host' in self.change_data.keys():
                    self.host = self.change_data['host']

                if 'vcpus' in self.change_data.keys():
                    self.vcpus = float(self.change_data['vcpus'])

                if 'memory_mb' in self.change_data.keys():
                    self.mem = float(self.change_data['memory_mb'])

                root = -1
                ephemeral = -1
                swap = -1
                if 'root_gb' in self.change_data.keys():
                    root = float(self.change_data['root_gb'])

                if 'ephemeral_gb' in self.change_data.keys():
                    ephemeral = float(self.change_data['ephemeral_gb'])

                if 'flavor' in self.change_data.keys():
                    flavor = self.change_data['flavor']
                    if 'nova_object.data' in flavor.keys():
                        flavor_data = flavor['nova_object.data']
                        if 'swap' in flavor_data.keys():
                            swap = float(flavor_data['swap'])

                if root != -1: 
                    self.local_disk += root
                if ephemeral != -1:
                    self.local_disk += ephemeral
                if swap != -1:
                    self.local_disk += swap/float(1024)

                self.vm_state = self.change_data['vm_state']

            elif self.object_name == 'ComputeNode':
                if 'host' in self.change_data.keys():                                                 
                    self.host = self.change_data['host']                                                   
                                                                                                 
                if 'deleted' in self.change_list and 'deleted' in self.change_data.keys():                 
                    if self.change_data['deleted'] == "true" or self.change_data['deleted'] == True:       
                        self.status = "disabled"                                                      
                                                                                                 
                if 'vcpus' in self.change_list and 'vcpus' in self.change_data.keys():                     
                    self.vcpus = self.change_data['vcpus']                                                 
                                                                                                 
                if 'vcpus_used' in self.change_list and 'vcpus_used' in self.change_data.keys():           
                    self.vcpus_used = self.change_data['vcpus_used']                                       
                                                                                                 
                if 'memory_mb' in self.change_list and 'memory_mb' in self.change_data.keys():             
                    self.mem = self.change_data['memory_mb']                                               
                                                                                                 
                if 'free_ram_mb' in self.change_list and 'free_ram_mb' in self.change_data.keys():         
                    self.free_mem = self.change_data['free_ram_mb']                                        
                                                                                                 
                if 'local_gb' in self.change_list and 'local_gb' in self.change_data.keys():               
                    self.local_disk = self.change_data['local_gb']                                         
                                                                                                 
                if 'free_disk_gb' in change_list and 'free_disk_gb' in change_data.keys():       
                    self.free_local_disk = self.change_data['free_disk_gb']                                
                                                                                                 
                if 'disk_available_least' in self.change_list and \
                   'disk_available_least' in self.change_data.keys():
                    self.disk_available_least = self.change_data['disk_available_least']                   
                                                 
        elif self.method == 'build_and_run_instance':
            if 'scheduler_hints' in self.args['filter_properties'].keys():
                scheduler_hints = self.args['filter_properties']['scheduler_hints']      
                if 'heat_resource_name' in scheduler_hints.keys():    
                    self.heat_resource_name = scheduler_hints['heat_resource_name'] 
                if 'heat_resource_uuid' in scheduler_hints.keys():    
                    self.heat_resource_uuid = scheduler_hints['heat_resource_uuid']
                if 'heat_root_stack_id' in scheduler_hints.keys():    
                    self.heat_root_stack_id = scheduler_hints['heat_root_stack_id']
                if 'heat_stack_name' in scheduler_hints.keys():       
                    self.heat_stack_name = scheduler_hints['heat_stack_name']
                                                                                                 
            if 'uuid' in self.args['instance']['nova_object.data'].keys():                          
                self.uuid = self.args['instance']['nova_object.data']['uuid']                            
            




