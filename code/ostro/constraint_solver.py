#!/bin/python


################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.2: Feb. 9, 2016
#
# Functions 
# - Constrain the search 
#
################################################################################################################


import sys

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, Volume, VGroupLink, VMLink, VolumeLink, LEVELS


class ConstraintSolver:

    def __init__(self, _logger):
        self.logger = _logger

        self.status = "success"

    def compute_candidate_list(self, _level, _n, _node_placements, _avail_resources, _avail_logical_groups):
        candidate_list = []
        for rk, r in _avail_resources.iteritems():
            candidate_list.append(r)

        # Compute capacity constraint
        if isinstance(_n.node, VGroup) or isinstance(_n.node, VM):
            self._constrain_compute_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate compute capacity constraint for node = " + _n.node.name
                self.logger.error(self.status)
                return candidate_list

        # Storage capacity constraint
        if (isinstance(_n.node, VGroup) and len(_n.node.volume_sizes) > 0) or isinstance(_n.node, Volume):
            self._constrain_storage_capacity(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate storage capacity constraint for node = " + _n.node.name
                self.logger.error(self.status)
                return candidate_list

        # Network bandwidth constraint
        self._constrain_nw_bandwidth_capacity(_level, _n, _node_placements, candidate_list)
        if len(candidate_list) == 0:
            self.status = "violate nw bandwidth capacity constraint for node = " + _n.node.name
            self.logger.error(self.status)
            return candidate_list

        # Host Aggregate constraint
        if len(_n.node.host_aggregates) > 0:
            self._constrain_host_aggregates(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate host aggregate constraint for node = " + _n.node.name
                self.logger.error(self.status)
                return candidate_list

        # Diversity constraint
        if len(_n.node.diversity_groups) > 0:
            self._constrain_diversity(_level, _n, _node_placements, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate diversity constraint for node = " + _n.node.name
                self.logger.error(self.status)
                return candidate_list

        # Exclusivity constraint
        exclusivity_id = _n.get_exclusivity_id()
        if exclusivity_id == None:
            exclusivity_id = _n.get_parent_exclusivity_id()
            if exclusivity_id == None:
                self._constrain_non_exclusivity(_level, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate non-exclusivity constraint for node = " + _n.node.name
                    self.logger.error(self.status)
                    return candidate_list
        else:
            self._constrain_exclusivity(_level, exclusivity_id, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate exclusivity constraint for node = " + _n.node.name
                self.logger.error(self.status)
                return candidate_list

        # Affinity constraint
        affinity_id = _n.get_affinity_id()
        if affinity_id != None:
            if affinity_id in _avail_logical_groups.keys():
                self._constrain_affinity(_level, affinity_id, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate affinity constraint for node = " + _n.node.name
                    self.logger.error(self.status)
                    return candidate_list

        return candidate_list

    def _constrain_affinity(self, _level, _affinity_id, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_affinity(_level, _affinity_id, r) == False:
                if r not in conflict_list:
                    conflict_list.append(r)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                self.logger.debug("violates affinity in resource = " + debug_resource_name)

    def check_affinity(self, _level, _affinity_id, _candidate):
        match = False

        memberships = _candidate.get_memberships(_level)
        if _affinity_id in memberships.keys(): 
            match = True

        return match

    def _constrain_non_exclusivity(self, _level, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_exclusivity(_level, r) == True:
                if r not in conflict_list:
                    conflict_list.append(r)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                self.logger.debug("violates non exclusivity in resource = " + debug_resource_name)

    def conflict_exclusivity(self, _level, _candidate):
        conflict = False

        memberships = _candidate.get_memberships(_level)
        for mk in memberships.keys():
            if memberships[mk].group_type == "EX" and mk.split(":")[0] == _level:
                conflict = True

        return conflict

    def _constrain_exclusivity(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = self._get_exclusive_candidates(_level, _exclusivity_id, _candidate_list)
        if len(candidate_list) == 0:
            if _exclusivity_id.split(":")[0] == _level:
                candidate_list = self._get_hibernated_candidates(_level, _candidate_list)

                for cc in _candidate_list:
                    if cc not in candidate_list:
                        _candidate_list.remove(cc)

                        debug_resource_name = cc.get_resource_name(_level)
                        self.logger.debug("violates the exclusivity group in resource = " + debug_resource_name)

            else: # i.e., _level > exclusivity_level
                pass

    def _get_exclusive_candidates(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.check_exclusivity(_level, _exclusivity_id, r) == True:
                if r not in candidate_list:
                    candidate_list.append(r)

        return candidate_list

    def check_exclusivity(self, _level, _exclusivity_id, _candidate):
        match = False

        memberships = _candidate.get_memberships(_level)
        if _exclusivity_id in memberships.keys():
            match = True

        return match
        
    def _get_hibernated_candidates(self, _level, _candidate_list):
        candidate_list = []

        for r in _candidate_list:
            if self.check_hibernated(_level, r) == True:
                if r not in candidate_list:
                    candidate_list.append(r)

        return candidate_list

    def check_hibernated(self, _level, _candidate):
        match = False

        num_of_placed_vms = _candidate.get_num_of_placed_vms(_level)
        if num_of_placed_vms == 0:
            match = True
        
        return match
        
    def _constrain_host_aggregates(self, _level, _n, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_host_aggregates(_level, _n.node, r) == False:
                if r not in conflict_list:
                    conflict_list.append(r)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                self.logger.debug("violates the host aggregate in resource = " + debug_resource_name)

    def check_host_aggregates(self, _level, _v, _candidate):
        return self._match_host_aggregates(_v, _candidate.get_memberships(_level))

    def _match_host_aggregates(self, _v, _target_memberships):
        if isinstance(_v, VM):
            match = True

            for mk in _v.host_aggregates.keys():
                if mk not in _target_memberships.keys():
                    match = False
                    break

            return match

        elif isinstance(_v, VGroup):
            match = True

            for sg in _v.subvgroup_list:
                match = self._match_host_aggregates(sg, _target_memberships)
                if match == False:
                    break

            return match
  
    def _constrain_diversity(self, _level, _n, _node_placements, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_diversity(_level, _n, _node_placements, r) == True:
                if r not in conflict_list:
                    conflict_list.append(r)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)
  
                debug_resource_name = cc.get_resource_name(_level)
                self.logger.debug("violates the diversity group in resource = " + debug_resource_name)

    def conflict_diversity(self, _level, _n, _node_placements, _candidate):
        conflict = False

        for v in _node_placements.keys(): 
            diversity_level = _n.get_common_diversity(v.diversity_groups)
            if diversity_level != "ANY" and LEVELS.index(diversity_level) >= LEVELS.index(_level):
                if diversity_level == "host":
                    if _candidate.cluster_name == _node_placements[v].cluster_name and \
                       _candidate.rack_name == _node_placements[v].rack_name and  \
                       _candidate.host_name == _node_placements[v].host_name:
                        conflict = True
                        break
                elif diversity_level == "rack":
                    if _candidate.cluster_name == _node_placements[v].cluster_name and \
                       _candidate.rack_name == _node_placements[v].rack_name:
                        conflict = True
                        break
                elif diversity_level == "cluster":
                    if _candidate.cluster_name == _node_placements[v].cluster_name:
                        conflict = True
                        break

        return conflict

    def _constrain_compute_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_compute_availability(_level, _n.node, ch) == False:
                conflict_list.append(ch)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                (avail_vCPUs, avail_mem, avail_local_disk) = cc.get_avail_resources(_level)
                self.logger.debug("compute resource constrained in resource = " + debug_resource_name)
                if _n.node.vCPUs > avail_vCPUs:
                    self.logger.debug("lack of CPU = " + str(_n.node.vCPU - avail_vCPUs))
                if _n.node.mem > avail_mem:
                    self.logger.debug("lack of mem = " + str(_n.node.mem - avail_mem))
                if _n.node.local_volume_size > avail_local_disk:
                    self.logger.debug("lack of local disk = " + str(_n.node.local_volume_size - avail_local_disk))

    def check_compute_availability(self, _level, _v, _ch):
        available = True

        (avail_vCPUs, avail_mem, avail_local_disk) = _ch.get_avail_resources(_level)
        if avail_vCPUs < _v.vCPUs or avail_mem < _v.mem or avail_local_disk < _v.local_volume_size:
            available = False

        return available

    def _constrain_storage_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_storage_availability(_level, _n.node, ch) == False:
                conflict_list.append(ch)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                avail_storages = cc.get_avail_storages(_level)
                avail_disks = []
                volume_classes = []
                volume_sizes = []
                if isinstance(_n.node, VGroup):
                    for vck in _n.node.volume_sizes.keys():
                        volume_classes.append(vck)
                        volume_sizes.append(_n.node.volume_sizes[vck])
                else:
                    volume_classes.append(_n.node.volume_class)
                    volume_sizes.append(_n.node.volume_size)
             
                for vc in volume_classes:
                    for sk, s in avail_storages.iteritems():
                        if vc == "any" or s.storage_class == vc:
                            avail_disks.append(s.storage_avail_disk)

                self.logger.debug("storage resource constrained in resource = " + debug_resource_name)
                #for ds in avail_disks:
                    #print "    disk size = ", ds
                #for vs in volume_sizes:
                    #print "    volume size = ", vs

    def check_storage_availability(self, _level, _v, _ch):
        available = False

        volume_sizes = []
        if isinstance(_v, VGroup):
            for vck in _v.volume_sizes.keys():
                volume_sizes.append((vck, _v.volume_sizes[vck]))
        else:
            volume_sizes.append((_v.volume_class, _v.volume_size))

        avail_storages = _ch.get_avail_storages(_level)
        for (vc, vs) in volume_sizes:
            for sk, s in avail_storages.iteritems():
                if vc == "any" or s.storage_class == vc:
                    if s.storage_avail_disk >= vs:
                        available = True
                        break
                    else:
                        available = False
            if available == False:
                break

        return available

    def _constrain_nw_bandwidth_capacity(self, _level, _n, _node_placements, _candidate_list):
        conflict_list = []

        for cr in _candidate_list:
            if self.check_nw_bandwidth_availability(_level, _n, _node_placements, cr) == False:
                if cr not in conflict_list:
                    conflict_list.append(cr)

        for cc in conflict_list:
            if cc in _candidate_list:
                _candidate_list.remove(cc)

                debug_resource_name = cc.get_resource_name(_level)
                #bandwidth = None
                #if _level == "cluster":
                    #bandwidth = str(min(cc.cluster_avail_nw_bandwidths))
                #elif _level == "rack":
                    #bandwidth = str(min(cc.cluster_avail_nw_bandwidths)) + "-" + \
                    #            str(min(cc.rack_avail_nw_bandwidths))
                #elif _level == "host":
                    #bandwidth = str(min(cc.cluster_avail_nw_bandwidths)) + "-" + \
                    #            str(min(cc.rack_avail_nw_bandwidths)) + "-" + \
                    #            str(min(cc.host_avail_nw_bandwidths))

                self.logger.debug("network bandwidth constrained in resource = " + debug_resource_name)
                #self.logger.debug("avail bandwidth = " + bandwidth)
                #self.logger.debug("requested bandwidth = " + str(_n.node.nw_bandwidth))

    def check_nw_bandwidth_availability(self, _level, _n, _node_placements, _cr):
        # NOTE: 3rd entry for special node requiring bandwidth of out-going from spine switch
        total_req_bandwidths = [0, 0, 0]

        link_list = _n.get_all_links()

        for vl in link_list:
            bandwidth = _n.get_bandwidth_of_link(vl)

            placement_level = None
            if vl.node in _node_placements.keys(): # vl.node is VM or Volume
                placement_level = _node_placements[vl.node].get_common_placement(_cr)
            else: # in the open list
                placement_level = _n.get_common_diversity(vl.node.diversity_groups)
                if placement_level == "ANY":
                    implicit_diversity = self.get_implicit_diversity(_n.node, link_list, vl.node, _level)
                    if implicit_diversity[0] != None:
                        placement_level = implicit_diversity[1]

            self.get_req_bandwidths(_level, placement_level, bandwidth, total_req_bandwidths)

        return self._check_nw_bandwidth_availability(_level, total_req_bandwidths, _cr)

    # To find any implicit diversity relation caused by the other links of _v 
    # (i.e., intersection between _v and _target_v) 
    def get_implicit_diversity(self, _v, _link_list, _target_v, _level):
        max_implicit_diversity = (None, 0)

        for vl in _link_list:
            diversity_level = _v.get_common_diversity(vl.node.diversity_groups)
            if diversity_level != "ANY" and LEVELS.index(diversity_level) >= LEVELS.index(_level):
                for dk, dl in vl.node.diversity_groups.iteritems():
                    if LEVELS.index(dl) > LEVELS.index(diversity_level):
                        if _target_v.uuid != vl.node.uuid:
                            if dk in _target_v.diversity_groups.keys():
                                if LEVELS.index(dl) > max_implicit_diversity[1]:
                                    max_implicit_diversity = (dk, dl)

        return max_implicit_diversity

    def get_req_bandwidths(self, _level, _placement_level, _bandwidth, _total_req_bandwidths):
        if _level == "cluster" or _level == "rack":
            if _placement_level == "cluster" or _placement_level == "rack":
                _total_req_bandwidths[1] += _bandwidth
        elif _level == "host":
            if _placement_level == "cluster" or _placement_level == "rack":
                _total_req_bandwidths[1] += _bandwidth
                _total_req_bandwidths[0] += _bandwidth
            elif _placement_level == "host":
                _total_req_bandwidths[0] += _bandwidth

    def _check_nw_bandwidth_availability(self, _level, _req_bandwidths, _candidate_resource):
        available = True

        if _level == "cluster":
            cluster_avail_bandwidths = []
            for srk, sr in _candidate_resource.cluster_avail_switches.iteritems():
                cluster_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(cluster_avail_bandwidths) < _req_bandwidths[1]:
                available = False

        elif _level == "rack":
            rack_avail_bandwidths = []
            for srk, sr in _candidate_resource.rack_avail_switches.iteritems():
                rack_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(rack_avail_bandwidths) < _req_bandwidths[1]:
                available = False

        elif _level == "host":
            host_avail_bandwidths = []
            for srk, sr in _candidate_resource.host_avail_switches.iteritems():
                host_avail_bandwidths.append(max(sr.avail_bandwidths))

            if max(host_avail_bandwidths) < _req_bandwidths[0]:
                available = False

            rack_avail_bandwidths = []
            for srk, sr in _candidate_resource.rack_avail_switches.iteritems():
                rack_avail_bandwidths.append(max(sr.avail_bandwidths))

            avail_bandwidth = min(max(host_avail_bandwidths), max(rack_avail_bandwidths))
            if avail_bandwidth < _req_bandwidths[1]:
                available = False

        return available




