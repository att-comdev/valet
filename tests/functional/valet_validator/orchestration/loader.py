'''
Created on May 2, 2016

@author: Yael
'''

from heatclient.client import Client
import time
import traceback
from valet_validator.common import Result, General
from valet_validator.common.init import CONF
from valet_validator.common.auth import Auth
import json
import requests


class Loader(object):

    def __init__(self, config_file=None):
        '''
        initializing the loader - connecting to heat
        '''
        General.log_info("Initializing Loader")

        heat_url = CONF.heat.HEAT_URL + str(Auth.get_project_id())
        token = Auth.get_auth_token()

        heat = Client(CONF.heat.VERSION, endpoint=heat_url, token=token)
        self.stacks = heat.stacks


    def create_stack(self, stack_name, template_name, template_resources):
        General.log_info("Starting to create stacks")
        groups = template_resources.groups

        try:
            for key in groups:
                if groups[key].group_type == "exclusivity":
                    self.create_valet_group(groups[key].group_name)

            self.stacks.create(stack_name = stack_name, template = template_resources.template_data)
            return self.wait(stack_name, operation = "create")

        except Exception:
            General.log_error(traceback.format_exc())
            return Result(False, "Failed to create stack")


    def create_valet_group(self, group_name):
        try:
            group_url = "%s/groups" % CONF.nova.HOST

            headers =   {   "X-Auth-Token": Auth.get_auth_token(), 
                            "Content-Type": "application/json"   }

            grp_data =  {   "name": group_name,
                            "type": "exclusivity" }

            group_details = self.get_existing_groups(group_url, group_name, headers)
#           group_details[0] - group id
#           group_details[1] - group members

            if group_details == None:
                General.log_info("Creating group with member")
                create_response = requests.post(group_url, data=json.dumps(grp_data), headers=headers)
                General.log_info(create_response.json())
                group_details = create_response.json()["id"], create_response.json()["members"]
            else:
                General.log_info("Group exists")

            self.add_group_member(group_name, group_details, headers)
        except Exception:
            General.log_error("Failed to create valet group")
            General.log_error(traceback.format_exc())


    def add_group_member(self, group_name, group_details, headers):
        if Auth.get_project_id() not in group_details[1]:
            add_member_url = "%s/groups/%s/members" % (CONF.nova.HOST, group_details[0])
            member_data = {  "members": [ Auth.get_project_id() ]  }
            
            requests.put(add_member_url, data=json.dumps(member_data), headers=headers)


    def delete_stack(self, stack_name):
        self.stacks.delete(stack_id = stack_name)
        return self.wait(stack_name, operation = "delete")


    def delete_all_stacks(self):
        General.log_info("Starting to delete stacks")
        try:
            for stack in self.stacks.list():
                self.delete_stack(stack.id)
            
        except Exception:
            General.log_error("Failed to delete stacks")
            General.log_error(traceback.format_exc())


    def get_existing_groups(self, group_url, group_name, headers):
        list_response = requests.get(group_url, headers=headers)
        
        for grp in list_response.json()["groups"]:
            if grp["name"] == group_name:
                return grp["id"], grp["members"]
            
        return None


    def wait(self, stack_name, count = CONF.heat.TIME_CAP, operation = "Operation"):
        '''
        Checking the result of the process (create/delete) and writing the result to log 
        '''
        while str(self.stacks.get(stack_name).status) == "IN_PROGRESS" and count > 0:
            count -= 1
            time.sleep(1)

        if str(self.stacks.get(stack_name).status) == "COMPLETE":
            General.log_info(operation + " Successfully completed")
            return Result()
        elif str(self.stacks.get(stack_name).status) == "FAILED":
            msg = operation + " Failed  -  " + self.stacks.get(stack_name).stack_status_reason
        else:
            msg = operation + " timed out"
        General.log_error(msg)
        
        return Result(False, msg)


