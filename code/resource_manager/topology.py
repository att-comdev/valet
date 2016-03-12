#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Capture datacenter configuration and layout including networking
#
#################################################################################################################


import copy
import sys

from resource_base import HostGroup, Switch, Link


class Topology:

    def __init__(self, _config):
        self.config = _config

    # Triggered by rhosts change
    def set_topology(self, _datacenter, _host_groups, _hosts, _rhosts, _switches):
        result_status = self._set_host_topology(_datacenter, _host_groups, _hosts, _rhosts)
        if result_status != "success":
            return result_status
            
        result_status = self._set_network_topology(_datacenter, _host_groups, _hosts, _switches)
        if result_status != "success":
            return result_status

        return "success"

    def _set_host_topology(self, _datacenter, _host_groups, _hosts, _rhosts):
        for rhk, rh in _rhosts.iteritems():
            h = copy.deepcopy(rh)

            if "infra" not in h.tag:
                h.tag.append("infra")

            # TODO: naming convention
            if (_datacenter.name + "r0") not in _host_groups.keys():
                host_group = HostGroup(_datacenter.name + "r0")                          
                host_group.host_type = "rack"                                                        
                _host_groups[host_group.name] = host_group

            h.host_group = _host_groups[_datacenter.name + "r0"]

            _hosts[h.name] = h

        for hgk, hg in _host_groups.iteritems():
            hg.parent_resource = _datacenter

            # TODO: naming convention
            for hk, h in _hosts.iteritems():
                hg.child_resources[h.name] = h

            _datacenter.resources[hgk] = hg

        return "success"

    # NOTE: this is just muck-ups
    def _set_network_topology(self, _datacenter, _host_groups, _hosts, _switches):
        root_switch = Switch(_datacenter.name)
        root_switch.switch_type = "root"

        _datacenter.root_switches[root_switch.name] = root_switch
        _switches[root_switch.name] = root_switch

        for hgk, hg in _host_groups.iteritems():
            switch = Switch(hgk)
            switch.switch_type = "ToR"

            up_link = Link(hgk + "-" + _datacenter.name)
            up_link.resource = root_switch
            up_link.nw_bandwidth = sys.maxint
            up_link.avail_nw_bandwidth = up_link.nw_bandwidth
            switch.up_links[up_link.name] = up_link

            hg.switches[switch.name] = switch
            _switches[switch.name] = switch

            for hk, h in hg.child_resources.iteritems():
                leaf_switch = Switch(hk)
                leaf_switch.switch_type = "leaf"

                l_up_link = Link(hk + "-" + hgk)                                         
                l_up_link.resource = switch                                                  
                l_up_link.nw_bandwidth = sys.maxint                          
                l_up_link.avail_nw_bandwidth = l_up_link.nw_bandwidth                            
                leaf_switch.up_links[l_up_link.name] = l_up_link

                h.switches[leaf_switch.name] = leaf_switch 
                _switches[leaf_switch.name] = leaf_switch

        return "success"




