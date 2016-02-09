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

from resource_base import Host, LogicalGroup, Flavor


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

        status = self._set_resources(_hosts)
        if status != "success":
            return status

        status = self._set_placed_vms(_hosts, _logical_groups)
        if status != "success":
            return status

        return "success"

    # TODO: for logical_group, just check if there is new one or deleted one
    def _set_availability_zones(self, _hosts, _logical_groups):
        hosts_info = ""

        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.nova_url + \
                             self.nova_version + \
                             str(self.project_token) + \
                             self.nova_host_zones_api)
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
                    if h["host_name"] in self.resource.hosts.keys():
                        host = self.resource.hosts[h["host_name"]]
                        if host.zone != h["zone"]:
                            #host.last_metadata_update = time.time()

                            self.logger.warn("host (" + host.name + ") updated (zone updated)")
                            host.zone = h["zone"]

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host zones from Nova"

        return "success"

    # TODO: for logical_group, just check if there is new one or deleted one
    def _set_aggregates(self, _hosts, _logical_groups):
        aggregates = ""

        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.nova_url + \
                             self.nova_version + \
                             str(self.project_token) + \
                             self.nova_host_aggregates_api)
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

            for aggregate in aggregate_list:
                print name
                # deleted != false
                # host_list
                # availability_zone?

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host aggregates from Nova"

        return "success"

    # TODO
    def _set_resources(self, _hosts):
        host_list = ""

        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.nova_url + \
                             self.nova_version + \
                             str(self.project_token) + \
                             self.nova_host_resources_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        hosts = {}

        try:
            hosts_info = json.loads(results)
            #print json.dumps(hosts_info, indent=4)
            host_list = hosts_info["hypervisors"]

            for hv in host_list:
                host = Host(hv["service"]["host"])
                host.tag.append("nova")
                host.status = hv["status"]
                host.state = hv["state"]
                host.vCPUs = hv["vcpus"] * self.config.vcpus_overbooking_per_core # TODO: need to verify
                host.avail_vCPUs = host.vCPUs - hv["vcpus_used"]
                host.mem_cap = float(hv["memory_mb"]) * self.config.memory_overbooking_ratio # TODO
                host.avail_mem_cap = host.mem_cap - float(hv["memory_mb_used"])
                host.local_disk_cap = hv["local_gb"] * self.config.local_disk_overbooking_ratio # TODO
                host.avail_local_disk_cap = host.local_disk_cap - hv["local_gb_used"]

                hosts[host.name] = host

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host resources from Nova"

        return "success"

    # TODO: after checking vms, if all vms are delted from EX logical groups, delete them
    def _set_placed_vms(self, _hosts, _logical_groups):
        host_list = ""

        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.nova_url + "v2/" + str(self.project_token) + \
                 "/os-hypervisors" + "/cirrus205/servers")
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            host_list = json.loads(results)
            #print json.dumps(host_list, indent=4)
        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting vms placed in each host from Nova"

        return "success"

    # TODO
    def set_flavors(self, _flavors):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.nova_url + \
                             self.nova_version + \
                             str(self.project_token) + \
                             self.nova_flavors_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            flavor_info = json.loads(results)
            #print json.dumps(self.flavor_info, indent=4)
            flavor_list = flavor_info["flavors"]

            for f in flavor_list:
                if f["name"] in self.resource.flavors.keys():
                    flavor = self.resource.flavors[f["name"]]
                    if f["vcpus"] != flavor.vCPUs or \
                       f["ram"] != flavor.mem_cap or \
                       f["disk"] != flavor.disk_cap:
                        flavor.vCPUs = f["vcpus"]
                        flavor.mem_cap = f["ram"]
                        flavor.disk_cap = f["disk"]

                        flavor.last_update = time.time()

                        self.logger.warn("flavor (" + flavor.name + ") updated")
                else:
                    flavor = Flavor(f["name"])
                    flavor.vCPUs = f["vcpus"]
                    flavor.mem_cap = f["ram"]
                    flavor.disk_cap = f["disk"]

                    flavor.last_update = time.time()

                    self.logger.warn("new flavor (" + flavor.name + ") added")

                    self.resource.flavors[flavor.name] = flavor

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting flavors"

        return "success"



