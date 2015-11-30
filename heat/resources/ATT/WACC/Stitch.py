'''
Stitch.py

Author: Joe D'Andrea
Created: 18 December 2014
Contact: jdandrea@research.att.com
'''

import pickle
import simplejson
import urllib2

from oslo_config import cfg
from oslo_log import log as logging

from heat.common import exception
from heat.common.i18n import _
from heat.db import api as db_api
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource

LOG = logging.getLogger(__name__)


class Stitch(resource.Resource):
    '''
    A stitch describes the connection of two or more networks.
    Each network is described by a subnet UUID, a tenant ID,
    a WAN subnet UUID, and a Keystone token for authentication.

    Properties:

     networks:
     - subnet_id: First Subnet UUID
       tenant_id: First Tenant ID
       wan_id: First WAN Subnet UUID
       auth_token: First Keystone token
     - subnet_id: Second Subnet UUID
       tenant_id: Second Tenant ID
       wan_id: Second WAN Subnet UUID
       auth_token: Second Keystone token
     . . .
     - subnet_id: Last Subnet UUID
       tenant_id: Last Tenant ID
       wan_id: Last WAN Subnet UUID
       auth_token: Last Keystone token
    '''

    PROPERTIES = (
        NETWORKS,
    ) = (
        'networks',
    )

    _NETWORK_KEYS = (
        SUBNET_ID, TENANT_ID, WAN_ID, AUTH_TOKEN,
    ) = (
        "subnet_id", "tenant_id", "wan_id", "auth_token",
    )

    properties_schema = {
        NETWORKS: properties.Schema(
            properties.Schema.LIST,
            _('List of two or more networks to stitch together.'),
            schema=properties.Schema(
                properties.Schema.MAP,
                schema={
                    SUBNET_ID: properties.Schema(
                        properties.Schema.STRING,
                        _('Subnet UUID.'),
                        required=True
                    ),
                    TENANT_ID: properties.Schema(
                        properties.Schema.STRING,
                        _('Tenant ID.'),
                        required=True
                    ),
                    WAN_ID: properties.Schema(
                        properties.Schema.STRING,
                        _('WAN Subnet ID.'),
                        required=True
                    ),
                    AUTH_TOKEN: properties.Schema(
                        properties.Schema.STRING,
                        _('Keystone token.'),
                        required=True
                    ),
                },
            ),
            required=True,
            constraints=[constraints.Length(min=2)],
            update_allowed=True),
    }

    def __init__(self, name, json_snippet, stack):
        super(Stitch, self).__init__(name, json_snippet, stack)
        self._service_name = 'WACC'

    def handle_create(self):
        # Must have at least two networks. We only pass the first two.
        networks = self.properties.get(self.NETWORKS)
        if len(networks) < 2:
            raise exception.Error(_('Must provide at least two '
                                    'networks to stitch together.'))
        payload = {
            'srcToken': networks[0][self.AUTH_TOKEN],
            'srcTenant': networks[0][self.TENANT_ID],
            'srcSubnet': networks[0][self.SUBNET_ID],
            'srcWan': networks[0][self.WAN_ID],
            'dstToken': networks[1][self.AUTH_TOKEN],
            'dstTenant': networks[1][self.TENANT_ID],
            'dstSubnet': networks[1][self.SUBNET_ID],
            'dstWan': networks[1][self.WAN_ID],
        }
        payload_string = simplejson.dumps(payload)
        uri = 'http://lt-jeep.research.att.com:8080/WACC/rest/connections'
        LOG.info(_('Posting %(service)s request: %(uri)s\n'
                   'Payload: %(payload)s' % {
            'service': self._service_name,
            'uri': uri,
            'payload': payload_string,
        }))

        method = 'POST'
        content_type = 'application/x-www-form-urlencoded'

        try:
            request = urllib2.Request(uri, data=payload_string,
                                     headers={'Content-type': content_type})
            request.get_method = lambda: method
            response = urllib2.urlopen(request)
            output_string = response.read()

            # Turn the output into a dict if possible
            output = ''
            try:
                output = simplejson.loads(output_string)
            except simplejson.JSONDecodeError as exc:
                output = output_string

            # Set the request/response for this plugin in the backing store.
            #self.db_set({
            #    'uri': uri,
            #    'request': payload,
            #    'status': response.code,
            #    'response': output,
            #})

            LOG.info(_('%(name)s HTTP Status: %(status)d' % {
                'name': self._service_name,
                'status': response.code,
            }))

            LOG.info(_('%(name)s Response: %(response)s' % {
                'name': self._service_name,
                'response': output_string,
            }))

            response.close()
        except urllib2.URLError as exc:
            message = None
            if hasattr(exc, 'reason'):
                message = _("Failed to reach %(uri)s. Reason: %(reason)s") % {
                    'uri': uri,
                    'reason': exc.reason,
                }
            elif hasattr(exc, 'code'):
                message = _("Request %(uri)s failed. Reason: %(code)s") % {
                    'uri': uri,
                    'code': exc.code,
                }
            if message:
                LOG.warning(_('%(service)s Failure: %(msg)s. Continuing.\n' % {
                    'service': self._service_name,
                    'msg': message,
                }))
            return None
        return
        #self.resource_id_set(self.properties[self.NAME])

    def handle_update(self, json_snippet, templ_diff, prop_diff):
        return
        #self.resource_id_set(self.properties[self.NAME])

    def handle_delete(self):
        return
        #self.resource_id_set(None)

def resource_mapping():
    """Map names to resources."""
    return {'ATT::WACC::Stitch': Stitch}
