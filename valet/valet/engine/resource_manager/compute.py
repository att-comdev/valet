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
from valet.engine.resource_manager.resource_base import Host, LogicalGroup, Flavor


class Compute(object):

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
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + self.config.nova_host_zones_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            hosts_info = json.loads(results)
            # print json.dumps(hosts_info, indent=4)
            if "hosts" in hosts_info.keys():
                host_list = hosts_info["hosts"]

                for h in host_list:
                    if "service" in h.keys():
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
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + self.config.nova_host_aggregates_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            aggregates = json.loads(results)
            # print json.dumps(aggregates, indent=4)
            if "aggregates" in aggregates.keys():
                aggregate_list = aggregates["aggregates"]

                for a in aggregate_list:
                    aggregate = LogicalGroup(a["name"])
                    aggregate.group_type = "AGGR"
                    if a["deleted"] is not False:
                        aggregate.status = "disabled"

                    metadata = {}
                    for mk in a["metadata"].keys():
                        metadata[mk] = a["metadata"][mk]
                    aggregate.metadata = metadata

                    _logical_groups[aggregate.name] = aggregate

                    for hn in a["hosts"]:
                        host = _hosts[hn]
                        host.memberships[aggregate.name] = aggregate

                        aggregate.vms_per_host[host.name] = []

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host aggregates from Nova"

        return "success"

    # NOTE: do not set any info in _logical_groups
    def _set_placed_vms(self, _hosts, _logical_groups):
        error_status = None

        for hk in _hosts.keys():
            vm_uuid_list = []
            result_status = self._get_vms_of_host(hk, vm_uuid_list)

            if result_status == "success":
                for vm_uuid in vm_uuid_list:
                    vm_detail = []    # (vm_name, az, metadata, status)
                    result_status_detail = self._get_vm_detail(vm_uuid, vm_detail)

                    if result_status_detail == "success":
                        # if vm_detail[3] != "SHUTOFF":  # status == "ACTIVE" or "SUSPENDED"
                        vm_id = ("none", vm_detail[0], vm_uuid)
                        _hosts[hk].vm_list.append(vm_id)

                        # _logical_groups[vm_detail[1]].vm_list.append(vm_id)
                        # _logical_groups[vm_detail[1]].vms_per_host[hk].append(vm_id)
                    else:
                        error_status = result_status_detail
                        break
            else:
                error_status = result_status

            if error_status is not None:
                break

        if error_status is None:
            return "success"
        else:
            return error_status

    def _get_vms_of_host(self, _hk, _vm_list):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + "/os-hypervisors/" + _hk + "/servers")
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            servers = json.loads(results)
            # print json.dumps(servers, indent=4)
            if "hypervisors" in servers.keys():
                hypervisor_list = servers["hypervisors"]
                for hv in hypervisor_list:
                    if "servers" in hv.keys():
                        server_list = hv["servers"]
                        for s in server_list:
                            _vm_list.append(s["uuid"])

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting existing vms"

        return "success"

    def _get_vm_detail(self, _vm_uuid, _vm_detail):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + "/servers/" + _vm_uuid)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.HTTPGET, 1)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            server = json.loads(results)
            # print json.dumps(server, indent=4)
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
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + self.config.nova_host_resources_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            hosts_info = json.loads(results)
            # print json.dumps(hosts_info, indent=4)
            host_list = hosts_info["hypervisors"]

            for hv in host_list:
                if hv["service"]["host"] in _hosts.keys():
                    host = _hosts[hv["service"]["host"]]
                    host.status = hv["status"]
                    host.state = hv["state"]
                    host.original_vCPUs = float(hv["vcpus"])
                    host.vCPUs_used = float(hv["vcpus_used"])
                    host.original_mem_cap = float(hv["memory_mb"])
                    host.free_mem_mb = float(hv["free_ram_mb"])
                    host.original_local_disk_cap = float(hv["local_gb"])
                    host.free_disk_gb = float(hv["free_disk_gb"])
                    host.disk_available_least = float(hv["disk_available_least"])

        except (ValueError, KeyError, TypeError):
            return "JSON format error while setting host resources from Nova"

        return "success"

    def set_flavors(self, _flavors):
        error_status = None

        result_status = self._set_flavors(_flavors)

        if result_status == "success":
            for _, f in _flavors.iteritems():
                result_status_detail = self._set_extra_specs(f)
                if result_status_detail != "success":
                    error_status = result_status_detail
                    break
        else:
            error_status = result_status

        if error_status is None:
            return "success"
        else:
            return error_status

    def _set_flavors(self, _flavors):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + self.config.nova_flavors_api)
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            flavor_info = json.loads(results)
            # print json.dumps(flavor_info, indent=4)
            flavor_list = flavor_info["flavors"]

            for f in flavor_list:
                flavor = Flavor(f["name"])
                flavor.flavor_id = f["id"]
                if "OS-FLV-DISABLED:disabled" in f.keys():
                    if f["OS-FLV-DISABLED:disabled"] is not False:
                        flavor.status = "disabled"

                flavor.vCPUs = float(f["vcpus"])
                flavor.mem_cap = float(f["ram"])

                root_gb = float(f["disk"])

                ephemeral_gb = 0.0
                if "OS-FLV-EXT-DATA:ephemeral" in f.keys():
                    ephemeral_gb = float(f["OS-FLV-EXT-DATA:ephemeral"])

                swap_mb = 0.0
                if "swap" in f.keys():
                    if f["swap"] != '':
                        swap_mb = float(f["swap"])

                flavor.disk_cap = root_gb + ephemeral_gb + swap_mb / float(1024)

                _flavors[flavor.name] = flavor

        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting flavors"

        return "success"

    def _set_extra_specs(self, _flavor):
        buf = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.config.nova_url + self.config.nova_version + str(self.project_token) + "/flavors/" + _flavor.flavor_id + "/os-extra_specs")
        c.setopt(pycurl.HTTPHEADER, ["X-Auth-Token: " + str(self.admin_token)])
        c.setopt(pycurl.POST, 0)
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        c.perform()
        results = buf.getvalue()
        buf.close()

        try:
            flavor_info = json.loads(results)
            # print json.dumps(flavor_info, indent=4)
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
    if admin_token is None:
        print "Error while getting admin_token"
        sys.exit(2)
    else:
        print "admin_token=",admin_token

    project_token = auth.get_project_token(config, admin_token)
    if project_token is None:
        print "Error while getting project_token"
        sys.exit(2)
    else:
        print "project_token=",project_token

    c = Compute(config, admin_token, project_token)

    hosts = {}
    logical_groups = {}
    flavors = {}

    #c._set_availability_zones(hosts, logical_groups)
    #c._set_aggregates(None, logical_groups)
    #c._set_placed_vms(hosts, logical_groups)
    #c._get_vms_of_host("qos101", None)
    #c._get_vm_detail("20b2890b-81bb-4942-94bf-c6bee29630bb", None)
    c._set_resources(hosts)
    #c._set_flavors(flavors)
'''
