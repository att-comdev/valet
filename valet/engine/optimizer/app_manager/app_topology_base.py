#!/bin/python


LEVELS = ["host", "rack", "cluster"]


class VGroup(object):
    ''' do not consider bandwidth and Volume request at this version. vgroup represents affinity group '''

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.vgroup_type = "AFF"       # Support Affinity group at this version
        self.level = None              # host, rack, or cluster

        self.survgroup = None          # where this vgroup belong to
        self.subvgroups = {}           # child vgroups

        self.diversity_groups = {}     # cumulative diversity/exclusivity group
        self.exclusivity_groups = {}   # over this level. key=name, value=level

        self.availability_zone_list = []
        self.extra_specs_list = []      # cumulative extra_specs

        self.vCPUs = 0
        self.mem = 0                   # MB
        self.local_volume_size = 0     # GB

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1

        self.host = None

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        subvgroup_list = []
        for vk in self.subvgroups.keys():
            subvgroup_list.append(vk)

        return {'name': self.name,
                'status': self.status,
                'vgroup_type': self.vgroup_type,
                'level': self.level,
                'survgroup': survgroup_id,
                'subvgroup_list': subvgroup_list,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': self.availability_zone_list,
                'extra_specs_list': self.extra_specs_list,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'host': self.host}


class VM(object):
    ''' do not consider bandwidth request at this version '''

    def __init__(self, _app_uuid, _uuid):
        self.app_uuid = _app_uuid
        self.uuid = _uuid
        self.name = None

        self.status = "requested"

        self.survgroup = None          # VGroup where this vm belongs to

        self.diversity_groups = {}
        self.exclusivity_groups = {}

        self.availability_zone = None
        self.extra_specs_list = []

        self.flavor = None
        self.vCPUs = 0
        self.mem = 0                  # MB
        self.local_volume_size = 0    # GB

        self.vCPU_weight = -1
        self.mem_weight = -1
        self.local_volume_weight = -1

        self.host = None              # where this vm is placed

    def get_json_info(self):
        survgroup_id = None
        if self.survgroup is None:
            survgroup_id = "none"
        else:
            survgroup_id = self.survgroup.uuid

        availability_zone = None
        if self.availability_zone is None:
            availability_zone = "none"
        else:
            availability_zone = self.availability_zone

        return {'name': self.name,
                'status': self.status,
                'survgroup': survgroup_id,
                'diversity_groups': self.diversity_groups,
                'exclusivity_groups': self.exclusivity_groups,
                'availability_zones': availability_zone,
                'extra_specs_list': self.extra_specs_list,
                'flavor': self.flavor,
                'cpus': self.vCPUs,
                'mem': self.mem,
                'local_volume': self.local_volume_size,
                'cpu_weight': self.vCPU_weight,
                'mem_weight': self.mem_weight,
                'local_volume_weight': self.local_volume_weight,
                'host': self.host}
