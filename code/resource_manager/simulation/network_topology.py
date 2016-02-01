#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.0: Dec. 7, 2015
#
# Functions 
# - Update the uplink of each Switch resource
# - Set resource grouping using naming convention (temporary), e.g., san3c001r003
#
# TODO: 
# - Track storage IO bandwidths
# - Name of switches
#################################################################################################################


import sys
import json
import time
import subprocess
import threading

from resource_base import Datacenter, HostGroup, Host, Switch, Link
from authentication import Authentication


class NetworkTopology(threading.Thread):

    def __init__(self, _t_id, _t_name, _resource, _data_lock, _a_name, _u, _pw, _logger):
        threading.Thread.__init__(self)

        self.thread_id = _t_id
        self.thread_name = _t_name
        self.data_lock = _data_lock
        self.end_of_process = False

        self.resource = _resource

        self.logger = _logger

        self.auth = Authentication()

        self.admin_tenant_name = _a_name
        self.user_name = _u
        self.pw = _pw

        self.admin_token = None

    def init_APIs(self, _k_tt):
        self.keystone_tenant_token_api = _k_tt

    def run(self):
        self.logger.info("start " + self.thread_name + " ......")

        test_fire = 3
        test_end = time.time() + test_fire
        while self.end_of_process == False:
            time.sleep(1)

            if time.time() > test_end:
                self.data_lock.acquire(1)
                if self.set_network_topology() == True:
                    self.logger.debug("network updated")
                    self.resource.update_topology()
                self.data_lock.release()

                test_end = time.time() + test_fire

        self.logger.info("exit " + self.thread_name)

    def _set_admin_token(self):                                                                  
        self.admin_token = self.auth.get_tenant_token(self.keystone_tenant_token_api, \
                                                      self.admin_tenant_name, \
                                                      self.user_name, self.pw)                   
        if self.admin_token == None:                                                             
            self.logger.error(self.auth.status)                                                  
            return False                                                                         
                                                                                                 
        return True

    def _set_graph(self):
        graph = None

        p = subprocess.Popen(["tegu_req", "-j", "-t", self.admin_token, "-k", "project=_all_proj", "graph"], \
                             stdout=subprocess.PIPE)
        output, err = p.communicate()

        try:
            graph = json.loads(output)
            #print json.dumps(self.graph, indent=4)
        except (ValueError, KeyError, TypeError):
            message = ""
            if err == None:
                message = output
            else:
                message = err
            
            self.logger.error("while getting graph from Tegu: " + message)
            return None

        return graph





    def set_network_topology(self):
        if self._set_admin_token() == False:               
            return False

        graph = self._set_graph()
        if graph == None:
            return False
    
        elements = None
        try:
            elements = graph["reqstate"][0]["details"]["netele"]
        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while getting network elements from Tegu")
            return False

        datacenter = None
        host_groups = {}
        hosts = {}
        switches = {}
        for hk in self.resource.hosts.keys():
            host = Host(self.resource.hosts[hk].name)
            hosts[host.name] = host
        datacenter = Datacenter(self.resource.datacenter.name)

        # NOTE: What if the topology is not hierarchy?
        rack_count = self._set_host_links(elements, switches, hosts)
        if rack_count > 0:
            cluster_count = self._set_rack_links(elements, switches, hosts)
            if cluster_count > 0:
                # Count of links between spine and datacenter
                link_count = self._set_cluster_links(elements, datacenter, switches, hosts) 
                if link_count == 0:
                    # Make mockup uplink to datacenter
                    for sk in switches.keys():
                        spine_switch = switches[sk]
                        if spine_switch.switch_type == "Spine":
                            link = Link(spine_switch.name + "-" + datacenter.name)
                            link.resource = datacenter 
                            link.nw_bandwidth = sys.maxint
                            link.avail_nw_bandwidth = link.nw_bandwidth
                            spine_switch.switch_list.append(link)

                            datacenter.spine_switch_list.append(spine_switch)
                elif link_count < 0:
                    return False

            elif cluster_count == 0:
                for sk in switches.keys():
                    leaf_switch = switches[sk]
                    if leaf_switch.switch_type == "Leaf":
                        link = Link(leaf_switch.name + "-" + datacenter.name)
                        link.resource = datacenter 
                        link.nw_bandwidth = sys.maxint
                        link.avail_nw_bandwidth = link.nw_bandwidth
                        leaf_switch.switch_list.append(link)

                        datacenter.spine_switch_list.append(leaf_switch)
            else:
                return False

        # May not be happened
        elif rack_count == 0:
            for hk in hosts.keys():
                host = hosts[hk]
                if "tegu" in host.tag:
                    link = Link(host.name + "-" + datacenter.name)
                    link.resource = datacenter 
                    link.nw_bandwidth = sys.maxint
                    link.avail_nw_bandwidth = link.nw_bandwidth
                    host.leaf_switch_list.append(link)

                    datacenter.spine_switch_list.append(host)
        else:
            return False

        self._check_update(datacenter, switches, hosts)

        return True

    def _check_update(self, _datacenter, _switches, _hosts):
        for hk in _hosts.keys():
            if hk not in self.resource.hosts.keys():
                new_host = self._create_new_host(_hosts[hk]) 
                self.resource.hosts[new_host.name] = new_host

                #new_host.last_update = time.time()
                #new_host.last_metadata_update = time.time()
                #self.resource.last_update = new_host.last_update
                #self.resource.last_metadata_update = new_host.last_metadata_update 

                self.logger.warn("new host (" + new_host.name + ") added from network")

        for rhk in self.resource.hosts.keys():
            if rhk not in _hosts.keys():
                host = self.resource.hosts[rhk]
                if "tegu" in host.tag:
                    host.tag.remove("tegu")

                host.last_update = time.time()
                #self.resource.last_update = host.last_update

                self.logger.warn("host (" + host.name + ") removed from network")

        for sk in _switches.keys():
            if sk not in self.resource.switches.keys():
                new_switch = self._create_new_switch(_switches[sk])
                self.resource.switches[new_switch.name] = new_switch

                #new_switch.last_update = time.time()
                #new_switch.last_link_update = time.time()
                #self.resource.last_update = new_switch.last_update

                self.logger.warn("new switch (" + new_switch.name + ") added")

        for rsk in self.resource.switches.keys():
            if rsk not in _switches.keys():
                switch = self.resource.switches[rsk]
                switch.status = "disabled"

                switch.last_update = time.time()
                #self.resource.last_update = switch.last_update

                self.logger.warn("switch (" + switch.name + ") disabled")

        for hk in _hosts.keys():
            host = _hosts[hk]
            rhost = self.resource.hosts[hk]
            (topology_updated, link_updated) = self._check_host_update(host, rhost)
            if topology_updated == True:
                rhost.last_update = time.time()
                #self.resource.last_update = rhost.last_update
            if link_updated == True:
                rhost.last_link_update = time.time()
                #self.resource.last_update = rhost.last_link_update

        for sk in _switches.keys():
            switch = _switches[sk]
            rswitch = self.resource.switches[sk]
            (topology_updated, link_updated) = self._check_switch_update(switch, rswitch)
            if topology_updated == True:
                rswitch.last_update = time.time()
                #self.resource.last_update = rswitch.last_update
            if link_updated == True:
                rswitch.last_link_update = time.time()
                #self.resource.last_update = rswitch.last_link_update

        if self._check_datacenter_update(_datacenter) == True:
            self.resource.datacenter.last_update = time.time()
            #self.resource.last_update = self.resource.datacenter.last_update

        for hk in self.resource.hosts.keys():
            host = self.resource.hosts[hk]
            if host.last_update > self.resource.current_timestamp:
                self.resource.update_switch_resource(host)

        for sk in self.resource.switches.keys():
            switch = self.resource.switches[sk]
            if switch.last_update > self.resource.current_timestamp:
                self.resource.update_spine_switch_resource(switch)

    def _create_new_switch(self, _switch):
        new_switch = Switch(_switch.name)
        new_switch.switch_type = _switch.switch_type
        new_switch.status = "enabled"

        new_switch.last_update = 0        

        return new_switch
        
    def _create_new_host(self, _host):
        new_host = Host(_host.name)
        new_host.tag.append("tegu")

        new_host.last_update = 0        

        return new_host
        
    def _create_new_link(self, _link):
        new_link = Link(_link.name)

        resource = None
        if _link.resource.name in self.resource.switches.keys():
            resource = self.resource.switches[_link.resource.name]
        elif _link.resource.name == self.resource.datacenter.name:
            resource = self.resource.datacenter

        new_link.resource = resource
        new_link.nw_bandwidth = _link.nw_bandwidth
        new_link.avail_nw_bandwidth = _link.avail_nw_bandwidth
    
        return new_link

    def _check_link_update(self, _link, _rlink):
        updated = False

        if _link.nw_bandwidth != _rlink.nw_bandwidth:
            _rlink.nw_bandwidth = _link.nw_bandwidth
            updated = True

        if _link.avail_nw_bandwidth != _rlink.avail_nw_bandwidth:
            _rlink.avail_nw_bandwidth = _link.avail_nw_bandwidth
            updated = True

        return updated

    def _check_host_update(self, _host, _rhost):
        updated = False
        link_updated = False

        if "tegu" not in _rhost.tag:
            _rhost.tag.append("tegu")
            updated = True
            self.logger.warn("host (" + _rhost.name + ") updated (tag)")

        for link in _host.leaf_switch_list:
            exist = False
            for rlink in _rhost.leaf_switch_list:
                if link.name == rlink.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("host (" + _host.name + ") updated (bandwidth)")
                    break
            if exist == False:
                new_link = self._create_new_link(link)
                _rhost.leaf_switch_list.append(new_link)
                link_updated = True
                self.logger.warn("host (" + _rhost.name + ") updated (new link)")

        for rlink in _rhost.leaf_switch_list:
            exist = False
            for link in _host.leaf_switch_list:
                if rlink.name == link.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("host (" + _rhost.name + ") updated (bandwidth)")
                    break
            if exist == False:
                _rhost.leaf_switch_list.remove(rlink)
                link_updated = True
                self.logger.warn("host (" + _rhost.name + ") updated (link removed)")

        return (updated, link_updated)

    def _check_switch_update(self, _switch, _rswitch):
        updated = False
        link_updated = False

        if _switch.switch_type != _rswitch.switch_type:
            _rswitch.switch_type = _switch.switch_type
            updated = True
            self.logger.warn("switch (" + _rswitch.name + ") updated (switch type)")

        if _rswitch.status == "disabled":
            _rswitch.status == "enabled"
            updated = True
            self.logger.warn("switch (" + _rswitch.name + ") updated (enabled)")

        # Check the uplink of spine(or rack)
        for link in _switch.switch_list:
            exist = False
            for rlink in _rswitch.switch_list:
                if link.name == rlink.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                new_link = self._create_new_link(link)
                _rswitch.switch_list.append(new_link)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (new link)")

        for rlink in _rswitch.switch_list:
            exist = False
            for link in _switch.switch_list:
                if rlink.name == link.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                _rswitch.switch_list.remove(rlink)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (link removed)")

        # Check the downlink of spine
        for switch in _switch.leaf_switch_list:
            exist = False
            for rswitch in _rswitch.leaf_switch_list:
                if switch.name == rswitch.name:
                    exist = True
                    break
            if exist == False:
                _rswitch.leaf_switch_list.append(self.resource.switches[switch.name])
                updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (new child)")

        for rswitch in _rswitch.leaf_switch_list:
            exist = False
            for switch in _switch.leaf_switch_list:
                if rswitch.name == switch.name:
                    exist = True
                    break
            if exist == False:
                _rswitch.leaf_switch_list.remove(rswitch)
                updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (child removed)")

        # Check the uplink of rack
        for link in _switch.spine_switch_list:
            exist = False
            for rlink in _rswitch.spine_switch_list:
                if link.name == rlink.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                new_link = self._create_new_link(link)
                _rswitch.spine_switch_list.append(new_link)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (new link)")

        for rlink in _rswitch.spine_switch_list:
            exist = False
            for link in _switch.spine_switch_list:
                if rlink.name == link.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink) 
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                _rswitch.spine_switch_list.remove(rlink)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (link removed)")

        # Check the downlink of rack 
        for host in _switch.host_list:
            exist = False
            for rhost in _rswitch.host_list:
                if host.name == rhost.name:
                    exist = True
                    break
            if exist == False:
                _rswitch.host_list.append(self.resource.hosts[host.name])
                updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (new host)")

        for rhost in _rswitch.host_list:
            exist = False
            for host in _switch.host_list:
                if rhost.name == host.name:
                    exist = True
                    break
            if exist == False:
                _rswitch.host_list.remove(rhost)
                updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (host removed)")

        # Check the peerlink of this switch
        for link in _switch.peer_switch_list:
            exist = False
            for rlink in _rswitch.peer_switch_list:
                if link.name == rlink.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink) 
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                new_link = self._create_new_link(link)
                _rswitch.peer_switch_list.append(new_link)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (new link)")

        for rlink in _rswitch.peer_switch_list:
            exist = False
            for link in _switch.peer_switch_list:
                if rlink.name == link.name:
                    exist = True
                    link_updated = self._check_link_update(link, rlink)
                    if link_updated == True:
                        self.logger.warn("switch (" + _rswitch.name + ") updated (bandwidth)")
                    break
            if exist == False:
                _rswitch.peer_switch_list.remove(rlink)
                link_updated = True
                self.logger.warn("switch (" + _rswitch.name + ") updated (link removed)")

        return (updated, link_updated)

    def _check_datacenter_update(self, _datacenter):
        updated = False

        for resource in _datacenter.spine_switch_list:
            exist = False
            for rresource in self.resource.datacenter.spine_switch_list:
                if resource.name == rresource.name:
                    exist = True
                    break
            if exist == False:
                if isinstance(resource, Switch):
                    self.resource.datacenter.spine_switch_list.append(self.resource.switches[resource.name])
                elif isinstance(source, Host):
                    self.resource.datacenter.spine_switch_list.append(self.resource.hosts[resource.name])
                updated = True
                self.logger.warn("datacenter updated (new resource)")

        for rresource in self.resource.datacenter.spine_switch_list:
            exist = False
            for resource in _datacenter.spine_switch_list:
                if rresource.name == resource.name:
                    exist = True
                    break
            if exist == False:
                self.resource.datacenter.spine_switch_list.remove(rresource)
                updated = True
                self.logger.warn("datacenter updated (resource removed)")
        
        return updated

    # Parse links to ToR switches
    def _set_host_links(self, _elements, _switches, _hosts):
        rack_count = 0

        try:
            for e in _elements:
                host = None
                if e["id"] in _hosts.keys():
                    host = _hosts[e["id"]]
                else:
                    link_elements = e["links"]
                    link_id = link_elements[0]["id"].split("-")
                    if "@" in link_id[0]:
                        host_id = link_id[0].split("@")
                        host = Host(host_id[0])
                        _hosts[host.name] = host

                if host != None:
                    if "tegu" not in host.tag:
                        host.tag.append("tegu")

                    link_elements = e["links"]
                    for le in link_elements:
                        switch_id = le["sw2"] 
 
                        switch = None
                        if switch_id in _switches.keys():
                            switch = _switches[switch_id]
                        else:
                            switch = Switch(switch_id)
                            switch.switch_type = "Leaf"
                            switch.status = "enabled"
                            _switches[switch_id] = switch
                            rack_count += 1

                        # Set downlink
                        if len(host.leaf_switch_list) == 0: # TODO
                            switch.host_list.append(host)

                        link = Link(le["id"])
                        link.resource = switch 
                        link.nw_bandwidth = float(le["allotment"]["max_capacity"]) / 1000000.0 # Mbps
                        network_usage = self._compute_network_usage(le)
                        if network_usage == -1:
                            return -1
                        link.avail_nw_bandwidth = link.nw_bandwidth - network_usage
                        host.leaf_switch_list.append(link)

        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while setting host link topology")
            return -1

        return rack_count

    # Parse links to Spine Switches
    def _set_rack_links(self, _elements, _switches, _hosts):
        cluster_count = 0

        try:
            for e in _elements:
                if e["id"] in _switches.keys():
                    if _switches[e["id"]].switch_type == "Leaf":
                        leaf_switch = _switches[e["id"]]

                        link_elements = e["links"]
                        for le in link_elements:
                            target_id = le["sw2"] 
                            
                            if target_id in _hosts.keys(): 
                                continue
                            if target_id in _switches.keys():
                                if _switches[target_id].switch_type == "Leaf":
                                    peer_switch = _switches[target_id]
                                    link = Link(le["id"])
                                    link.resource = peer_switch 
                                    link.nw_bandwidth = float(le["allotment"]["max_capacity"]) / 1000000.0 # Mbps
                                    network_usage = self._compute_network_usage(le)
                                    if network_usage == -1:
                                        return -1
                                    link.avail_nw_bandwidth = link.nw_bandwidth - network_usage
                                    leaf_switch.peer_switch_list.append(link)
                                    
                                    continue

                            spine_switch = None
                            if target_id in _switches.keys():
                                spine_switch = _switches[target_id]
                            else:
                                spine_switch = Switch(target_id)
                                spine_switch.switch_type = "Spine"
                                spine_switch.status = "enabled"
                                _switches[target_id] = spine_switch
                                cluster_count += 1

                            # Set downlink
                            if len(leaf_switch.spine_switch_list) == 0: # TODO
                                spine_switch.leaf_switch_list.append(leaf_switch)

                            link = Link(le["id"])
                            link.resource = spine_switch 
                            link.nw_bandwidth = float(le["allotment"]["max_capacity"]) / 1000000.0 # Mbps
                            network_usage = self._compute_network_usage(le)
                            if network_usage == -1:
                                return -1
                            link.avail_nw_bandwidth = link.nw_bandwidth - network_usage
                            leaf_switch.spine_switch_list.append(link)

        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while setting rack link topology")
            return -1

        return cluster_count

    # Parse links to root switch
    def _set_cluster_links(self, _elements, _datacenter, _switches, _hosts):
        link_count = 0

        try:
            for e in _elements:
                if e["id"] in _switches.keys():
                    if _switches[e["id"]].switch_type == "Spine":
                        spine_switch = _switches[e["id"]]

                        link_elements = e["links"]
                        for le in link_elements:
                            target_id = le["sw2"] 

                            if target_id in _hosts.keys(): # wont be happened!
                                continue
                            if target_id in _switches.keys(): 
                                if _switches[target_id].switch_type == "Leaf": # found downlink
                                    continue
                                if _switches[target_id].switch_type == "Spine":
                                    peer_switch = _switches[target_id]
                                    link = Link(le["id"])
                                    link.resource = peer_switch 
                                    link.nw_bandwidth = float(le["allotment"]["max_capacity"]) / 1000000.0 # Mbps
                                    network_usage = self._compute_network_usage(le)
                                    if network_usage == -1:
                                        return -1
                                    link.avail_nw_bandwidth = link.nw_bandwidth - network_usage
                                    spine_switch.peer_switch_list.append(link)

                                    continue

                            link = Link(le["id"])
                            link.resource = _datacenter 
                            link.nw_bandwidth = float(le["allotment"]["max_capacity"]) / 1000000.0 # Mbps
                            network_usage = self._compute_network_usage(le)
                            if network_usage == -1:
                                return -1
                            link.avail_nw_bandwidth = link.nw_bandwidth - network_usage
                            spine_switch.switch_list.append(link)

                            # Set downlink
                            _datacenter.spine_switch_list.append(spine_switch)

                            link_count += 1

        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while setting cluster link topology")
            return -1

        return link_count
        
    def _compute_network_usage(self, _element):
        usage = 0

        try:
            current_ts = time.time()
            for ts in _element["allotment"]["timeslices"]:
                if current_ts < ts["conclude"]:
                    usage = usage + ts["amt"]
        except (ValueError, KeyError, TypeError):
            self.logger.error("JSON format error while computing network usage")
            return -1

        return float(usage)/1000000.0



