#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Simulate hosts and flavors
#
#################################################################################################################


from resource_base import Host, LogicalGroup, Flavor


class SimCompute():
  
    def __init__(self, _config):
        self.config = _config

    def set_hosts(self, _hosts, _logical_groups):
        self._set_availability_zones(_hosts, _logical_groups)

        self._set_aggregates(_hosts, _logical_groups)

        self._set_resources(_hosts)

        self._set_placed_vms(_hosts, _logical_groups)

        return "success"

    def _set_availability_zones(self, _hosts, _logical_groups):
        num_of_non_compute_racks = self.config.num_of_racks / 2
        num_of_non_compute_hosts = 0
        if num_of_non_compute_racks == 0:
            num_of_non_compute_hosts = self.config.num_of_hosts_per_rack / 2 
        
        for r_num in range(0, self.config.num_of_racks):
            if num_of_non_compute_racks > 0 and r_num < num_of_non_compute_racks:
                continue

            for h_num in range(0, self.config.num_of_hosts_per_rack):
                if num_of_non_compute_hosts > 0 and h_num < num_of_non_compute_hosts:
                    continue
        
                host = Host(self.config.mode + "r" + str(r_num) + "c" + str(h_num))
                host.tag.append("nova")
 
                logical_group = LogicalGroup("nova")
                logical_group.group_type = "AZ"
                _logical_groups[logical_group.name] = logical_group

                host.memberships[logical_group.name] = logical_group

                _hosts[host.name] = host

    def _set_aggregates(self, _hosts, _logical_groups):
        for a_num in range(0, self.config.num_of_aggregates):
            metadata = {}
            #metadata["availability_zone"] = "nova"
            metadata["aggregate_sim"] = str(a_num)
        
            aggregate = LogicalGroup("aggregate" + str(a_num))
            aggregate.group_type = "AGGR"
            aggregate.metadata = metadata
        
            _logical_groups[aggregate.name] = aggregate

        for a_num in range(0, self.config.num_of_aggregates):
            aggregate = _logical_groups["aggregate" + str(a_num)]
            for r_num in range(0, self.config.num_of_racks):
                for h_num in range(0, self.config.num_of_hosts_per_rack):
                    host_name = self.config.mode + "r" + str(r_num) + "c" + str(h_num)
                    if host_name in _hosts.keys():
                        if (h_num % (self.config.aggregated_ratio + a_num)) == 0:
                            host = _hosts[host_name]
                            host.memberships[aggregate.name] = aggregate

    def _set_resources(self, _hosts):
        for r_num in range(0, self.config.num_of_racks):
            for h_num in range(0, self.config.num_of_hosts_per_rack):
                host_name = self.config.mode + "r" + str(r_num) + "c" + str(h_num)
                if host_name in _hosts.keys():
                    host = _hosts[host_name]
                    host.vCPUs = self.config.cpus_per_host * self.config.vcpus_overbooking_per_core 
                    host.avail_vCPUs = host.vCPUs
                    host.mem_cap = float(self.config.mem_per_host) * self.config.memory_overbooking_ratio
                    host.avail_mem_cap = host.mem_cap
                    host.local_disk_cap = self.config.disk_per_host * self.config.disk_overbooking_ratio
                    host.avail_local_disk_cap = host.local_disk_cap

    def _set_placed_vms(self, _hosts, _logical_hosts):
        pass

    def set_flavors(self, _flavors):
        for f_num in range(0, self.config.num_of_basic_flavors):
            flavor = Flavor("bflavor" + str(f_num))
            flavor.vCPUs = self.config.base_flavor_cpus * (f_num + 1)
            flavor.mem_cap = self.config.base_flavor_mem * (f_num + 1)
            flavor.disk_cap = self.config.base_flavor_disk * (f_num + 1)
 
            _flavors[flavor.name] = flavor

        for a_num in range(0, self.config.num_of_aggregates):
            flavor = Flavor("sflavor" + str(a_num))
            flavor.vCPUs = self.config.base_flavor_cpus * (a_num + 1)
            flavor.mem_cap = self.config.base_flavor_mem * (a_num + 1)
            flavor.disk_cap = self.config.base_flavor_disk * (a_num + 1)

            #flavor.extra_specs["availability_zone"] = "nova"
            flavor.extra_specs["aggregate_sim"] = str(a_num)

            _flavors[flavor.name] = flavor

        return "success"
            




