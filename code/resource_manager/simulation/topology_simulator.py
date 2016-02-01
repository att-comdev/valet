#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Jan. 10, 2016
#
# Functions 
# - Simulate datacenter configurations (i.e., layout, cabling)
#
#################################################################################################################


from resource_base import HostGroup, Host, Switch, Link


class SimTopology():

    def __init__(self, _config):
        self.config = _config

    def set_topology(self, _datacenter, _host_groups, _hosts, _switches):
        if self.config.mode == "sim_xsmall":
            self._set_xsmall_topology(_datacenter, _host_groups, _hosts, _switches)
        #elif self.site_type == "sim_small":
            #self._set_small_topology(topology)
        #elif self.site_type == "sim_medium":
            #self._set_medium_topology(topology)
        #elif self.site_type == "sim_large":
            #self._set_large_topology(topology)

        return "success"

    def _set_xsmall_topology(self, _datacenter, _host_groups, _hosts, _switches):
        root_switch = Switch("r0")
        root_switch.switch_type = "root"
        _switches[root_switch.name] = root_switch

        for r_num in range(0, self.config.num_of_racks_in_xsmall):
            switch = Switch(root_switch.name + "t" + str(r_num))
            switch.switch_type = "ToR"
            _switches[switch.name] = switch

            for h_num in range(0, self.config.num_of_hosts_per_rack_in_xsmall):
                leaf_switch = Switch(switch.name + "l" + str(h_num))
                leaf_switch.switch_type = "leaf"
                _switches[leaf_switch.name] = leaf_switch

        for r_num in range(0, self.config.num_of_racks_in_xsmall):
            s = _switches[root_switch.name + "t" + str(r_num)]

            up_link = Link(s.name + "-" + root_switch.name)
            up_link.resource = root_switch
            up_link.nw_bandwidth = self.config.bandwidth_of_rack  
            up_link.avail_nw_bandwidth = up_link.nw_bandwidth
            s.up_links[up_link.name] = up_link

            if self.config.num_of_racks_in_xsmall > 1:
                ps = None
                if (r_num % 2) == 0:
                    if (r_num + 1) < self.config.num_of_racks_in_xsmall: 
                        ps = _switches[root_switch.name + "t" + str(r_num + 1)]       
                else:
                    ps = _switches[root_switch.name + "t" + str(r_num - 1)]
                if ps != None: 
                    peer_link = Link(s.name + "-" + ps.name)
                    peer_link.resource = ps
                    peer_link.nw_bandwidth = self.config.bandwidth_of_rack  
                    peer_link.avail_nw_bandwidth = peer_link.nw_bandwidth
                    s.peer_links[peer_link.name] = peer_link
      
            for h_num in range(0, self.config.num_of_hosts_per_rack_in_xsmall):
                ls = _switches[s.name + "l" + str(h_num)]

                l_up_link = Link(ls.name + "-" + s.name)
                l_up_link.resource = s
                l_up_link.nw_bandwidth = self.config.bandwidth_of_host
                l_up_link.avail_nw_bandwidth = l_up_link.nw_bandwidth
                ls.up_links[l_up_link.name] = l_up_link

        for r_num in range(0, self.config.num_of_racks_in_xsmall):
            host_group = HostGroup(_datacenter.name + "r" + str(r_num))
            host_group.host_type = "rack"
            switch = _switches[root_switch.name + "t" + str(r_num)]
            host_group.switches[switch.name] = switch
            _host_groups[host_group.name] = host_group

            for h_num in range(0, self.config.num_of_hosts_per_rack_in_xsmall):
                host = Host(host_group.name + "c" + str(h_num))
                leaf_switch = _switches[switch.name + "l" + str(h_num)]
                host.switches[leaf_switch.name] = leaf_switch
                _hosts[host.name] = host

        for r_num in range(0, self.config.num_of_racks_in_xsmall):
            host_group = _host_groups[_datacenter.name + "r" + str(r_num)]
            host_group.parent_resource = _datacenter
      
            for h_num in range(0, self.config.num_of_hosts_per_rack_in_xsmall):
                host = _hosts[host_group.name + "c" + str(h_num)]
                host.host_group = host_group

                host_group.child_resources[host.name] = host
            
        _datacenter.root_switches[root_switch.name] = root_switch

        for r_num in range(0, self.config.num_of_racks_in_xsmall):
            host_group = _host_groups[_datacenter.name + "r" + str(r_num)]
            _datacenter.resources[host_group.name] = host_group


