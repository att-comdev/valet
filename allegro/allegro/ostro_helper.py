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
import uuid

from pecan import conf
import simplejson

from allegro.models import Group
from allegro.models import PlacementRequest
from allegro.models import PlacementResult
from allegro.models import Query

RESOURCE_TYPE = 'ATT::CloudQoS::ResourceGroup'


class Ostro(object):
    '''Ostro optimization engine helper class.'''

    args = None
    request = None
    response = None
    error_uri = None
    tenant_id = None

    tries = None  # Number of times to poll for placement.
    interval = None  # Interval in seconds to poll for placement.

    # TODO: Make debug mode a setting. Write dump file to a log.
    debug = True
    debug_file = '/tmp/allegro-dump.txt'

    def __init__(self):
        self.tries = conf.ostro.get('tries', 10)
        self.interval = conf.ostro.get('interval', 1)

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

    def _prepare_resources(self, resources):
        '''
        Pre-digests resource data for use by Ostro.
        Maps Heat resource names to Orchestration UUIDs.
        Ensures exclusivity groups exist and have tenant_id as a member.
        '''
        mapping = self._build_uuid_map(resources)
        ostro_resources = self._map_names_to_uuids(mapping, resources)
        self._sanitize_resources(ostro_resources)

        verify_error = self._verify_exclusivity_groups(
            ostro_resources, self.tenant_id)
        if type(verify_error) is dict:
            return verify_error
        return {'resources': ostro_resources}

    def _sanitize_resources(self, resources):
        '''Ensure lowercase keys at the top level of each resource.'''
        for res in resources.itervalues():
            for key in list(res.keys()):
                if not key.islower():
                    res[key.lower()] = res.pop(key)
        return resources

    # TODO: This really belongs in allegro-engine once it exists.
    def _send(self, stack_id, request):
        ''''Send request.'''

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
        response = {
            'status': {
                'type': 'error',
                'message': 'Timed out waiting for response.',
            }
        }
        self.error_uri = '/errors/server_error'
        return simplejson.dumps(response)

    def _verify_exclusivity_groups(self, resources, tenant_id):
        '''
        Returns an error status dict if a nonexistant exclusivity group
        is found or if the tenant is not a member. Returns None if ok.
        '''
        for res in resources.itervalues():
            res_type = res.get('type')
            if res_type == RESOURCE_TYPE:
                properties = res.get('properties')
                relationship = properties.get('relationship')
                if relationship.lower() == 'exclusivity':
                    group_name = properties.get('name')
                    group = Group.query.filter_by(  # pylint: disable=E1101
                        name=group_name).first()
                    if not group:
                        message = "Exclusivity group '%s' not found" % \
                                  (group_name)
                        self.error_uri = '/errors/not_found'
                    elif group and tenant_id not in group.members:
                        message = "Tenant ID %s not a member of " \
                                  "exclusivity group '%s' (%s)" % \
                                  (self.tenant_id, group.name, group.id)
                        self.error_uri = '/errors/conflict'
                    if message:
                        response = {
                            'status': {
                                'type': 'error',
                                'message': message,
                            }
                        }
                        return response

    def build_request(self, **kwargs):
        '''
        Build an Ostro request. If False is returned,
        the response attribute contains status as to the error.
        '''

        # TODO: Refactor this into create and update methods?
        self.args = kwargs.get('args')
        self.tenant_id = kwargs.get('tenant_id')
        self.response = None
        self.error_uri = None

        resources = self.args['resources']
        if 'resources_update' in self.args:
            action = 'update'
            resources_update = self.args['resources_update']
        else:
            action = 'create'
            resources_update = None

        # If we get any status in the response, it's an error. Bail.
        self.response = self._prepare_resources(resources)
        if 'status' in self.response:
            return False

        self.request = {
            "version": "1.0",
            "action": action,
            "resources": self.response['resources'],
            "stack_id": self.args['stack_id'],
        }

        if resources_update:
            # If we get any status in the response, it's an error. Bail.
            self.response = self._prepare_resources(resources_update)
            if 'status' in self.response:
                return False
            if ostro_resources_update:
                self.request['resources_update'] = ostro_resources_update

        return True

    def ping(self):
        '''Send a ping request and obtain a response.'''
        stack_id = str(uuid.uuid4())
        self.args = { 'stack_id': stack_id }
        self.response = None
        self.error_uri = None
        self.request = {
            "version": "1.0",
            "action": "ping",
            "stack_id": stack_id,
        }

    def replan(self, **kwargs):
        '''Replan a placement.'''
        self.args = kwargs.get('args')
        self.response = None
        self.error_uri = None
        self.request = {
            "version": "1.0",
            "action": "replan",
            "stack_id": self.args['stack_id'],
            "locations": self.args['locations'],
            "orchestration_id": self.args['orchestration_id'],
            "exclusions": self.args['exclusions'],
        }

    def send(self):
        '''Send the request and obtain a response.'''
        request_json = simplejson.dumps(
            [self.request], sort_keys=True, indent=2 * ' '
        )

        if self.debug:
            self._log(request_json, 'Payload')

        # TODO: Pass timeout value?
        result = self._send(self.args['stack_id'], request_json)

        if self.debug:
            self._log(result, 'Result', append=True)

        self.response = simplejson.loads(result)

        status_type = self.response['status']['type']
        if status_type != 'ok':
            self.error_uri = '/errors/server_error'

        return self.response
