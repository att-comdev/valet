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

import time

import simplejson

from allegro.models.music import PlacementRequest
from allegro.models.music import PlacementResult
from allegro.models.music import Query


class Ostro(object):
    '''Ostro optimization engine helper class.'''

    def __init__(self, **kwargs):
        self.args = kwargs
        self.response = None

        self.tries = 10  # Number of times to poll for placement.
        self.interval = 1  # Interval in seconds to poll for placement.

        self.debug = True
        self.debug_file = '/tmp/allegro-dump.txt'

        resources = self.args['resources']
        if 'resources_update' in self.args:
            action = 'update'
            resources_update = self.args['resources_update']
        else:
            action = 'create'
            resources_update = {}

        mapping = self._build_uuid_map(resources)
        ostro_resources = self._map_names_to_uuids(mapping, resources)
        self._sanitize_resources(ostro_resources)

        mapping = self._build_uuid_map(resources_update)
        ostro_resources_update = \
            self._map_names_to_uuids(mapping, resources_update)
        self._sanitize_resources(ostro_resources_update)

        self.request = {
            "version": "0.1",
            "action": action,
            "resources": ostro_resources
        }
        if ostro_resources_update:
            self.request['resources_update'] = ostro_resources_update

        self.request["stack_id"] = self.args['stack_id']

    def _build_uuid_map(self, resources):
        '''Build a dict mapping names to UUIDs.'''
        mapping = {}
        for key in resources.iterkeys():
            if 'name' in resources[key]:
                name = resources[key]['name']
                mapping[name] = key
        return mapping

    def _map_names_to_uuids(self, mapping, data):
        '''Map resource names to their UUID equivalents.'''
        if type(data) is dict:
            for key in data.iterkeys():
                if key != 'name':
                    data[key] = self._map_names_to_uuids(mapping, data[key])
        elif type(data) is list:
            for key, value in enumerate(data):
                data[key] = self._map_names_to_uuids(mapping, value)
        elif type(data) is str or type(data) is unicode:
            if data in mapping:
                return mapping[data]
        return data

    # TODO: Log to an actual logging facility and not a tmp file
    def _log(self, text, title, append=False):
        '''Log helper'''
        flag = 'a' if append else 'w'
        log = open(self.debug_file, flag)
        print >>log, "===%s===" % title
        print >>log, text
        log.close()

    # TODO: This really belongs in allegro-engine once it exists.
    def _place(self, stack_id, request):
        ''''Place resources.'''

        # Creating the placement request effectively enqueues it.
        placement_request = PlacementRequest(
            stack_id=stack_id, request=request
        )

        # Wait for a response. Unfortunately this is blocking.
        for tries in range(self.tries, 0, -1):
            query = Query(PlacementResult)
            placement_result = query.filter_by(stack_id=stack_id).first()
            if placement_result:
                placement = placement_result.placement
                placement_result.delete()
                return placement
            else:
                time.sleep(self.interval)
        return '{ \
            "status": { \
                "type": "error", \
                "message": "Timed out waiting for placement result." \
            } \
        }'

    def _sanitize_resources(self, resources):
        '''Ensure lowercase keys at the top level of each resource.'''
        for res in resources.itervalues():
            for key in list(res.keys()):
                if not key.islower():
                    res[key.lower()] = res.pop(key)
        return resources

    def send(self):
        '''Send the planning request and obtain a response.'''
        request_json = simplejson.dumps(
            [self.request], sort_keys=True, indent=2 * ' '
        )

        if self.debug:
            self._log(request_json, 'Payload')

        # TODO: Pass timeout value
        result = self._place(self.args['stack_id'], request_json)

        if self.debug:
            self._log(result, 'Result', append=True)

        self.response = simplejson.loads(result)
        return self.response
