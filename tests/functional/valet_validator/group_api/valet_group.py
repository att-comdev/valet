'''
Created on Jul 3, 2016

@author: Yael
'''

from valet_validator.common.init import CONF
from valet_validator.common.auth import Auth
import requests
import json
import traceback
from valet_validator.common import General

class ValetGroup(object):

    def __init__(self):
        self.groups_url = "%s/groups" % CONF.nova.HOST
 
        self.headers = { "X-Auth-Token": Auth.get_auth_token(), 
                         "Content-Type": "application/json"  }
        
    
    def create_group(self, group_name, group_type):
        grp_data = { "name": group_name, "type": group_type }
        return requests.post(self.groups_url, data=json.dumps(grp_data), headers=self.headers)


    def get_list_groups(self):
        list_response = requests.get(self.groups_url, headers=self.headers)
        return list_response.json()["groups"]
        

    def get_group_details(self, group_id):
        url = self.groups_url + "/" + group_id
        return requests.get(url, headers=self.headers)
    
    def update_group_members(self, group_id, members = None):
        add_member_url = self.groups_url + "/%s/members" % group_id
        data = json.dumps( {"members": [members or Auth.get_project_id()]})

        return requests.put(add_member_url, data=data, headers=self.headers)
        
        
    def update_group(self, group_id, new_description):
        url = self.groups_url + "/" + group_id
        new_data = json.dumps( {"description": new_description})
                
        return requests.put(url, new_data, headers=self.headers)
        

    def delete_group_member(self, group_id, member_id):
        url = self.groups_url + "/%s/members/%s" % (group_id, member_id)
        return requests.delete(url, headers=self.headers)


    def delete_all_group_member(self, group_id):
        url = self.groups_url + "/%s/members" % group_id
        return requests.delete(url, headers=self.headers)


    def delete_group(self, group_id):
        url = self.groups_url + "/%s" % group_id
        return requests.delete(url, headers=self.headers)




    def get_group_id_and_members(self, group_name, group_type = "exclusivity"):
        '''
        Checks if group name exists, if not - creates it
        returns group's id and members list
        '''
        group_details = self.check_group_exists(group_name)

        if group_details == None:
            General.log_info("Creating group")
            create_response = self.create_group(group_name, group_type)
            return create_response.json()["id"], create_response.json()["members"]
        else:
            General.log_info("Group exists")

        return group_details
     
     
    def add_group_member(self, group_details, members = None):
        '''
        Checks if member exists in group, if not - adds it
        '''
        # group_details - group id, group members
        try:
            if Auth.get_project_id() not in group_details[1]:
                General.log_info("Adding member to group")
                self.update_group_members(group_details[0])
        except Exception:
            General.log_error("Failed to add group member", traceback.format_exc())
            

    def check_group_exists(self, group_name):
        '''
        Checks if group exists in group list, if not returns None
        '''
        for grp in self.get_list_groups(group_name):
            if grp["name"] == group_name:
                return grp["id"], grp["members"]

        return None
    

    def delete_all_groups(self):
        DELETED = 204
        for group in self.get_list_groups():
            codes = [self.delete_all_group_member(group["id"]).status_code, self.delete_group(group["id"]).status_code]
            
            res = filter(lambda a: a != DELETED, codes)
            if res:
                return res[0]
            
        return DELETED
            

    
    
    
    
    
    