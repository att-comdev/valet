import sys

from openstack_filters import AggregateInstanceExtraSpecsFilter
from openstack_filters import AvailabilityZoneFilter
from openstack_filters import RamFilter
from openstack_filters import CoreFilter
from openstack_filters import DiskFilter

sys.path.insert(0, '../app_manager')
from app_topology_base import VGroup, VM, LEVELS


class ConstraintSolverSimple:

    def __init__(self, _logger):
        self.logger = _logger

        self.openstack_AZ = AvailabilityZoneFilter(self.logger)
        self.openstack_AIES = AggregateInstanceExtraSpecsFilter(self.logger)
        self.openstack_R = RamFilter(self.logger)
        self.openstack_C = CoreFilter(self.logger)
        self.openstack_D = DiskFilter(self.logger)

        self.status = "success"

    def compute_candidate_list(self, _level, _n, _node_placements, _avail_resources, _avail_logical_groups):
        candidate_list = []
        for rk, r in _avail_resources.iteritems():
            candidate_list.append(r)

        if (isinstance(_n.node, VM) and _n.node.availability_zone != None) or \
           (isinstance(_n.node, VGroup) and len(_n.node.availability_zone_list) > 0):       
            self._constrain_availability_zone(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate availability zone constraint for node = " + _n.node.name
                return candidate_list

        if len(_n.node.extra_specs_list) > 0:
            self._constrain_host_aggregates(_level, _n, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate host aggregate constraint for node = " + _n.node.name
                return candidate_list

        self._constrain_cpu_capacity(_level, _n, candidate_list)
        if len(candidate_list) == 0:
            self.status = "violate cpu capacity constraint for node = " + _n.node.name
            return candidate_list

        self._constrain_mem_capacity(_level, _n, candidate_list)
        if len(candidate_list) == 0:
            self.status = "violate memory capacity constraint for node = " + _n.node.name
            return candidate_list

        self._constrain_local_disk_capacity(_level, _n, candidate_list)
        if len(candidate_list) == 0:
            self.status = "violate local disk capacity constraint for node = " + _n.node.name
            return candidate_list

        # Diversity constraint
        if len(_n.node.diversity_groups) > 0:
            self._constrain_diversity(_level, _n, _node_placements, candidate_list)
            if len(candidate_list) == 0:
                self.status = "violate diversity constraint for node = " + _n.node.name
                return candidate_list

        # Exclusivity constraint
        exclusivities = self.get_exclusivities(_n.node.exclusivity_groups, _level)

        if len(exclusivities) > 1:
            self.status = "violate exclusivity constraint (more than one exclusivity) for node = " + _n.node.name
            return []
        else:
            if len(exclusivities) == 1:
                self._constrain_exclusivity(_level, exclusivities[exclusivities.keys()[0]], candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate exclusivity constraint for node = " + _n.node.name
                    return candidate_list
            else:
                self._constrain_non_exclusivity(_level, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate non-exclusivity constraint for node = " + _n.node.name
                    return candidate_list

        # Affinity constraint
        affinity_id = _n.get_affinity_id()
        if affinity_id != None:
            if affinity_id in _avail_logical_groups.keys():
                self._constrain_affinity(_level, affinity_id, candidate_list)
                if len(candidate_list) == 0:
                    self.status = "violate affinity constraint for node = " + _n.node.name
                    return candidate_list

        return candidate_list

    def _constrain_affinity(self, _level, _affinity_id, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_affinity(_level, _affinity_id, r) == False:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

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

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def conflict_exclusivity(self, _level, _candidate):
        conflict = False

        memberships = _candidate.get_memberships(_level)
        for mk in memberships.keys():
            if memberships[mk].group_type == "EX" and mk.split(":")[0] == _level:
                conflict = True

        return conflict

    def get_exclusivities(self, _exclusivity_groups, _level):
        exclusivities = {}
   
        for exk, level in _exclusivity_groups.iteritems():
            if level.split(":")[0] == _level:
                exclusivities[exk] = level

        return exclusivities

    def _constrain_exclusivity(self, _level, _exclusivity_id, _candidate_list):
        candidate_list = self._get_exclusive_candidates(_level, _exclusivity_id, _candidate_list)

        if len(candidate_list) == 0:
            if _exclusivity_id.split(":")[0] == _level:
                candidate_list = self._get_hibernated_candidates(_level, _candidate_list)
                _candidate_list[:] = [x for x in _candidate_list if x in candidate_list]
        else:
            _candidate_list[:] = [x for x in _candidate_list if x in candidate_list]

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
            if self.check_host_aggregates(_level, r, _n.node) == False:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_host_aggregates(self, _level, _candidate, _v):
        return self.openstack_AIES.host_passes(_level, _candidate, _v)

    def _constrain_availability_zone(self, _level, _n, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.check_availability_zone(_level, r, _n.node) == False:
                if r not in conflict_list:
                    conflict_list.append(r)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_availability_zone(self, _level, _candidate, _v):
        return self.openstack_AZ.host_passes(_level, _candidate, _v)

    def _constrain_diversity(self, _level, _n, _node_placements, _candidate_list):
        conflict_list = []

        for r in _candidate_list:
            if self.conflict_diversity(_level, _n, _node_placements, r) == True:
                if r not in conflict_list:
                    conflict_list.append(r)
  
        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

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

        return conflict

    def _constrain_cpu_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_cpu_capacity(_level, _n.node, ch) == False:
                conflict_list.append(ch)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_cpu_capacity(self, _level, _v, _candidate):
        return self.openstack_C.host_passes(_level, _candidate, _v)

    def _constrain_mem_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_mem_capacity(_level, _n.node, ch) == False:
                conflict_list.append(ch)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_mem_capacity(self, _level, _v, _candidate):
        return self.openstack_R.host_passes(_level, _candidate, _v)

    def _constrain_local_disk_capacity(self, _level, _n, _candidate_list):
        conflict_list = []

        for ch in _candidate_list:
            if self.check_local_disk_capacity(_level, _n.node, ch) == False:
                conflict_list.append(ch)

        _candidate_list[:] = [c for c in _candidate_list if c not in conflict_list]

    def check_local_disk_capacity(self, _level, _v, _candidate):
        return self.openstack_D.host_passes(_level, _candidate, _v)




