# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import requests

from oslo_log import log as logging

from cinder.i18n import _LE, _LW
from cinder.openstack.common.scheduler import filters
from qosorch import allegro_api

LOG = logging.getLogger(__name__)


class AllegroFilter(filters.BaseHostFilter):
    """Filter on Allegro assignment."""

    # Host state does not change within a request
    run_filter_once_per_request = True

    def __init__(self):
        self.api = allegro_api.AllegroAPIWrapper()

    def _is_same_host(self, host, location):
        host_name = host.split('@')[0]
        location_name = location.split('@')[0]
        return host_name == location_name

    # TODO: Factor out common code to a qosorch library
    def filter_all(self, filter_obj_list, filter_properties):
        hints_key = 'scheduler_hints'
        uuid_key = 'heat_resource_uuid'

        yield_all = False
        location = None
        uuid = None

        # If we don't have hints to process, yield (pass) all hosts
        # so other plugins have a fair shot. TODO: This will go away
        # once ostro can handle on-the-fly scheduling, except for cases
        # where we can't reach Allegro at all, then we may opt to fail
        # all hosts depending on a TBD config flag.
        if not filter_properties.get(hints_key, {}).has_key(uuid_key):
            LOG.debug("Lifecycle Scheduler Hints not found, Skipping.")
            yield_all = True
        else:
            uuid = filter_properties[hints_key][uuid_key]
            placement = self.api.placement(uuid)

            # TODO: Ostro will give a matching format (e.g., mtmac2@lvm#LVM)
            # Cinder's format is host@volume_group#pool
            if placement.get('location'):
                location = placement['location']

            if not location:
                LOG.debug("Placement unknown for resource: %s." % uuid)
                yield_all = True

        # Yield the hosts that pass.
        # Like the Highlander, there can (should) be only one.
        # TODO: If no hosts pass, do alternate scheduling.
        # If we can't be sure of a placement, yield all hosts for now.
        for obj in filter_obj_list:
            if location:
                match = self._is_same_host(obj.host, location)
                if match:
                    LOG.debug("Placement for resource %s: %s." % \
                              (uuid, obj.host))
            if yield_all or match:
                yield obj
        
    # Do nothing here. Let filter_all handle it in one swell foop.
    def host_passes(self, host_state, filter_properties):
        """Return True if host has sufficient capacity."""
        return False
