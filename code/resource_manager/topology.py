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


import json

from resource_base import Datacenter, HostGroup, Host, Switch, Link


class Topology:

    def __init__(self, _config):
        self.config = _config

    # TODO
    def set_topology(self, _datacenter, _host_groups, _hosts, _switches):

        # output = read topology JSON from AIC Formation

        topology = None
        try:
            topology = json.loads(output)
            #print json.dumps(topology, indent=4)
        except (ValueError, KeyError, TypeError):
            return "JSON format error while getting topology"

        # set _datacenter, _host_groups, _hosts, _switches from topology

        return "success"




