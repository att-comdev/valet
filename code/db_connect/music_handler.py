#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
#
#################################################################################################################


import json

from music import Music


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
            'event_id': 'text',
            'event': 'text',
            'PRIMARY KEY': '(event_id)'
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

    def get_requests(self):                                                                     
        event_list = []                                                                          
        request_list = []                                                                        
                                                                                                 
        #resource_updates = self.db.read_all_rows(self.config.db_keyspace, self.config.db_event_table)    
        #if len(resource_updates) > 0:                                                           
            # Update resource status                                                             
            # Delete each row once done                                                          
                                                                                                 
        requests = self.music.read_all_rows(self.config.db_keyspace, self.config.db_request_table)
        if len(requests) > 0:                                                                    
            for rowk, row in requests.iteritems():                                               
                r_list = json.loads(row['request'])                                              
                for r in r_list:                                                                 
                    request_list.append(r)                                                       
                                                                                                 
        return (event_list, request_list)

    def put_result(self, _result):                                                              
        for appk, app_placement in _result.iteritems():                                          
            data = {                                                                             
                'stack_id': appk,                                                                
                'placement': json.dumps(app_placement)                                                       
            }                                                                                    
                                                                                                 
            self.music.create_row(self.config.db_keyspace, self.config.db_response_table, data)
                                                                                                 
        for appk in _result.keys(): 
            self.music.delete_row_eventually(self.config.db_keyspace, \
                                             self.config.db_request_table, \
                                             'stack_id', \
                                             appk)

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

        self.logger.info("resource status updated")

    def update_resource_log_index(self, _k, _index):
        self.music.delete_row_eventually(self.config.db_keyspace, \
                                         self.config.db_resource_index_table, \
                                         'site_name', _k)

        data = {                                                                                 
            'site_name': _k,     
            'resource_log_index': str(_index)                                                
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_resource_index_table, data)

    def update_app_log_index(self, _k, _index):
        self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_app_index_table, 'site_name', _k)

        data = {                                                                                 
            'site_name': _k,     
            'app_log_index': str(_index)                                                
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_app_index_table, data)

    def add_app(self, _k, _app_data):
        self.music.delete_row_eventually(self.config.db_keyspace, self.config.db_app_table, 'stack_id', _k)
        
        data = {                                                                                 
            'stack_id': _k,     
            'app': json.dumps(_app_data)                                               
        }                                                                                        
                                                                                                 
        self.music.create_row(self.config.db_keyspace, self.config.db_app_table, data)







