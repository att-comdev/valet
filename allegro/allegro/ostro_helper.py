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

from pecan import conf
from pecan import request, redirect
import simplejson

if str(conf.ostro.version) == '2.0':
    from allegro.models.music import PlacementRequest
    from allegro.models.music import PlacementResult
    from allegro.models.music import Query
elif str(conf.ostro.version) == '1.5':
    from ostro15.planner import Optimization
else:
    from ostro.placement import Optimization


class OstroMusicProxy(object):
    testing = False

    # Request is JSON
    def place(self, stack_id, request):
        # Place it in Music
        self.placement_request = PlacementRequest(
            stack_id=stack_id, request=request
        )

        # Sample result - note changes from Ostro 1.5:
        #
        # Status message has changed from "done" to "success"
        # Version key has been removed
        # resource properties use "host" instead of "availability_zone"
        # host value reverted to host name only (Cinder results removed)
        if self.testing:
            placement = {
                "status": {
                    "message": "success",
                    "type": "ok"
                },
                "resources": {
                    "vm0_uuid": {
                        "properties": {
                            "host": "simr0c9"
                        }
                    },
                    "vm1_uuid": {
                        "properties": {
                            "host": "simr0c9"
                        }
                    },
                    "vm2_uuid": {
                        "properties": {
                            "host": "simr0c10"
                        }
                    }
                }
            }
            placement_json = simplejson.dumps(
                placement, sort_keys=True, indent=2 * ' '
            )
            self.placement_result = PlacementResult(
                stack_id=stack_id, placement=placement_json
            )

        # Now wait for a response. Unfortunately this is blocking.
        # TODO: This really belongs in allegro-engine once it is available..
        while True:
            query = Query(PlacementResult)
            placement_result = query.filter_by(stack_id=stack_id).first()
            if placement_result:
                placement = placement_result.placement
                placement_result.delete()
                return placement
            else:
                time.sleep(1)
        

class Ostro(object):
    def __init__(self, **kwargs):
        self.args = kwargs
        self.response = None

        self.debug = True
        self.debug_file = '/tmp/allegro-dump.txt'

        resources = self.args['resources']
        if 'resources_update' in self.args:
            action = 'update'
            resources_update = self.args['resources_update']
        else:
            action = 'create'
            resources_update = {}

        if str(conf.ostro.version) == '1.5' or \
           str(conf.ostro.version) == '2.0':
            mapping = self._build_uuid_map(resources)
            ostro_resources = self._map_names_to_uuids(mapping, resources)
            self._sanitize_resources(ostro_resources)

            mapping = self._build_uuid_map(resources_update)
            ostro_resources_update = self._map_names_to_uuids(mapping, resources_update)
            self._sanitize_resources(ostro_resources_update)
        else:
            ostro_resources = self._swap_uuid_and_name(resources)
            ostro_resources_update = self._swap_uuid_and_name(resources_update)

        self.request = {
            "version": "0.1",
            "action": action,
            "resources": ostro_resources
        }
        if ostro_resources_update:
            self.request['resources_update'] = ostro_resources_update

        if str(conf.ostro.version) == '1.5' or \
           str(conf.ostro.version) == '2.0':
            self.request["stack_id"] = self.args['stack_id']

    # This is needed until we use the new version of Ostro
    # The older version needs a name where the uuid will go,
    # so we use this helper to swap their places for now.
    def _swap_uuid_and_name(self, resources):
        swapped = {}
        for key in resources.iterkeys():
            res = resources[key].copy()
            name = res.pop("name", None)
            res['uuid'] = key
            swapped[name] = res
        return swapped

    def _build_uuid_map(self, resources):
        mapping = {}
        for key in resources.iterkeys():
            if 'name' in resources[key]:
                name = resources[key]['name']
                mapping[name] = key
        return mapping

    def _map_names_to_uuids(self, mapping, data):
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

    # Ensure all keys are lowercase at the top level of each resource..
    def _sanitize_resources(self, resources):
        for res in resources.itervalues():
            for key in list(res.keys()):
                if not key.islower():
                    res[key.lower()] = res.pop(key)
        return resources

    def _log(self, text, title, append=False):
       flag = 'a' if append else 'w'
       log = open(self.debug_file, flag)
       print >>log, "===%s===" % title
       print >>log, text
       log.close()

    def send(self):
        if str(conf.ostro.version) == '2.0' or \
           str(conf.ostro.version) == '1.5':
            request_json = simplejson.dumps(
                [self.request], sort_keys=True, indent=2 * ' '
            )
        else:
            request_json = simplejson.dumps(
                self.request, sort_keys=True, indent=2 * ' '
            )

        if self.debug:
            self._log(request_json, 'Payload')

        # TODO: Pass timeout value to optimizer
        if str(conf.ostro.version) == '2.0':
            optimizer = OstroMusicProxy()
        elif str(conf.ostro.version) == '1.5':
            optimizer = Optimization(True)
        else:
            optimizer = Optimization()

        if 'update_dc_topology' in dir(optimizer):
            update_result = optimizer.update_dc_topology()
            if update_result != "done":
                # Fake an Ostro response with an error status
                # TODO: Require Ostro to use uniform response payloads.
                response = {
                    'status': {
                        'type': 'error',
                        'message': update_result,
                    }
                }
                return response 

        if str(conf.ostro.version) == '2.0':
            result = optimizer.place(self.args['stack_id'], request_json)
        elif str(conf.ostro.version) == '1.5':
            result = optimizer.place(request_json)
        else:
            result = optimizer.place(request_json, False)

        if self.debug:
            self._log(result, 'Result', append=True)

        self.response = simplejson.loads(result)
        return self.response

if __name__ == "__main__":
    request = {
      "action": "create",
      "resources": {
        "my_instance": {
          "Properties": {
            "flavor": "m1.small",
            "image": "ubuntu12_04",
            "key_name": "demo",
            "name": "my_instance",
            "networks": [{
              "network": "demo-net"
            }]
          },
          "Type": "OS::Nova::Server",
          "uuid": "12de4ad4-011e-4188-93e0-cd6351155506"
        },
        "my_volume": {
          "Properties": {
            "name": "my_volume",
            "size": 1
          },
          "Type": "OS::Cinder::Volume",
          "uuid": "4b21cb8a-f313-4438-8431-e684ce200e3f"
        }
      },
      "version": 0.1
    }

    request_json = simplejson.dumps(
        request, sort_keys=True, indent=2 * ' '
    )
    optimizer = Optimization()
    result = optimizer.place(request_json, False)
    print result
    exit
