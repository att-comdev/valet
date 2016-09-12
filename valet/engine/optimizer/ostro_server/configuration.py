#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions
# - Set all configurations to run Ostro
#
#################################################################################################################


import os
import sys


class Config(object):

    def __init__(self, config_file_name="ostro.cfg"):

        # System parameters
        self.config_file_name = config_file_name
        self.root_loc = None

        self.mode = None

        self.process = None

        self.control_loc = None

        self.api_proc = None

        self.keystone_url = None
        self.keystone_tenant_token_api = None
        self.keystone_project_token_api = None

        self.nova_url = None
        self.nova_version = None
        self.nova_host_resources_api = None
        self.nova_host_zones_api = None
        self.nova_host_aggregates_api = None
        self.nova_flavors_api = None

        self.network_control = False
        self.network_control_api = None

        self.db_keyspace = None
        self.db_request_table = None
        self.db_response_table = None
        self.db_event_table = None
        self.db_resource_table = None
        self.db_app_table = None
        self.db_resource_index_table = None
        self.db_app_index_table = None
        self.db_uuid_table = None
        self.replication_factor = 0
        self.db_hosts = []

        self.ip = None

        self.priority = 0

        self.rpc_server_ip = None
        self.rpc_server_port = 0

        # Logging parameters
        self.logger_name = None
        self.logging_level = None
        self.logging_loc = None

        self.resource_log_loc = None
        self.app_log_loc = None
        self.max_main_log_size = 0
        self.max_log_size = 0
        self.max_num_of_logs = 0

        # Management parameters
        self.datacenter_name = None

        self.num_of_region_chars = 0
        self.rack_code_list = []
        self.node_code_list = []

        self.topology_trigger_time = None
        self.topology_trigger_freq = 0
        self.compute_trigger_time = None
        self.compute_trigger_freq = 0

        self.default_cpu_allocation_ratio = 1
        self.default_ram_allocation_ratio = 1
        self.default_disk_allocation_ratio = 1

        self.static_cpu_standby_ratio = 0
        self.static_mem_standby_ratio = 0
        self.static_local_disk_standby_ratio = 0

        # Authentication parameters
        self.auth_loc = None
        self.project_name = None
        self.admin_tenant_name = None
        self.user_name = None
        self.pw = None

        # Simulation parameters
        self.sim_cfg_loc = None

        self.num_of_hosts_per_rack = 0
        self.num_of_racks = 0
        self.num_of_spine_switches = 0
        self.num_of_aggregates = 0
        self.aggregated_ratio = 0

        self.cpus_per_host = 0
        self.mem_per_host = 0
        self.disk_per_host = 0
        self.bandwidth_of_spine = 0
        self.bandwidth_of_rack = 0
        self.bandwidth_of_host = 0

        self.num_of_basic_flavors = 0
        self.base_flavor_cpus = 0
        self.base_flavor_mem = 0
        self.base_flavor_disk = 0

    def configure(self):
        status = self._configure_system()

        if status != "success":
            return status

        self.sim_cfg_loc = self.root_loc + self.sim_cfg_loc
        self.auth_loc = self.root_loc + self.auth_loc
        self.process = self.root_loc + self.process
        self.logging_loc = self.root_loc + self.logging_loc
        self.resource_log_loc = self.root_loc + self.resource_log_loc
        self.app_log_loc = self.root_loc + self.app_log_loc

        self.keystone_url = self.api_proc + self.control_loc + self.keystone_url
        self.nova_url = self.api_proc + self.control_loc + self.nova_url
        self.network_control_api = self.api_proc + self.control_loc + self.network_control_api

        status = self._set_authentication()
        if status != "success":
            return status

        if self.mode.startswith("live") is False:
            status = self._set_simulation()
            if status != "success":
                return status

        return "success"

    def _configure_system(self):
        try:
            config_path = os.path.dirname(os.path.realpath(__file__))
            f = open(config_path + "/" + self.config_file_name, "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                if k == "root_loc":
                    self.root_loc = os.path.dirname(os.path.realpath(config_path + "/" + v.strip()))
                elif k == "mode":
                    self.mode = v.strip()
                elif k == "priority":
                    self.priority = v.strip()
                elif k == "logger_name":
                    self.logger_name = v.strip()
                elif k == "logging_level":
                    self.logging_level = v.strip()
                elif k == "logging_loc":
                    self.logging_loc = v.strip()
                elif k == "resource_log_loc":
                    self.resource_log_loc = v.strip()
                elif k == "app_log_loc":
                    self.app_log_loc = v.strip()
                elif k == "max_main_log_size":
                    self.max_main_log_size = int(v.strip())
                elif k == "max_log_size":
                    self.max_log_size = int(v.strip())
                elif k == "max_num_of_logs":
                    self.max_num_of_logs = int(v.strip())
                elif k == "process":
                    self.process = v.strip()
                elif k == "rpc_server_ip":
                    self.rpc_server_ip = v.strip()
                elif k == "rpc_server_port":
                    self.rpc_server_port = int(v.strip())
                elif k == "datacenter_name":
                    self.datacenter_name = v.strip()
                elif k == "keystone_url":
                    self.keystone_url = ':' + v.strip()
                elif k == "keystone_tenant_token_api":
                    self.keystone_tenant_token_api = v.strip()
                elif k == "keystone_project_token_api":
                    self.keystone_project_token_api = v.strip()
                elif k == "network_control":
                    control = v.strip()
                    if control == "yes":
                        self.network_control = True
                    else:
                        self.network_control = False
                elif k == "network_control_api":
                    self.network_control_api = ':' + v.strip()
                elif k == "nova_url":
                    self.nova_url = ':' + v.strip()
                elif k == "nova_version":
                    self.nova_version = v.strip()
                elif k == "nova_host_resources_api":
                    self.nova_host_resources_api = v.strip()
                elif k == "nova_host_zones_api":
                    self.nova_host_zones_api = v.strip()
                elif k == "nova_host_aggregates_api":
                    self.nova_host_aggregates_api = v.strip()
                elif k == "nova_flavors_api":
                    self.nova_flavors_api = v.strip()
                elif k == "default_cpu_allocation_ratio":
                    self.default_cpu_allocation_ratio = int(v.strip())
                elif k == "default_ram_allocation_ratio":
                    self.default_ram_allocation_ratio = float(v.strip())
                elif k == "default_disk_allocation_ratio":
                    self.default_disk_allocation_ratio = int(v.strip())
                elif k == "static_cpu_standby_ratio":
                    self.static_cpu_standby_ratio = int(v.strip())
                elif k == "static_mem_standby_ratio":
                    self.static_mem_standby_ratio = int(v.strip())
                elif k == "static_local_disk_standby_ratio":
                    self.static_local_disk_standby_ratio = int(v.strip())
                elif k == "topology_trigger_time":
                    self.topology_trigger_time = v.strip()
                elif k == "topology_trigger_frequency":
                    self.topology_trigger_freq = float(v.strip())
                elif k == "compute_trigger_time":
                    self.compute_trigger_time = v.strip()
                elif k == "compute_trigger_frequency":
                    self.compute_trigger_freq = float(v.strip())
                elif k == "db_keyspace":
                    self.db_keyspace = v.strip()
                elif k == "db_request_table":
                    self.db_request_table = v.strip()
                elif k == "db_response_table":
                    self.db_response_table = v.strip()
                elif k == "db_event_table":
                    self.db_event_table = v.strip()
                elif k == "db_resource_table":
                    self.db_resource_table = v.strip()
                elif k == "db_app_table":
                    self.db_app_table = v.strip()
                elif k == "db_resource_index_table":
                    self.db_resource_index_table = v.strip()
                elif k == "db_app_index_table":
                    self.db_app_index_table = v.strip()
                elif k == "db_uuid_table":
                    self.db_uuid_table = v.strip()
                elif k == "replication_factor":
                    self.replication_factor = int(v.strip())
                elif k == "db_hosts":
                    hl = v.strip().split(",")
                    for h in hl:
                        self.db_hosts.append(h)
                elif k == "ip":
                    self.ip = v.strip()
                elif k == "control_loc":
                    self.control_loc = v.strip()
                elif k == "api_proc":
                    self.api_proc = v.strip()
                    if self.api_proc == "http":
                        self.api_proc = self.api_proc + "://"
                elif k == "num_of_region_chars":
                    self.num_of_region_chars = int(v.strip())
                elif k == "rack_code_list":
                    rcl = v.strip().split(",")
                    for rc in rcl:
                        self.rack_code_list.append(rc)
                elif k == "node_code_list":
                    ncl = v.strip().split(",")
                    for nc in ncl:
                        self.node_code_list.append(nc)
                elif k == "auth_loc":
                    self.auth_loc = v.strip()
                elif k == "sim_cfg_loc":
                    self.sim_cfg_loc = v.strip()

                line = f.readline()

            f.close()

            return "success"

        except IOError as e:
            return "I/O error({}): {} while parsing system parameters".format(e, e.errno, e.strerror)
        except Exception as e:
            return "Unexpected error while parsing system parameters: %s" % e

    def _set_authentication(self):
        try:
            f = open(self.auth_loc, "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                if k == "project_name":
                    self.project_name = v.strip()
                elif k == "admin_tenant_name":
                    self.admin_tenant_name = v.strip()
                elif k == "user_name":
                    self.user_name = v.strip()
                elif k == "password":
                    self.pw = v.strip()

                line = f.readline()

            f.close()

            return "success"
        except IOError as e:
            return "I/O error({}): {} while parsing authentication parameters".format(e.errno, e.strerror)
        except Exception as e:
            return "Unexpected error while parsing authentication parameters: %s" % e

    def _set_simulation(self):
        try:
            f = open(self.sim_cfg_loc, "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                if k == "num_of_spine_switches":
                    self.num_of_spine_switches = int(v.strip())
                elif k == "num_of_hosts_per_rack":
                    self.num_of_hosts_per_rack = int(v.strip())
                elif k == "num_of_racks":
                    self.num_of_racks = int(v.strip())
                elif k == "num_of_aggregates":
                    self.num_of_aggregates = int(v.strip())
                elif k == "aggregated_ratio":
                    self.aggregated_ratio = int(v.strip())
                elif k == "cpus_per_host":
                    self.cpus_per_host = int(v.strip())
                elif k == "mem_per_host":
                    self.mem_per_host = int(v.strip())
                elif k == "disk_per_host":
                    self.disk_per_host = int(v.strip())
                elif k == "bandwidth_of_spine":
                    self.bandwidth_of_spine = int(v.strip())
                elif k == "bandwidth_of_rack":
                    self.bandwidth_of_rack = int(v.strip())
                elif k == "bandwidth_of_host":
                    self.bandwidth_of_host = int(v.strip())
                elif k == "num_of_basic_flavors":
                    self.num_of_basic_flavors = int(v.strip())
                elif k == "base_flavor_cpus":
                    self.base_flavor_cpus = int(v.strip())
                elif k == "base_flavor_mem":
                    self.base_flavor_mem = int(v.strip())
                elif k == "base_flavor_disk":
                    self.base_flavor_disk = int(v.strip())

                line = f.readline()

            f.close()

            return "success"
        except IOError as e:
            return "I/O error({}): {} while parsing simulation parameters".format(e.errno, e.strerror)
        except Exception:
            return "Unexpected error while parsing simulation parameters: ", sys.exc_info()[0]


# Unit test
'''
if __name__ == '__main__':
    config = Config()

    status = config.configure()
    if status != "success":
        print status
        exit(2)

    print "sim_cfg_loc=",config.sim_cfg_loc

    print "process_loc=",config.process

    print "keystone_url=",config.keystone_url
    print "nova_url=",config.nova_url
    print "network=",config.network_control_api

    print "rack codes"
    for rc in config.rack_code_list:
        print "    rc=",rc

    print "node codes"
    for nc in config.node_code_list:
        print "    nc=",nc
'''
