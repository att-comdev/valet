#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Capture Host status and metadata from Nova
#
#################################################################################################################


import json
import pycurl
import StringIO
import sys

from resource_base import Host, LogicalGroup, Flavor
from authentication import Authentication

sys.path.insert(0, '../ostro_server')
from configuration import Config


class Compute:
  
    def __init__(self, _config, _admin_token, _project_token):
        self.config = _config
        self.admin_token = _admin_token
        self.project_token = _project_token

    def set_hosts(self, _hosts, _logical_groups):
        status = self._set_availability_zones(_hosts, _logical_groups)
        if status != "success":
            return status

        status = self._set_aggregates(_hosts, _logical_groups)
        if status != "success":
            return status

        status = self._set_placed_vms(_hosts, _logical_groups)
        if status != "success":
            return status

        status = self._set_resources(_hosts)
        if status != "success":
            return status

        return "success"

    def _set_availability_zones(self, _hosts, _logical_groups):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             self.config.nova_host_zones_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            hosts_info = json.loads(results)
            #print json.dumps(hosts_info, indent=4)
            host_list = hosts_info["hosts"]

            for h in host_list:
                if h["service"] == "compute":
                    host = Host(h["host_name"])
                    host.tag.append("nova")
     
                    logical_group = None
                    if h["zone"] not in _logical_groups.keys():
                        logical_group = LogicalGroup(h["zone"])
                        logical_group.group_type = "AZ"
                        _logical_groups[logical_group.name] = logical_group
                    else:
                        logical_group = _logical_groups[h["zone"]]

                    host.memberships[logical_group.name] = logical_group

                    if host.name not in logical_group.vms_per_host.keys():
                        logical_group.vms_per_host[host.name] = []

                    _hosts[host.name] = host

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host zones from Nova"

        return "success"

    def _set_aggregates(self, _hosts, _logical_groups):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             self.config.nova_host_aggregates_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            aggregates = json.loads(results)
            #print json.dumps(aggregates, indent=4)
            aggregate_list = aggregates["aggregates"]

            for a in aggregate_list:
                if a["deleted"] == "false":
                    aggregate = LogicalGroup(a["name"])
                    aggregate.group_type = "AGGR"
                    
                    metadata = {}
                    for mk, mv in a.metadata.iteritems():
                        metadata[mk] = mv
                    aggregate.metadata = metadata

                    _logical_groups[aggregate.name] = aggregate

                    for hn in a["hosts"]:
                        host = _hosts[hn]
                        host.memberships[aggregate.name] = aggregate

                        aggregate.vms_per_host[host.name] = []

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host aggregates from Nova"

        return "success"

    def _set_placed_vms(self, _hosts, _logical_groups):
        error_status = None

        for hk in _hosts.keys():
            vm_uuid_list = []
            result_status = self._get_vms_of_host(hk, vm_uuid_list)
        
            if result_status == "success":    
                for vm_uuid in vm_uuid_list:
                    vm_detail = []
                    result_status_detail = self._get_vm_detail(vm_uuid, vm_detail)
                
                    if result_status_detail == "success":
                        #if vm_detail[3] != "SHUTOFF":  # status == "ACTIVE" or "SUSPENDED"
                        vm_id = ("none", vm_detail[0], vm_uuid)
                        _hosts[hk].vm_list.append(vm_id)

                        _logical_groups[vm_detail[1]].vm_list.append(vm_id)
                        _logical_groups[vm_detail[1]].vms_per_host[hk].append(vm_id)
                    else:
                        error_status = result_status_detail
                        break
            else:
                error_status = result_status

            if error_status != None:
                break

        if error_status == None:
            return "success"
        else:
            return error_status

    def _get_vms_of_host(self, _hk, _vm_list):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             "/os-hypervisors/" + _hk + "/servers")
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            servers = json.loads(results)
            #print json.dumps(servers, indent=4)
            server_list = servers["hypervisors"][0]["servers"]
            for s in server_list:
                _vm_list.append(s["uuid"])

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting existing vms"

        return "success"

    def _get_vm_detail(self, _vm_uuid, _vm_detail):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             "/servers/" + _vm_uuid)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            server = json.loads(results)
            #print json.dumps(server, indent=4)
            vm_name = server["server"]["name"]
            _vm_detail.append(vm_name)
            az = server["server"]["OS-EXT-AZ:availability_zone"]
            _vm_detail.append(az)
            metadata = server["server"]["metadata"]
            _vm_detail.append(metadata)
            status = server["server"]["status"]
            _vm_detail.append(status)

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting vm detail"

        return "success"

    def _set_resources(self, _hosts):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             self.config.nova_host_resources_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            hosts_info = json.loads(results)
            #print json.dumps(hosts_info, indent=4)
            host_list = hosts_info["hypervisors"]

            for hv in host_list:
                if hv["service"]["host"] in _hosts.keys():
                    host = _hosts[hv["service"]["host"]]
                    host.status = hv["status"]
                    host.state = hv["state"]
                    host.vCPUs = hv["vcpus"] * self.config.vcpus_overbooking_per_core # TODO:
                    host.avail_vCPUs = host.vCPUs - hv["vcpus_used"]
                    host.mem_cap = float(hv["memory_mb"]) * self.config.memory_overbooking_ratio # TODO
                    host.avail_mem_cap = host.mem_cap - float(hv["memory_mb_used"])
                    host.local_disk_cap = hv["local_gb"] * self.config.disk_overbooking_ratio # TODO
                    host.avail_local_disk_cap = host.local_disk_cap - hv["local_gb_used"]

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host resources from Nova"

        return "success"

    def set_flavors(self, _flavors):
        error_status = None

        result_status = self._set_flavors(_flavors)

        if result_status == "success":
            for fk, f in _flavors.iteritems():
                result_status_detail = self._set_extra_specs(f)
                if result_status_detail != "success":
                    error_status = result_status_detail
                    break
        else:
            error_status = result_status

        if error_status == None:
            return "success"
        else:
            return error_status

    def _set_flavors(self, _flavors):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             self.config.nova_flavors_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            flavor_info = json.loads(results)
            #print json.dumps(flavor_info, indent=4)
            flavor_list = flavor_info["flavors"]

            for f in flavor_list:
                flavor = Flavor(f["name"])
                flavor.flavor_id = f["id"]
                flavor.vCPUs = f["vcpus"]
                flavor.mem_cap = f["ram"]
                flavor.disk_cap = f["disk"]

                _flavors[flavor.name] = flavor

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting flavors"

        return "success"

    def _set_extra_specs(self, _flavor):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + \
                             self.config.nova_version + \
                             str(self.project_token) + \
                             "/flavors/" + _flavor.flavor_id + "/os-extra_specs")
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            flavor_info = json.loads(results)
            #print json.dumps(flavor_info, indent=4)
            extra_specs = flavor_info["extra_specs"]

            for sk, sv in extra_specs.iteritems():
                _flavor.extra_specs[sk] = sv

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting flavor extra spec"

        return "success"



# Unit test
'''
if __name__ == '__main__':
    config = Config()
    config_status = config.configure()
    if config_status != "success":
        print "Error while configuring Ostro: " + config_status
        sys.exit(2)

    auth = Authentication()

    admin_token = auth.get_tenant_token(config)
    if admin_token == None:                                                             
        print "Error while getting admin_token"
        sys.exit(2)
    else:
        print "admin_token=",admin_token
                                                                                                 
    project_token = auth.get_project_token(config, admin_token)          
    if project_token == None:                                                           
        print "Error while getting project_token"
        sys.exit(2)
    else:
        print "project_token=",project_token
                      
    c = Compute(config, admin_token, project_token)

    hosts = {}
    logical_groups = {}
    flavors = {}

    #c._set_availability_zones(hosts, logical_groups)
    #c._set_aggregates(hosts, logical_groups)
    #c._set_placed_vms(hosts, logical_groups)
    #c._set_resources(hosts)
    c.set_flavors(flavors)
'''

