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

from music import Music
from event import Event

sys.path.insert(0, '../util')
from util import adjust_json_string

class MusicHandler:

    def __init__(self, _config, _logger):
        self.music = Music()

        self.config = _config
        
        self.logger = _logger

    def init_db(self):
        self.music.create_keyspace(self.config.db_keyspace)

        schema = {
            'stack_id': 'text',
            'request': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_request_table, schema)

        schema = {
            'stack_id': 'text',
            'placement': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_response_table, schema)

        schema = {
            'timestamp': 'text',
            'exchange': 'text',
            'method': 'text',
            'args': 'text',
            'PRIMARY KEY': '(timestamp)'
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_event_table, schema)

        schema = {
            'site_name': 'text',
            'resource': 'text',
            'PRIMARY KEY': '(site_name)'                                                         
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_resource_table, schema)      

        schema = {
            'stack_id': 'text',
            'app': 'text',
            'PRIMARY KEY': '(stack_id)'                                                         
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_app_table, schema)      

        schema = {
            'site_name': 'text',
            'app_log_index': 'text',
            'PRIMARY KEY': '(site_name)'                                                         
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_app_index_table, schema)     

        schema = {
            'site_name': 'text',
            'resource_log_index': 'text',
            'PRIMARY KEY': '(site_name)'                                                         
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_resource_index_table, schema)  

        schema = {
            'uuid': 'text',
            'h_uuid': 'text',
            's_uuid': 'text',
            'PRIMARY KEY': '(uuid)'                                                         
        }
        self.music.create_table(self.config.db_keyspace, self.config.db_uuid_table, schema)  

    def get_events(self):
        event_list = []

        events = self.music.read_all_rows(self.config.db_keyspace, self.config.db_event_table)

        if len(events) > 0:
            for rowk, row in events.iteritems():
                event_id = row['timestamp']
                exchange = row['exchange']
                method = row['method']
                args_data = row['args']

                self.logger.debug("db: event (" + event_id + ") is entered")

                if exchange != "nova":
                    self.delete_event(event_id)
                    self.logger.debug("db: event exchange (" + exchange + ") is not supported")
                    continue

                if method != 'object_action' and method != 'build_and_run_instance':
                    self.delete_event(event_id)
                    self.logger.debug("db: event method (" + method + ") is not considered")
                    continue

                if len(args_data) == 0:
                    self.delete_event(event_id)
                    self.logger.debug("db: event does not have args")
                    continue

                args_data = adjust_json_string(args_data)

                #args = simplejson.loads(row['args'])
                try:
                    args = json.loads(args_data)                                                 
                except (ValueError, KeyError, TypeError):                                        
                    self.logger.warn("db: error while decoding to JSON event = " + method)               
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

            self.logger.debug("db: event (" + e.event_id + ") is parsed")

            if e.method == "object_action":
                if e.object_name == 'Instance':
                    if e.uuid == None or e.uuid == "none" or \
                       e.host == None or e.host == "none" or \
                       e.vcpus == -1 or e.mem == -1:
                        error_event_list.append(e)
                        self.logger.warn("db: data missing in instance object event")
                                         
                elif e.object_name == 'ComputeNode':
                    if e.host == None or e.host == "none":                                               
                        error_event_list.append(e)
                        self.logger.warn("db: data missing in compute object event")

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
                    self.logger.warn("db: data missing in build event")
       
        if len(error_event_list) > 0: 
            event_list[:] = [e for e in even_list if e not in error_event_list]
            
        if len(event_list) > 0:                                                
            event_list.sort(key=operator.attrgetter('event_id'))                                     
           
        return event_list

    def delete_event(self, _event_id):                                                           
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_event_table, \
                                         'timestamp', _event_id)

    def get_uuid(self, _uuid):
        h_uuid = None
        s_uuid = None

        row = self.music.read_row(self.config.db_keyspace, self.config.db_uuid_table, 'uuid', _uuid)

        if len(row) > 0:
            h_uuid  = row[row.keys()[0]]['h_uuid']
            s_uuid  = row[row.keys()[0]]['s_uuid']

            self.logger.info("db: get heat uuid (" + h_uuid + ") for uuid = " + _uuid)
        else:
            self.logger.debug("db: heat uuid not found")

        return (h_uuid, s_uuid)

    def put_uuid(self, _e):
        heat_resource_uuid = "none"
        heat_root_stack_id = "none"
        if _e.heat_resource_uuid != None and _e.heat_resource_uuid != "none":
            heat_resource_uuid = _e.heat_resource_uuid
        if _e.heat_root_stack_id != None and _e.heat_root_stack_id != "none":
            heat_root_stack_id = _e.heat_root_stack_id
                                          
        data = {                                                                             
            'uuid': _e.uuid,
            'h_uuid': heat_resource_uuid,
            's_uuid': heat_root_stack_id                                                                
        }                                                                                    
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_uuid_table, data)

        self.logger.info("db: uuid (" + _e.uuid + ") added")
        
        '''                                                                                         
        self.delete_event(_e.event_id)

        self.logger.info("db: build event (" + _e.event_id + ") deleted")
        '''

    def delete_uuid(self, _k):
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_uuid_table, \
                                         'uuid', _k)

    def get_requests(self):                                                                     
        request_list = []                                                                        
                                                                                                 
        requests = self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)

        if len(requests) > 0:                                                                    
            self.logger.info("db: placement request arrived")

            for rowk, row in requests.iteritems():  
                self.logger.info("    request_id = " + row['stack_id'])
                                             
                r_list = json.loads(row['request'])                                              
                for r in r_list:                                                                 
                    request_list.append(r)                                                       
                                                                                                 
        return request_list

    def put_result(self, _result):                                                              
        for appk, app_placement in _result.iteritems():                                          
            data = {                                                                             
                'stack_id': appk,                                                                
                'placement': json.dumps(app_placement)                                                       
            }                                                                                    
                                                                                                 
            self.music.create_row(self.config.db_keyspace, self.config.db_response_table, data)

        self.logger.info("db: placement result added")
                                                                                                 
        for appk in _result.keys(): 
            self.music.delete_row_eventually(self.config.db_keyspace, \
                                             self.config.db_request_table, \
                                             'stack_id', \
                                             appk)

        self.logger.info("db: placement request deleted")

    def get_resource_status(self, _k):                                                  
        json_resource = {} 
 
        row = self.music.read_row(self.config.db_keyspace, self.config.db_resource_table, 'site_name', _k)
 
        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

            '''
            self.music.delete_row_eventually(self.config.db_keyspace, \
                                             self.config.db_resource_table, \
                                             'site_name', _k)
            '''
       
            self.logger.info("db: get resource status")

        return json_resource

    def update_resource_status(self, _k, _status):                                                  
        row = self.music.read_row(self.config.db_keyspace, self.config.db_resource_table, 'site_name', _k)
 
        json_resource = {}  
        if len(row) > 0:
            str_resource = row[row.keys()[0]]['resource']
            json_resource = json.loads(str_resource)

            if 'flavors' in _status.keys():                                                          
                flavors = _status['flavors']                                                         
                for fk, f in flavors.iteritems():                                                    
                    if fk in json_resource['flavors'].keys():                                        
                        del json_resource['flavors'][fk]  
                    json_resource['flavors'][fk] = f                                             
                                                                                                 
            if 'logical_groups' in _status.keys():                                                   
                logical_groups = _status['logical_groups']                                           
                for lgk, lg in logical_groups.iteritems():                                           
                    if lgk in json_resource['logical_groups'].keys():                                
                        del json_resource['logical_groups'][lgk]                                     
                    json_resource['logical_groups'][lgk] = lg                                   
                                                                                                 
            if 'storages' in _status.keys():                                                         
                storages = _status['storages']                                                       
                for stk, st in storages.iteritems():                                                 
                    if stk in json_resource['storages'].keys():                                      
                        del json_resource['storages'][stk]                                           
                    json_resource['storages'][stk] = st                                          
                                                                                                 
            if 'switches' in _status.keys():                                                         
                switches = _status['switches']                                                       
                for sk, s in switches.iteritems():                                                   
                    if sk in json_resource['switches'].keys():                                       
                        del json_resource['switches'][sk]                                            
                    json_resource['switches'][sk] = s                                            
                                                                                                 
            if 'hosts' in _status.keys():                                                            
                hosts = _status['hosts']                                                             
                for hk, h in hosts.iteritems():                                                      
                    if hk in json_resource['hosts'].keys():                                          
                        del json_resource['hosts'][hk]                                               
                    json_resource['hosts'][hk] = h                                               
                                                                                                 
            if 'host_groups' in _status.keys():                                                      
                host_groupss = _status['host_groups']                                                
                for hgk, hg in host_groupss.iteritems():                                             
                    if hgk in json_resource['host_groups'].keys():                                   
                        del json_resource['host_groups'][hgk]                                        
                    json_resource['host_groups'][hgk] = hg                                       
                                                                                                 
            if 'datacenter' in _status.keys():                                                       
                datacenter = _status['datacenter']                                                   
                del json_resource['datacenter']                                                      
                json_resource['datacenter'] = datacenter                                             
                                                                                                 
            json_resource['timestamp'] = _status['timestamp']                                        
                                                                                                 
            self.music.delete_row_eventually(self.config.db_keyspace, \
                                             self.config.db_resource_table, \
                                             'site_name', _k)
        else:
            json_resource = _status 
 
        data = {                                                                                 
            'site_name': _k,     
            'resource': json.dumps(json_resource)                                                
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_resource_table, data)

        self.logger.info("db: resource status updated")

    def update_resource_log_index(self, _k, _index):
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_resource_index_table, \
                                         'site_name', _k)

        data = {                                                                                 
            'site_name': _k,     
            'resource_log_index': str(_index)                                                
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_resource_index_table, data)

        self.logger.info("db: resource log index updated")

    def update_app_log_index(self, _k, _index):
        self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_app_index_table, 'site_name', _k)

        data = {                                                                                 
            'site_name': _k,     
            'app_log_index': str(_index)                                                
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_app_index_table, data)

        self.logger.info("db: app log index updated")

    def add_app(self, _k, _app_data):
        self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _k)
        
        data = {                                                                                 
            'stack_id': _k,     
            'app': json.dumps(_app_data)                                               
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_app_table, data)

        self.logger.info("db: app added")

    # TODO: get all other VMs related to this VM
    def get_vm_info(self, _s_uuid, _h_uuid, _host): 
        updated = False
        json_app = {}

        vm_info = {}

        row = self.music.read_row(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _s_uuid)

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

            vms = json_app["VMs"]
            for vmk, vm in vms.iteritems():
                if vmk == _h_uuid:
                    if vm["status"] != "deleted":
                        if vm["host"] != _host:
                            vm["planned_host"] = vm["host"]
                            vm["host"] = _host
                            self.logger.warn("db: conflicted placement decision from Ostro")
                            # TODO: affinity, diversity, exclusivity validation check
                            updated = True
                        else:
                            self.logger.debug("db: placement as expected")
                    else:
                        vm["status"] = "scheduled"
                        self.logger.warn("db: vm was deleted")
                        updated = True

                    vm_info = vm
                    break
            else:
                self.logger.error("db: vm is missing from stack")

        else:
            self.logger.warn("db: not found stack for update = " + _s_uuid)

        if updated == True:
            self.add_app(_s_uuid, json_app)

        return vm_info

    def update_vm_info(self, _s_uuid, _h_uuid):
        updated = False
        json_app = {}

        row = self.music.read_row(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _s_uuid)

        if len(row) > 0:
            str_app = row[row.keys()[0]]['app']
            json_app = json.loads(str_app)

            vms = json_app["VMs"]
            for vmk, vm in vms.iteritems():
                if vmk == _h_uuid:
                    if vm["status"] != "deleted":
                        vm["status"] = "deleted"
                        self.logger.debug("db: deleted marked")
                        updated = True
                    else:
                        self.logger.warn("db: vm was already deleted")

                    break
            else:
                self.logger.error("db: vm is missing from stack")

        else:
            self.logger.warn("db: not found stack for update = " + _s_uuid)

        if updated == True:
            self.add_app(_s_uuid, json_app)






