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
Restarter.py

Author: Joe D'Andrea
Created: 26 June 2014
Contact: jdandrea@research.att.com
'''

from oslo_log import log as logging

from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import scheduler
from heat.engine.resources import signal_responder
from heat.engine import resource
from heat.engine import support

LOG = logging.getLogger(__name__)


class Restarter(signal_responder.SignalResponder):
    PROPERTIES = (
        INSTANCE_ID,
    ) = (
        'instance_id',
    )

    ATTRIBUTES = (
        ALARM_URL,
    ) = (
        'alarm_url',
    )

    properties_schema = {
        INSTANCE_ID: properties.Schema(
            properties.Schema.STRING,
            _('Instance ID to be restarted.'),
            required=True
        ),
    }

    attributes_schema = {
        ALARM_URL: attributes.Schema(
            _("A signed url to handle the alarm (Heat extension).")
        )
    }

    def _find_resource(self, resource_id):
        '''
        Return the resource with the specified instance ID, or None if it
        cannot be found.
        '''
        for resource in self.stack.itervalues():
            if resource.resource_id == resource_id:
                return resource
        return None

    def handle_create(self):
        super(Restarter, self).handle_create()
        self.resource_id_set(self._get_user_id())

    def handle_signal(self, details=None):
        if self.action in (self.SUSPEND, self.DELETE):
            msg = _('Cannot signal resource during %s') % self.action
            raise Exception(msg)

        if details is None:
            alarm_state = 'insufficient data'
        else:
            alarm_state = details.get('state', 'insufficient data').lower()

        LOG.info(_('%(name)s Alarm, new state %(state)s')
                 % {'name': self.name, 'state': alarm_state})

        if alarm_state != 'insufficient data':
            return

        victim = self._find_resource(self.properties[self.INSTANCE_ID])
        if victim is None:
            LOG.info(_('%(name)s Alarm, can not find instance %(instance)s')
                     % {'name': self.name,
                        'instance': self.properties[self.INSTANCE_ID]})
            return

        client = self.nova()
        servers = client.servers.list()
        server_victim = None
        for server in servers:
            if server.id == victim.resource_id:
                server_victim = server
                break

        if server_victim == None:
            LOG.info(_('%(name)s Alarm, can\'t find/restart resource: '
                       '%(victim)s')
                       % {'name': self.name, 'victim': victim.name})
            return

        if server_victim.status == 'HARD_REBOOT':
            LOG.info(_('%(name)s Alarm, hard reboot already in '
                       'progress: %(victim)s')
                       % {'name': self.name, 'victim': victim.name})
        else:
            LOG.info(_('%(name)s Alarm, restarting resource: '
                       '%(victim)s')
                       % {'name': self.name, 'victim': victim.name})
            response = server_victim.reboot('HARD')
        return

    def _resolve_attribute(self, name):
        '''
        heat extension: "AlarmUrl" returns the url to post to the policy
        when there is an alarm.
        '''
        if name == self.ALARM_URL and self.resource_id is not None:
            return unicode(self._get_signed_url())

class RestarterDeprecated(Restarter):
    """
    DEPRECATED: Use ATT::CloudQoS::Restarter instead.
    """

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS is now ATT::CloudQoS.')
    )

def resource_mapping():
    """Map names to resources."""
    return {
       'ATT::QoS::Restarter': RestarterDeprecated,
       'ATT::CloudQoS::Restarter': Restarter
    }
