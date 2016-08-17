#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 1.0: Aug. 12, 2016
#
# Functions
# - Parse each application
#
#################################################################################################################

from valet.engine.optimizer.app_manager.app_topology_base import VGroup, VGroupLink, VM, VMLink, LEVELS
# from valet.engine.optimizer.app_manager.app_topology_base import Volume, VolumeLink


'''
NOTE: Restrictions of nested groups
    EX in EX
    EX in DIV
    DIV in EX
    DIV in DIV

    VM/group cannot exist in multiple EX groups
    Nested group's level cannot be higher than nesting group
'''


class Parser(object):

    def __init__(self, _resource, _logger):
        self.resource = _resource

        self.logger = _logger

        self.high_level_allowed = True
        if "none" in self.resource.datacenter.region_code_list:
            self.high_level_allowed = False

        self.format_version = None
        self.stack_id = None          # used as application id
        self.application_name = None
        self.action = None            # [create|update|ping]

        self.total_nw_bandwidth = 0
        self.total_CPU = 0
        self.total_mem = 0
        self.total_local_vol = 0
        self.total_vols = {}

        self.status = "success"

    def set_topology(self, _graph):
        if "version" in _graph.keys():
            self.format_version = _graph["version"]
        else:
            self.format_version = "0.0"

        if "stack_id" in _graph.keys():
            self.stack_id = _graph["stack_id"]
        else:
            self.stack_id = "none"

        if "application_name" in _graph.keys():
            self.application_name = _graph["application_name"]
        else:
            self.application_name = "none"

        if "action" in _graph.keys():
            self.action = _graph["action"]
        else:
            self.action = "any"

        return self._set_topology(_graph["resources"])

    def _set_topology(self, _elements):
        vgroups = {}
        vms = {}
        volumes = {}

        for rk, r in _elements.iteritems():

            if r["type"] == "OS::Nova::Server":
                vm = VM(self.stack_id, rk)

                if "name" in r.keys():
                    vm.name = r["name"]
                else:
                    vm.name = vm.uuid

                if vm.set_vm_properties(r["properties"]["flavor"], self.resource) is False:
                    self.status = "not recognize flavor = " + r["properties"]["flavor"]
                    return ({}, {}, {})

                if "availability_zone" in r["properties"].keys():
                    az = r["properties"]["availability_zone"]
                    # NOTE: do not allow to specify a certain host name
                    vm.availability_zone = az.split(":")[0]

                vms[vm.uuid] = vm

                self.logger.debug("get a vm = " + vm.name)

            elif r["type"] == "OS::Cinder::Volume":
                self.logger.debug("do nothing for volume at this version")

                '''
                volume = Volume(self.stack_id, rk)

                if "name" in r.keys():
                    volume.name = r["name"]
                else:
                    volume.name = volume.uuid

                if "tier" in r['properties']['metadata']:
                    volume.volume_class = r['properties']['metadata']['tier']
                else:
                    volume.volume_class = "any"

                volume.volume_size = r["properties"]["size"]

                volumes[volume.uuid] = volume
                '''

            elif r["type"] == "ATT::Valet::GroupAssignment":
                vgroup = VGroup(self.stack_id, rk)

                vgroup.vgroup_type = None
                if r["properties"]["group_type"] == "affinity":
                    vgroup.vgroup_type = "AFF"
                elif r["properties"]["group_type"] == "diversity":
                    vgroup.vgroup_type = "DIV"
                elif r["properties"]["group_type"] == "exclusivity":
                    vgroup.vgroup_type = "EX"
                else:
                    self.status = "unknown group = " + r["properties"]["group_type"]
                    return ({}, {}, {})

                if "group_name" in r["properties"].keys():
                    vgroup.name = r["properties"]["group_name"]
                else:
                    if vgroup.vgroup_type == "EX":
                        self.status = "no exclusivity identifier"
                        return ({}, {}, {})
                    else:
                        vgroup.name = "any"

                vgroup.level = r["properties"]["level"]

                if vgroup.level != "host":
                    if self.high_level_allowed is False:
                        self.status = "only host level of affinity group allowed in this site " + \
                                      "due to the mis-match of host naming convention"
                        return ({}, {}, {})

                vgroups[vgroup.uuid] = vgroup

                self.logger.debug("get a group = " + vgroup.name)

            '''
            elif r["type"] == "OS::Nova::ServerGroup" or \
                 r["type"] == "OS::Heat::AutoScalingGroup" or \
                 r["type"] == "OS::Heat::Stack" or \
                 r["type"] == "OS::Heat::ResourceGroup":
                 r["type"] == "OS::Heat::ResourceGroup":

                self.status = "Not supported resource type (" + r["type"]+ ") in this version"
                return ({}, {}, {})
            '''

        self._set_vm_links(_elements, vms)

        if self._set_volume_links(_elements, vms, volumes) is False:
            return ({}, {}, {})

        self._set_total_link_capacities(vms, volumes)

        self._set_weight(vms, volumes)

        self.logger.debug("all vms parsed")

        if self._merge_diversity_groups(_elements, vgroups, vms, volumes) is False:
            return ({}, {}, {})

        if self._merge_exclusivity_groups(_elements, vgroups, vms, volumes) is False:
            return ({}, {}, {})

        if self._merge_affinity_groups(_elements, vgroups, vms, volumes) is False:
            return ({}, {}, {})

        # Delete all remaining EX and DIV vgroups
        for vgk in vgroups.keys():
            vg = vgroups[vgk]
            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                del vgroups[vgk]

        self.logger.debug("all groups resolved")

        for vgk in vgroups.keys():
            vgroup = vgroups[vgk]
            self._set_vgroup_links(vgroup, vgroups, vms, volumes)

            if isinstance(vgroup, VGroup):
                self._set_vgroup_weight(vgroup)

        self.logger.debug("all groups parsed")

        return (vgroups, vms, volumes)

    def _set_vm_links(self, _elements, _vms):
        for _, r in _elements.iteritems():
            if r["type"] == "ATT::CloudQoS::Pipe":
                resources = r["properties"]["resources"]
                for vk1 in resources:
                    if vk1 in _vms.keys():
                        vm = _vms[vk1]
                        for vk2 in resources:
                            if vk2 != vk1:
                                if vk2 in _vms.keys():
                                    link = VMLink(_vms[vk2])
                                    if "bandwidth" in r["properties"].keys():
                                        link.nw_bandwidth = r["properties"]["bandwidth"]["min"]
                                    vm.vm_list.append(link)

    def _set_volume_links(self, _elements, _vms, _volumes):
        for rk, r in _elements.iteritems():

            if r["type"] == "OS::Cinder::VolumeAttachment":
                self.logger.debug("do nothing for volume attachment at this version")

                '''
                vm_uuid = r["properties"]["instance_uuid"]
                if vm_uuid not in _vms.keys():
                    self.status = "vm {} of volume attachement {} not exist".format(vm_uuid, r["name"])
                    return False
                vm = _vms[vm_uuid]

                vol_uuid = r["properties"]["volume_id"]
                if vol_uuid not in _volumes.keys():
                    self.status = "volume {} of volume attachement {} not exist".format(vol_uuid, r["name"])
                    return False
                volume = _volumes[vol_uuid]

                vm2volume_link = VolumeLink(volume)
                volume2vm_link = VolumeLink(vm)

                name = None
                if "name" in r.keys():
                    name = r["name"]
                else:
                    name = rk

                self._set_volume_attributes(_elements, rk, name, vm2volume_link, volume2vm_link)

                vm.volume_list.append(vm2volume_link)
                volume.vm_list.append(volume2vm_link)
                '''

        return True

    '''
    def _set_volume_attributes(self, _elements, _link_id, _link_name, _link1, _link2):
        for _, r in _elements.iteritems():
            if r["type"] == "ATT::CloudQoS::Pipe":
                resources = r["properties"]["resources"]
                if _link_id in resources:
                    property_elements = r["properties"]
                    if "bandwidth" in property_elements.keys():
                        _link1.io_bandwidth = r["properties"]["bandwidth"]["min"]
                        _link2.io_bandwidth = r["properties"]["bandwidth"]["min"]
                    break
    '''

    def _set_total_link_capacities(self, _vms, _volumes):
        for _, vm in _vms.iteritems():
            for vl in vm.vm_list:
                vm.nw_bandwidth += vl.nw_bandwidth
            for voll in vm.volume_list:
                vm.io_bandwidth += voll.io_bandwidth

        for _, volume in _volumes.iteritems():
            for vl in volume.vm_list:
                volume.io_bandwidth += vl.io_bandwidth

    def _set_weight(self, _vms, _volumes):
        for _, vm in _vms.iteritems():

            if self.resource.CPU_avail > 0:
                vm.vCPU_weight = float(vm.vCPUs) / float(self.resource.CPU_avail)
            else:
                vm.vCPU_weight = 1.0
            self.total_CPU += vm.vCPUs

            if self.resource.mem_avail > 0:
                vm.mem_weight = float(vm.mem) / float(self.resource.mem_avail)
            else:
                vm.mem_weight = 1.0
            self.total_mem += vm.mem

            if self.resource.local_disk_avail > 0:
                vm.local_volume_weight = float(vm.local_volume_size) / float(self.resource.local_disk_avail)
            else:
                if vm.local_volume_size > 0:
                    vm.local_volume_weight = 1.0
                else:
                    vm.local_volume_weight = 0.0
            self.total_local_vol += vm.local_volume_size

            bandwidth = vm.nw_bandwidth + vm.io_bandwidth

            if self.resource.nw_bandwidth_avail > 0:
                vm.bandwidth_weight = float(bandwidth) / float(self.resource.nw_bandwidth_avail)
            else:
                if bandwidth > 0:
                    vm.bandwidth_weight = 1.0
                else:
                    vm.bandwidth_weight = 0.0

            self.total_nw_bandwidth += bandwidth

        for _, volume in _volumes.iteritems():

            if self.resource.disk_avail > 0:
                volume.volume_weight = float(volume.volume_size) / float(self.resource.disk_avail)
            else:
                if volume.volume_size > 0:
                    volume.volume_weight = 1.0
                else:
                    volume.volume_weight = 0.0

            if volume.volume_class in self.total_vols.keys():
                self.total_vols[volume.volume_class] += volume.volume_size
            else:
                self.total_vols[volume.volume_class] = volume.volume_size

            if self.resource.nw_bandwidth_avail > 0:
                volume.bandwidth_weight = float(volume.io_bandwidth) / float(self.resource.nw_bandwidth_avail)
            else:
                if volume.io_bandwidth > 0:
                    volume.bandwidth_weight = 1.0
                else:
                    volume.bandwidth_weight = 0.0

            self.total_nw_bandwidth += volume.io_bandwidth

    def _merge_diversity_groups(self, _elements, _vgroups, _vms, _volumes):
        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "diversity" and \
                   r["properties"]["level"] == level:

                    vgroup = _vgroups[rk]

                    for vk in r["properties"]["resources"]:
                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].diversity_groups[rk] = vgroup.level
                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].diversity_groups[rk] = vgroup.level
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = "group type (" + vg.vgroup_type + ") not allowd to be " + \
                                              "nested in diversity group at this version"
                                return False

                            vgroup.subvgroups[vk] = vg
                            vg.diversity_groups[rk] = vgroup.level
                        else:
                            self.status = "invalid resource = " + vk
                            return False

        return True

    def _merge_exclusivity_groups(self, _elements, _vgroups, _vms, _volumes):
        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "exclusivity" and \
                   r["properties"]["level"] == level:

                    vgroup = _vgroups[rk]

                    for vk in r["properties"]["resources"]:
                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                self.status = "group type (" + vg.vgroup_type + ") not allowd to be " + \
                                              "nested in exclusivity group at this version"
                                return False

                            vgroup.subvgroups[vk] = vg
                            vg.exclusivity_groups[rk] = vgroup.level + ":" + vgroup.name
                        else:
                            self.status = "invalid resource = " + vk
                            return False

        return True

    def _merge_affinity_groups(self, _elements, _vgroups, _vms, _volumes):
        affinity_map = {}  # key is uuid of vm, volume, or vgroup & value is its parent vgroup

        for level in LEVELS:
            for rk, r in _elements.iteritems():
                if r["type"] == "ATT::Valet::GroupAssignment" and \
                   r["properties"]["group_type"] == "affinity" and \
                   r["properties"]["level"] == level:

                    vgroup = None
                    if rk in _vgroups.keys():
                        vgroup = _vgroups[rk]
                    else:
                        continue

                    self.logger.debug("merge for affinity = " + vgroup.name)

                    for vk in r["properties"]["resources"]:

                        if vk in _vms.keys():
                            vgroup.subvgroups[vk] = _vms[vk]
                            _vms[vk].survgroup = vgroup

                            affinity_map[vk] = vgroup

                            self._add_implicit_diversity_groups(vgroup, _vms[vk].diversity_groups)
                            self._add_implicit_exclusivity_groups(vgroup, _vms[vk].exclusivity_groups)
                            self._add_memberships(vgroup, _vms[vk])
                            self._add_resource_requirements(vgroup, _vms[vk])

                            del _vms[vk]

                        elif vk in _volumes.keys():
                            vgroup.subvgroups[vk] = _volumes[vk]
                            _volumes[vk].survgroup = vgroup

                            affinity_map[vk] = vgroup

                            self._add_implicit_diversity_groups(vgroup, _volumes[vk].diversity_groups)
                            self._add_implicit_exclusivity_groups(vgroup, _volumes[vk].exclusivity_groups)
                            self._add_memberships(vgroup, _volumes[vk])
                            self._add_resource_requirements(vgroup, _volumes[vk])

                            del _volumes[vk]

                        elif vk in _vgroups.keys():
                            vg = _vgroups[vk]

                            if LEVELS.index(vg.level) > LEVELS.index(level):
                                self.status = "grouping scope: nested group's level is higher"
                                return False

                            if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                                if self._merge_subgroups(vgroup, vg.subvgroups, _vms, _volumes, _vgroups,
                                                         _elements, affinity_map) is False:
                                    return False
                                del _vgroups[vk]
                            else:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    if self._get_subgroups(vg, _elements, _vgroups, _vms, _volumes, affinity_map) is False:
                                        return False

                                    vgroup.subvgroups[vk] = vg
                                    vg.survgroup = vgroup

                                    affinity_map[vk] = vgroup

                                    self._add_implicit_diversity_groups(vgroup, vg.diversity_groups)
                                    self._add_implicit_exclusivity_groups(vgroup, vg.exclusivity_groups)
                                    self._add_memberships(vgroup, vg)
                                    self._add_resource_requirements(vgroup, vg)

                                    del _vgroups[vk]

                        else:  # vk belongs to the other vgroup already or refer to invalid resource
                            if vk not in affinity_map.keys():
                                self.status = "invalid resource = " + vk
                                return False

                            if affinity_map[vk].uuid != vgroup.uuid:
                                if self._exist_in_subgroups(vk, vgroup) is None:
                                    self._set_implicit_grouping(vk, vgroup, affinity_map, _vgroups)

        return True

    def _merge_subgroups(self, _vgroup, _subgroups, _vms, _volumes, _vgroups, _elements, _affinity_map):
        for vk, _ in _subgroups.iteritems():
            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])
                self._add_resource_requirements(_vgroup, _vms[vk])

                del _vms[vk]

            elif vk in _volumes.keys():
                _vgroup.subvgroups[vk] = _volumes[vk]
                _volumes[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _volumes[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _volumes[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _volumes[vk])
                self._add_resource_requirements(_vgroup, _volumes[vk])

                del _volumes[vk]

            elif vk in _vgroups.keys():
                vg = _vgroups[vk]

                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is higher"
                    return False

                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups, _vms, _volumes, _vgroups, _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _volumes, _affinity_map) is False:
                            return False

                        _vgroup.subvgroups[vk] = vg
                        vg.survgroup = _vgroup

                        _affinity_map[vk] = _vgroup

                        self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                        self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                        self._add_memberships(_vgroup, vg)
                        self._add_resource_requirements(_vgroup, vg)

                        del _vgroups[vk]

            else:  # vk belongs to the other vgroup already or refer to invalid resource
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False

                if _affinity_map[vk].uuid != _vgroup.uuid:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)

        return True

    def _get_subgroups(self, _vgroup, _elements, _vgroups, _vms, _volumes, _affinity_map):

        for vk in _elements[_vgroup.uuid]["properties"]["resources"]:

            if vk in _vms.keys():
                _vgroup.subvgroups[vk] = _vms[vk]
                _vms[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _vms[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _vms[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _vms[vk])
                self._add_resource_requirements(_vgroup, _vms[vk])

                del _vms[vk]

            elif vk in _volumes.keys():
                _vgroup.subvgroups[vk] = _volumes[vk]
                _volumes[vk].survgroup = _vgroup

                _affinity_map[vk] = _vgroup

                self._add_implicit_diversity_groups(_vgroup, _volumes[vk].diversity_groups)
                self._add_implicit_exclusivity_groups(_vgroup, _volumes[vk].exclusivity_groups)
                self._add_memberships(_vgroup, _volumes[vk])
                self._add_resource_requirements(_vgroup, _volumes[vk])

                del _volumes[vk]

            elif vk in _vgroups.keys():
                vg = _vgroups[vk]

                if LEVELS.index(vg.level) > LEVELS.index(_vgroup.level):
                    self.status = "grouping scope: nested group's level is higher"
                    return False

                if vg.vgroup_type == "DIV" or vg.vgroup_type == "EX":
                    if self._merge_subgroups(_vgroup, vg.subvgroups, _vms, _volumes, _vgroups, _elements, _affinity_map) is False:
                        return False
                    del _vgroups[vk]
                else:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        if self._get_subgroups(vg, _elements, _vgroups, _vms, _volumes, _affinity_map) is False:
                            return False

                        _vgroup.subvgroups[vk] = vg
                        vg.survgroup = _vgroup

                        _affinity_map[vk] = _vgroup

                        self._add_implicit_diversity_groups(_vgroup, vg.diversity_groups)
                        self._add_implicit_exclusivity_groups(_vgroup, vg.exclusivity_groups)
                        self._add_memberships(_vgroup, vg)
                        self._add_resource_requirements(_vgroup, vg)

                        del _vgroups[vk]
            else:
                if vk not in _affinity_map.keys():
                    self.status = "invalid resource = " + vk
                    return False

                if _affinity_map[vk].uuid != _vgroup.uuid:
                    if self._exist_in_subgroups(vk, _vgroup) is None:
                        self._set_implicit_grouping(vk, _vgroup, _affinity_map, _vgroups)

        return True

    def _add_implicit_diversity_groups(self, _vgroup, _diversity_groups):
        for dz, level in _diversity_groups.iteritems():
            if LEVELS.index(level) >= LEVELS.index(_vgroup.level):
                _vgroup.diversity_groups[dz] = level

    def _add_implicit_exclusivity_groups(self, _vgroup, _exclusivity_groups):
        for ex, level in _exclusivity_groups.iteritems():
            l = level.split(":", 1)[0]
            if LEVELS.index(l) >= LEVELS.index(_vgroup.level):
                _vgroup.exclusivity_groups[ex] = level

    def _add_resource_requirements(self, _vgroup, _v):
        if isinstance(_v, VM):
            _vgroup.vCPUs += _v.vCPUs
            _vgroup.mem += _v.mem
            _vgroup.local_volume_size += _v.local_volume_size
        # elif isinstance(_v, Volume):
        #     if _v.volume_class in _vgroup.volume_sizes.keys():
        #         _vgroup.volume_sizes[_v.volume_class] += _v.volume_size
        #     else:
        #         _vgroup.volume_sizes[_v.volume_class] = _v.volume_size
        elif isinstance(_v, VGroup):
            _vgroup.vCPUs += _v.vCPUs
            _vgroup.mem += _v.mem
            _vgroup.local_volume_size += _v.local_volume_size
            for vc in _v.volume_sizes.keys():
                if vc in _vgroup.volume_sizes.keys():
                    _vgroup.volume_sizes[vc] += _v.volume_sizes[vc]
                else:
                    _vgroup.volume_sizes[vc] = _v.volume_sizes[vc]

    def _add_memberships(self, _vgroup, _v):
        if isinstance(_v, VM) or isinstance(_v, VGroup):
            for extra_specs in _v.extra_specs_list:
                _vgroup.extra_specs_list.append(extra_specs)

            if isinstance(_v, VM) and _v.availability_zone is not None:
                if _v.availability_zone not in _vgroup.availability_zone_list:
                    _vgroup.availability_zone_list.append(_v.availability_zone)

            if isinstance(_v, VGroup):
                for az in _v.availability_zone_list:
                    if az not in _vgroup.availability_zone_list:
                        _vgroup.availability_zone_list.append(az)

            '''
            for hgk, hg in _v.host_aggregates.iteritems():
                _vgroup.host_aggregates[hgk] = hg
            '''

    # Take vk's most top parent as a s_vg's child vgroup
    def _set_implicit_grouping(self, _vk, _s_vg, _affinity_map, _vgroups):
        t_vg = _affinity_map[_vk]  # where _vk currently belongs to

        if t_vg.uuid in _affinity_map.keys():  # if the parent belongs to the other parent vgroup
            self._set_implicit_grouping(t_vg.uuid, _s_vg, _affinity_map, _vgroups)

        else:
            if LEVELS.index(t_vg.level) > LEVELS.index(_s_vg.level):
                t_vg.level = _s_vg.level
                '''
                self.status = "Grouping scope: sub-group's level is larger"
                return False
                '''

            if self._exist_in_subgroups(t_vg.uuid, _s_vg) is None:
                _s_vg.subvgroups[t_vg.uuid] = t_vg
                t_vg.survgroup = _s_vg

                _affinity_map[t_vg.uuid] = _s_vg

                self._add_implicit_diversity_groups(_s_vg, t_vg.diversity_groups)
                self._add_implicit_exclusivity_groups(_s_vg, t_vg.exclusivity_groups)
                self._add_memberships(_s_vg, t_vg)
                self._add_resource_requirements(_s_vg, t_vg)

                del _vgroups[t_vg.uuid]

    def _exist_in_subgroups(self, _vk, _vg):
        containing_vg_uuid = None
        for vk, v in _vg.subvgroups.iteritems():
            if vk == _vk:
                containing_vg_uuid = _vg.uuid
                break
            else:
                if isinstance(v, VGroup):
                    containing_vg_uuid = self._exist_in_subgroups(_vk, v)
                    if containing_vg_uuid is not None:
                        break
        return containing_vg_uuid

    def _set_vgroup_links(self, _vgroup, _vgroups, _vms, _volumes):
        for _, svg in _vgroup.subvgroups.iteritems():  # currently, not define vgroup itself in pipe
            if isinstance(svg, VM):
                for vml in svg.vm_list:
                    found = False
                    for _, tvgroup in _vgroups.iteritems():
                        containing_vg_uuid = self._exist_in_subgroups(vml.node.uuid, tvgroup)
                        if containing_vg_uuid is not None:
                            found = True
                            if containing_vg_uuid != _vgroup.uuid and \
                               self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
                                self._add_nw_link(vml, _vgroup)
                            break
                    if found is False:
                        for tvk in _vms.keys():
                            if tvk == vml.node.uuid:
                                self._add_nw_link(vml, _vgroup)
                                break
                for voll in svg.volume_list:
                    found = False
                    for _, tvgroup in _vgroups.iteritems():
                        containing_vg_uuid = self._exist_in_subgroups(voll.node.uuid, tvgroup)
                        if containing_vg_uuid is not None:
                            found = True
                            if containing_vg_uuid != _vgroup.uuid and \
                               self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
                                self._add_io_link(voll, _vgroup)
                            break
                    if found is False:
                        for tvk in _volumes.keys():
                            if tvk == voll.node.uuid:
                                self._add_io_link(voll, _vgroup)
                                break
            # elif isinstance(svg, Volume):
            #     for vml in svg.vm_list:
            #         found = False
            #         for _, tvgroup in _vgroups.iteritems():
            #             containing_vg_uuid = self._exist_in_subgroups(vml.node.uuid, tvgroup)
            #             if containing_vg_uuid is not None:
            #                 found = True
            #                 if containing_vg_uuid != _vgroup.uuid and \
            #                    self._exist_in_subgroups(containing_vg_uuid, _vgroup) is None:
            #                     self._add_io_link(vml, _vgroup)
            #                 break
            #         if found is False:
            #             for tvk in _vms.keys():
            #                 if tvk == vml.node.uuid:
            #                     self._add_io_link(vml, _vgroup)
            #                     break
            elif isinstance(svg, VGroup):
                self._set_vgroup_links(svg, _vgroups, _vms, _volumes)

                for svgl in svg.vgroup_list:  # svgl is a link to VM or Volume
                    if self._exist_in_subgroups(svgl.node.uuid, _vgroup) is None:
                        self._add_nw_link(svgl, _vgroup)
                        self._add_io_link(svgl, _vgroup)

    def _add_nw_link(self, _link, _vgroup):
        _vgroup.nw_bandwidth += _link.nw_bandwidth
        vgroup_link = self._get_vgroup_link(_link, _vgroup.vgroup_list)
        if vgroup_link is not None:
            vgroup_link.nw_bandwidth += _link.nw_bandwidth
        else:
            link = VGroupLink(_link.node)  # _link.node is VM
            link.nw_bandwidth = _link.nw_bandwidth
            _vgroup.vgroup_list.append(link)

    def _add_io_link(self, _link, _vgroup):
        _vgroup.io_bandwidth += _link.io_bandwidth
        vgroup_link = self._get_vgroup_link(_link, _vgroup.vgroup_list)
        if vgroup_link is not None:
            vgroup_link.io_bandwidth += _link.io_bandwidth
        else:
            link = VGroupLink(_link.node)
            link.io_bandwidth = _link.io_bandwidth
            _vgroup.vgroup_list.append(link)

    def _get_vgroup_link(self, _link, _vgroup_link_list):
        vgroup_link = None
        for vgl in _vgroup_link_list:
            if vgl.node.uuid == _link.node.uuid:
                vgroup_link = vgl
                break
        return vgroup_link

    def _set_vgroup_weight(self, _vgroup):
        # success = True

        if self.resource.CPU_avail > 0:
            _vgroup.vCPU_weight = float(_vgroup.vCPUs) / float(self.resource.CPU_avail)
        else:
            if _vgroup.vCPUs > 0:
                _vgroup.vCPU_weight = 1.0
            else:
                _vgroup.vCPU_weight = 0.0

        if self.resource.mem_avail > 0:
            _vgroup.mem_weight = float(_vgroup.mem) / float(self.resource.mem_avail)
        else:
            if _vgroup.mem > 0:
                _vgroup.mem_weight = 1.0
            else:
                _vgroup.mem_weight = 0.0

        if self.resource.local_disk_avail > 0:
            _vgroup.local_volume_weight = float(_vgroup.local_volume_size) / float(self.resource.local_disk_avail)
        else:
            if _vgroup.local_volume_size > 0:
                _vgroup.local_volume_weight = 1.0
            else:
                _vgroup.local_volume_weight = 0.0

        vol_list = []
        for vol_class in _vgroup.volume_sizes.keys():
            vol_list.append(_vgroup.volume_sizes[vol_class])

        if self.resource.disk_avail > 0:
            _vgroup.volume_weight = float(sum(vol_list)) / float(self.resource.disk_avail)
        else:
            if sum(vol_list) > 0:
                _vgroup.volume_weight = 1.0
            else:
                _vgroup.volume_weight = 0.0

        bandwidth = _vgroup.nw_bandwidth + _vgroup.io_bandwidth

        if self.resource.nw_bandwidth_avail > 0:
            _vgroup.bandwidth_weight = float(bandwidth) / float(self.resource.nw_bandwidth_avail)
        else:
            if bandwidth > 0:
                _vgroup.bandwidth_weight = 1.0
            else:
                _vgroup.bandwidth_weight = 0.0

        for _, svg in _vgroup.subvgroups.iteritems():
            if isinstance(svg, VGroup):
                self._set_vgroup_weight(svg)
