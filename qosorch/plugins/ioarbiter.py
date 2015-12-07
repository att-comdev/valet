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
from oslo_log import log as logging
from qosorch import plugin

try:
    # Kilo onward
    from heat.engine.resources.openstack.cinder.volume import CinderVolumeAttachment
except ImportError:
    # Icehouse and Juno
    from heat.engine.resources.volume import CinderVolumeAttachment

LOG = logging.getLogger(__name__)


class IOArbiter(plugin.ReservationPlugin):
    ''' IOArbiter plugin '''

    def __init__(self, reservation):
        super(IOArbiter, self).__init__(reservation)

    #@property
    #def expects_encoded_payload(self):
    #    # IOArbiter DOES want encoded payloads.
    #    return True

    @property
    def service_name(self):
        return 'IOArbiter'

    def send_ioarbiter_commands(self, params, commands):
        """Send commands to IOArbiter."""

        # Merge params and credentials into a payload.
        # TODO: Get credentials from heat.conf and existing settings.
        credentials = {
            'os_username': 'ioarbiter',
            'os_password': 'w!seguys',
            'os_tenant_name': 'demo',
            'os_region_name': 'regionOne',
            'os_auth_url': self.reservation.context.auth_url,
        }
        payload = params.copy()
        payload.update(credentials)

        for key, value in commands.iteritems():
            #payload['num'] = ('%(key)s,%(value)s' % {
            #    'key': key, 'value': value
            #})
            payload['type'] = key
            payload['num'] = value

            # IOArbiter does not return status. We just call the API for now.
            self.call_api(payload=payload, content_type='application/json')

        # TODO: Uncomment once IOArbiter provides JSON output.
        #try:
        #    if output:
        #        result = simplejson.loads(output)
        #    #if result['endstate']['status'] != 'OK':
        #    #    try again 3x
        #    #self.resource_id_set(result['reqstate'][0]['details']['id'])
        #except:
        #    print "%s Response must be valid JSON." % self.service_name
        #    raise

        # TODO: Process result as appropriate
        # {"status":"ok","desc":"rules are sent"}
        #self.resource_id_set(server_id+'-'+volume_id)

    def handle_create(self, resource_ids):
        """Reserve server-to-volume-attachment bandwidth via IOArbiter."""

        if len(resource_ids) != 1:
            return

        # In Cinder, Volume and VolumeAttachment resources have the same UUID!
        # Thus we need to tell find_resource to match on a specific type.
        res_id = resource_ids[0]
        res = self.find_resource(res_id, 'OS::Cinder::VolumeAttachment')
        if res:
            server_id = res.properties.get(CinderVolumeAttachment.INSTANCE_ID)
            volume_id = res.properties.get(CinderVolumeAttachment.VOLUME_ID)
        else:
            # Do nothing
            return

        bandwidth = self.bandwidth

        # Build the IOArbiter request payload
        params = {
            'vm': server_id,
            'share': volume_id,
        }

        # Bandwidth is bps. We convert to Kbps here for IOArbiter.
        minmax = '[' + str(int(bandwidth['min'])) + ',' + \
                       str(int(bandwidth['max'])) + ']'

        commands = {
            'min-bw-read': minmax,
            'min-bw-write': minmax,
            'max-bw-read': minmax,
            'max-bw-write': minmax,
        }

        self.send_ioarbiter_commands(params, commands)

    def handle_delete(self):
        """Reset server-to-volume-attachment bandwidth to 0 via IOArbiter."""
        #if self.reservation.resource_id is None:
        #    return
        data = self.db_get()
        if not data:
            return

        try:
            request = data['request']
            params = {
                'vm': request['vm'],
                'share': request['share'],
            }

            minmax = '[0,0]'
            commands = {
                'min-bw-read': minmax,
                'min-bw-write': minmax,
                'max-bw-read': minmax,
                'max-bw-write': minmax,
            }

            self.send_ioarbiter_commands(params, commands)

        except:
            #self.reservation.resource_id_set(None)
            return

        #self.reservation.resource_id_set(None)

    # TODO: Add Get Attribute support that dips into the JSON output

    def _resolve_attribute(self, name):
        '''Resolve attribute.'''
        data = self.db_get()
        if not data:
            return
        return data

def register():
    '''Map names to classes.'''
    return {'ioarbiter': IOArbiter}
