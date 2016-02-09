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


import sys


class Config:

    def __init__(self):
        self.mode = None

        self.logger_name = None
        self.logging_level = None
        self.logging_loc = None

        self.process = None

        self.rpc_server_ip = None
        self.rpc_server_port = 0

        self.datacenter_name = None

        self.keystone_url = None
        self.keystone_tenant_token_api = None
        self.keystone_project_token_api = None

        self.network_control = False
        self.network_control_api = None

        self.nova_url = None
        self.nova_host_resources_api = None
        self.nova_host_zones_api = None
        self.nova_host_aggregates_api = None
        self.nova_flavors_api = None

        self.vcpus_overbooking_per_core = 1
        self.memory_overbooking_ratio = 1
        self.disk_overbooking_ratio = 1

        self.topology_trigger_time = None
        self.topology_trigger_freq = 0
        self.compute_trigger_time = None
        self.compute_trigger_freq = 0

        self.db_keyspace = None

        self.control_loc = None

        self.project_name = None
        self.admin_tenant_name = None
        self.user_name = None
        self.pw = None

        #self.sim_duration = 0

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
        try:
            # TODO: Allow only admin to read
            f = open("./ostro.cfg", "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                if k == "mode":
                    self.mode = v.strip()
                elif k == "logger_name":
                    self.logger_name = v.strip()
                elif k == "logging_level":
                    self.logging_level = v.strip()
                elif k == "logging_loc":
                    self.logging_loc = v.strip()
                elif k == "process":
                    self.process = v.strip()
                elif k == "rpc_server_ip":
                    self.rpc_server_ip = v.strip()
                elif k == "rpc_server_port":
                    self.rpc_server_port = int(v.strip())
                elif k == "datacenter_name":
                    self.datacenter_name = v.strip()
                elif k == "keystone_url":
                    self.keystone_url = v.strip()
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
                    self.network_control_api = v.strip()
                elif k == "nova_url":
                    self.nova_url = v.strip()
                elif k == "nova_host_resources_api":
                    self.nova_host_resources_api = v.strip()
                elif k == "nova_host_zones_api":
                    self.nova_host_zones_api = v.strip()
                elif k == "nova_host_aggregates_api":
                    self.nova_host_aggregates_api = v.strip()
                elif k == "nova_flavors_api":
                    self.nova_flavors_api = v.strip()
                elif k == "vcpus_overbooking_per_core":
                    self.vcpus_overbooking_per_core = int(v.strip())
                elif k == "memory_overbooking_ratio":
                    self.memory_overbooking_ratio = float(v.strip())
                elif k == "local_disk_overbooking_ratio":
                    self.disk_overbooking_ratio = int(v.strip())
                elif k == "topology_trigger_time":
                    self.topology_trigger_time = v.strip()
                elif k == "topology_trigger_frequency":
                    self.topology_trigger_freq = int(v.strip())
                elif k == "compute_trigger_time":
                    self.compute_trigger_time = v.strip()
                elif k == "compute_trigger_frequency":
                    self.compute_trigger_freq = int(v.strip())
                elif k == "db_keyspace":
                    self.db_keyspace = v.strip()
                elif k == "control_loc":
                    self.control_loc = v.strip()
                elif k == "auth_loc":
                    status = self._set_authentication(v.strip())
                    if status != "success":
                        return status
                elif k == "sim_cfg_loc":
                    if self.mode.startswith("live") == False:
                        status = self._set_simulation(v.strip())
                        if status != "success":
                            return status

                line = f.readline()

            f.close()

            return "success"

        except IOError as e:
            return "I/O error({}): {}".format(e.errno, e.strerror)
        except:
            return "Unexpected error: ", sys.exc_info()[0]

    def _set_authentication(self, _loc):
        try:
            # TODO: Allow only admin to read
            f = open(_loc, "r")
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
            return "I/O error({}): {}".format(e.errno, e.strerror)
        except:
            return "Unexpected error: ", sys.exc_info()[0]

    def _set_simulation(self, _loc):
        try:
            f = open(_loc, "r")
            line = f.readline()

            while line:
                if line.startswith("#") or line.startswith(" ") or line == "\n":
                    line = f.readline()
                    continue

                (rk, v) = line.split("=")
                k = rk.strip()

                #if k == "sim_duration":
                    #self.sim_duration = int(v.strip())
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
            return "I/O error({}): {}".format(e.errno, e.strerror)
        except:
            return "Unexpected error: ", sys.exc_info()[0]



# Unit test
config = Config()
config.configure()
