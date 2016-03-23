#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.3: Mar. 15, 2016
#
# Functions 
#
#################################################################################################################


import six
import sys

import openstack_utils

sys.path.insert(0, '../app_manager')
from app_topology_base import VM


_SCOPE = 'aggregate_instance_extra_specs'


class AggregateInstanceExtraSpecsFilter:
    """AggregateInstanceExtraSpecsFilter works with InstanceType records."""

    # Aggregate data and instance type does not change within a request
    run_filter_once_per_request = True

    def __init__(self, _logger):
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        """Return a list of hosts that can create instance_type
        Check that the extra specs associated with the instance type match
        the metadata provided by aggregates.  If not present return False.
        """

        # If 'extra_specs' is not present or extra_specs are empty then we
        # need not proceed further
        extra_specs_list = []
        for extra_specs in _v.extra_specs_list:
            if "host_aggregates" not in extra_specs.keys():
                extra_specs_list.append(extra_specs)

        if len(extra_specs_list) == 0:
            return True

        metadatas = openstack_utils.aggregate_metadata_get_by_host(_level, _host)

        matched_logical_group_list = []
        for extra_specs in extra_specs_list:
            for lgk, metadata in metadatas.iteritems():
                if self._match_metadata(_host.get_resource_name(_level), lgk, extra_specs, metadata) == True:
                    matched_logical_group_list.append(lgk)
                    break
            else:
                return False

        for extra_specs in _v.extra_specs_list:
            if "host_aggregates" in extra_specs.keys():
                extra_specs["host_aggregates"] = matched_logical_group_list
                break
        else:
            host_aggregate_extra_specs = {}
            host_aggregate_extra_specs["host_aggregates"] = matched_logical_group_list
            _v.extra_specs_list.append(host_aggregate_extra_specs)

        return True
        
    def _match_metadata(self, _h_name, _lg_name, _extra_specs, _metadata):
        for key, req in six.iteritems(_extra_specs):
            # Either not scope format, or aggregate_instance_extra_specs scope
            scope = key.split(':', 1)
            if len(scope) > 1:
                if scope[0] != _SCOPE:
                    continue
                else:
                    del scope[0]
            key = scope[0]
       
            if key == "host_aggregates":
                continue

            aggregate_vals = _metadata.get(key, None)
            if not aggregate_vals:
                self.logger.debug("key (" + key + ") not exists in logical_group (" + _lg_name + ") " + \
                                  " of host (" + _h_name + ")")
                return False
            for aggregate_val in aggregate_vals:
                if openstack_utils.match(aggregate_val, req):
                    break
            else:
                self.logger.debug("key (" + key + ")'s value (" + req + ") not exists in logical_group " + \
                                  "(" + _lg_name + ") " + " of host (" + _h_name + ")")
                return False

        return True


# NOTE: originally, OpenStack used the metadata of host_aggregate
class AvailabilityZoneFilter:
    """Filters Hosts by availability zone.
    Works with aggregate metadata availability zones, using the key
    'availability_zone'
    Note: in theory a compute node can be part of multiple availability_zones
    """

    # Availability zones do not change within a request
    run_filter_once_per_request = True

    def __init__(self, _logger):
        self.logger = _logger

    def host_passes(self, _level, _host, _v):
        az_request_list = []
        if isinstance(_v, VM):
            az_request_list.append(_v.availability_zone)
        else:
            for az in _v.availability_zone_list:
                az_request_list.append(az)

        if len(az_request_list) == 0:
            return True

        #metadatas = openstack_utils.aggregate_metadata_get_by_host(_level, _host, key='availability_zone')
        availability_zone_list = openstack_utils.availability_zone_get_by_host(_level, _host)

        for azr in az_request_list:
            if azr not in availability_zone_list:
                self.logger.debug("AZ (" + azr + ") not exists in host " + \
                                  "(" + _host.get_resource_name(_level) + ")")
                return False

        return True

        '''
        if 'availability_zone' in metadata:
            hosts_passes = availability_zone in metadata['availability_zone']
            host_az = metadata['availability_zone']
        else:
            hosts_passes = availability_zone == CONF.default_availability_zone
            host_az = CONF.default_availability_zone

        if not hosts_passes:
            LOG.debug("Availability Zone '%(az)s' requested. "
                      "%(host_state)s has AZs: %(host_az)s",
                      {'host_state': host_state,
                       'az': availability_zone,
                       'host_az': host_az})

        return hosts_passes
        '''



# Unit test

