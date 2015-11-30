#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

'''
tegu.py

Author: Joe D'Andrea
Created: 8 August 2014
Contact: jdandrea@research.att.com
'''

from datetime import datetime
import simplejson
import time

from oslo_log import log as logging
from qosorch import plugin

from heat.common.i18n import _
from heat.common import exception

LOG = logging.getLogger(__name__)


class Tegu(plugin.ReservationPlugin):
    ''' Tegu plugin '''

    def __init__(self, reservation):
        super(Tegu, self).__init__(reservation)

    #@property
    #def expects_encoded_payload(self):
    #    # Tegu does NOT want encoded payloads. Send as-is.
    #    return False

    @property
    def service_name(self):
        return 'Tegu'

    def handle_create(self, resource_ids):
        """Reserve server-to-server bandwidth via Tegu."""

        if len(resource_ids) != 2:
            return

        res_id1 = resource_ids[0]
        res_id2 = resource_ids[1]
        res1 = self.find_resource(res_id1)
        res2 = self.find_resource(res_id2)
        if not (res1.type() == 'OS::Nova::Server' and
                res2.type() == 'OS::Nova::Server'):
            # Do nothing
            return

        # time: Expiration time as a unix timestamp.
        # Tegu supports dates up through 1/1/2025.
        # Any date past that will be rejected, so use 12/31/2024 23:59:59.
        end_time = "12/31/2024 23:59:59"
        dmy = "%m/%d/%Y %H:%M:%S"
        expire = int(time.mktime(datetime.strptime(end_time, dmy).timetuple()))

        # Build the Tegu request payload
        token_tenant = "%(token)s/%(tenant_id)s" % {
            'token': self.reservation.context.auth_token,
            'tenant_id': self.reservation.context.tenant_id,
        }
        server1 = "%(prefix)s/%(s1)s" % {
            'prefix': token_tenant,
            #'s1': res_id1,
            's1': res1.name,
        }
        server2 = "%(prefix)s/%(s2)s" % {
            'prefix': token_tenant,
            #'s2': res_id2,
            's2': res2.name,
        }

        bandwidth = self.bandwidth

        # Bandwidth is bps. We convert to Mbps here for Tegu.
        payload = "reserve %(bw)s %(sec)d %(s1)s,%(s2)s s-cookie voice" % {
            'bw': str(int(max(bandwidth['min'], bandwidth['max']) * 0.000001)) + 'M',
            'sec': expire,
            's1': server1,
            's2': server2,
        }

        self.call_api(payload=payload)

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
        #
        # {
        #     "endstate": {
        #         "comment": "1 errors processing requests",
        #         "status": "ERROR"
        #     },
        #     "reqstate": [
        #         {
        #             "comment": "reservation rejected: unable to map host name to a known IP address: host unknown: d2af17a5a3d940be81867652cb95491e/0d7db51c-7ba1-4a88-bb05-347a10667b04 maps to an IP, but IP not known to SDNC: d2af17a5a3d940be81867652cb95491e/10.0.2.19",
        #             "request": 1,
        #             "status": "ERROR"
        #         }
        #     ]
        # }

        # {
        #     "endstate": {
        #         "comment": "0 errors processing requests",
        #         "status": "OK"
        #     },
        #     "reqstate": [
        #         {
        #             "comment": "reservation accepted; reservation path has 1 entries",
        #             "details": {
        #                 "bandwin": 1000000000,
        #                 "bandwout": 1000000000,
        #                 "host1": "d2af17a5a3d940be81867652cb95491e/0d7db51c-7ba1-4a88-bb05-347a10667b04:0",
        #                 "host2": "d2af17a5a3d940be81867652cb95491e/4e6f9a59-6099-4cb2-8649-8f5806364f29:0",
        #                 "id": "res6ef5_00002",
        #                 "ptype": "bandwidth",
        #                 "qid": "res6ef5_00002",
        #                 "state": "ACTIVE",
        #                 "time": 327142614
        #             },
        #             "request": 1,
        #             "status": "OK"
        #         }
        #     ]
        # }

        return

    def handle_delete(self):
        """Cancel server-to-server bandwidth reservation via Tegu."""
        #if self.reservation.resource_id is None:
        #    return
        data = self.db_get()
        if not data:
            return

        try:
            response = data['response']
            reservation_id = response['reqstate'][0]['details']['id']
            payload = "reservation %(id)s s-cookie" % {
                'id': reservation_id,
            }

            try:
                self.call_api(payload=payload, method='DELETE')
            except exception:
                pass
        except:
            pass
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
    return {'tegu': Tegu}
