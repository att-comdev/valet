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
import json, simplejson
import operator

from configuration import Config

sys.path.insert(0, '../db_connect')
from event import Event
from music import Music

sys.path.insert(0, '../util')
from util import adjust_json_string

class EventChecker:

    def __init__(self, _config):
        self.music = Music()

        self.config = _config
        
    def get_events(self):
        event_list = []

        events = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)

        if len(events) == 0:
            print "error: no events entered"
        else:
            for rowk, row in events.iteritems():
                event_id = row['timestamp']
                exchange = row['exchange']
                method = row['method']
                args_data = row['args']

                if exchange != "nova":
                    self.delete_event(event_id)
                    continue

                if method != 'object_action' and method != 'build_and_run_instance':
                    self.delete_event(event_id)
                    continue

                if len(args_data) == 0:
                    self.delete_event(event_id)
                    continue

                args_data = adjust_json_string(args_data)

                #args = simplejson.loads(row['args'])
                try:
                    args = json.loads(args_data)                                                 
                except (ValueError, KeyError, TypeError):   
                    print "event args parsing error = ", event_id                                     
                    continue                                                                     
                                                                                                 
                if method == 'object_action':                                                    
                    if 'objinst' in args.keys():                                                 
                        objinst = args['objinst']                                                
                        if 'nova_object.name' in objinst.keys():                                 
                            nova_object_name = objinst['nova_object.name']                       
                            if nova_object_name == 'Instance':                                   
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():                      
                                    change_list = objinst['nova_object.changes']                 
                                    change_data = objinst['nova_object.data']                    
                                    if 'vm_state' in change_list and \
                                       'vm_state' in change_data.keys():                     
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
                            elif nova_object_name == 'ComputeNode':                              
                                if 'nova_object.changes' in objinst.keys() and \
                                   'nova_object.data' in objinst.keys():                      
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
                    '''                                                                
                    else:                                                                        
                        filter_properties = args['filter_properties']                            
                        if 'scheduler_hints' not in filter_properties.keys():                    
                            self.delete_event(event_id)                                          
                            continue
                    '''                                                             
                                                                                                 
                    if 'instance' not in args.keys():                                            
                        self.delete_event(event_id)                                              
                        continue                                                                 
                    else:                                                                        
                        instance = args['instance']                                              
                        if 'nova_object.data' not in instance.keys():                            
                            self.delete_event(event_id)                                          
                            continue                                                             
                                                                                                 
                    e = Event(event_id)                                                          
                    e.exchange = exchange                                                        
                    e.method = method                                                            
                    e.args = args                                                                
                    event_list.append(e)  

        error_event_list = []
        for e in event_list:
            e.set_data()

            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.uuid == None or e.uuid == "none" or \
                       e.host == None or e.host == "none" or \
                       e.vcpus == -1 or e.mem == -1:
                        error_event_list.append(e)
                                         
                elif e.object_name == 'ComputeNode':
                    if e.host == None or e.host == "none":                                               
                        error_event_list.append(e)

            elif e.method == "build_and_run_instance": 
                '''
                if e.heat_resource_name == None or e.heat_resource_name == "none" or \
                   e.heat_resource_uuid == None or e.heat_resource_uuid == "none" or \
                   e.heat_root_stack_id == None or e.heat_root_stack_id == "none" or \
                   e.heat_stack_name == None or e.heat_stack_name == "none" or \
                   e.uuid == None or e.uuid == "none":
                '''
                if e.uuid == None or e.uuid == "none":                                                   
                    error_event_list.append(e)
       
        if len(error_event_list) > 0: 
            event_list[:] = [e for e in even_list if e not in error_event_list]
            
        if len(event_list) > 0:                                                
            event_list.sort(key=operator.attrgetter('event_id'))                                     
           
        return event_list

    def delete_event(self, _event_id):                                                           
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_event_table, \
                                         'timestamp', _event_id)



if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Client: " + config_status
        sys.exit(2)

    ec = EventChecker(config)

    event_list = ec.get_events()
    for e in event_list:
        print "event_id = ", e.event_id
        #print json.dumps(e.args, indent=4)
        if e.method == 'object_action' and e.object_name == 'ComputeNode':
            for cell in e.numa_cell_list:
                #print json.dumps(cell, indent=4)        
                if 'nova_object.data' in cell.keys():
                    if 'cpuset' in cell['nova_object.data']:
                        cpuset = cell['nova_object.data']['cpuset']
                        for c in cpuset:
                            print "core = ", c





