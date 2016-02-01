#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Oct. 15, 2015

# NOTE:
# - Track Keystone versions
#################################################################################################################


import sys
import pycurl
import json
import StringIO


class Authentication:

    def __init__(self):
        self.status = "success"

    def get_tenant_token(self, _config):
        in_data = json.dumps({"auth": {"tenantName": _config.admin_tenant_name, \
                                       "passwordCredentials": {"username": _config.user_name, \
                                                               "password": _config.password}}})
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        keystone_url = _config.keystone_url + _config.keystone_tenant_token_api
        c.setopt(pycurl.URL, keystone_url)
        c.setopt(pycurl.HTTPHEADER, ["Content-Type: application/json", "Accept: application/jso"])
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, in_data)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        authentication_result = buf.getvalue()
        buf.close()

        token_id = ""
        try:
            decoded = json.loads(authentication_result)
            #print json.dumps(decoded, indent=4)
            token_id = decoded["access"]["token"]["id"]
        except (ValueError, KeyError, TypeError):
            self.status =  "JSON format error while getting token id"
            return None

        return token_id

    def get_project_token(self, _config, _admin_token):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        keystone_url = _config.keystone_url + _config.keystone_project_token_api
        c.setopt(pycurl.URL, keystone_url)
        c.setopt(pycurl.HTTPHEADER, ["User-Agent: python-keystoneclient", "X-Auth-Token: " + str(_admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        projects_result = buf.getvalue()
        buf.close()

        project_id = None
        try:
            decoded = json.loads(projects_result)
            #print json.dumps(decoded, indent=4)
            elements = decoded["projects"]
            for e in elements:
                if e["name"] == _project_name:
                    project_id = e["id"]
        except (ValueError, KeyError, TypeError):
            self.status = "JSON format error while getting project token"
            return None

        return project_id

    #def get_tenant_tokens(self, _keystone_url, _token_id):
        #buf = StringIO.StringIO()
        #c = pycurl.Curl()
        #c.setopt(pycurl.URL, _keystone_url + "tenants")
        #c.setopt(pycurl.HTTPHEADER, ["User-Agent: python-keystoneclient", "X-Auth-Token: " + str(_token_id)])
        #c.setopt(pycurl.POST, 0)
        #c.setopt(pycurl.WRITEFUNCTION, buf.write)
        #c.perform()
        #tenants_result = buf.getvalue()
        #buf.close()
        #tenant_ids = []
        #try:
            #decoded = json.loads(tenants_result)
            #print json.dumps(decoded, indent=4)
            #elements = decoded["tenants"]
            #for e in elements:
                #tenant_ids.append(e["id"])
        #except (ValueError, KeyError, TypeError):
            #self.status = "JSON format error while getting tenants"
            #return None
        #return tenant_ids


## Test ##
