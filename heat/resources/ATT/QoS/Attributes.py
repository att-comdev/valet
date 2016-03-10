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
Attributes.py

Author: Joe D'Andrea
Created: 11 June 2015
Contact: jdandrea@research.att.com
'''

from oslo_log import log as logging

from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.engine import support

LOG = logging.getLogger(__name__)


class Attributes(resource.Resource):
    """
    QoS Attributes are used by one or more QoS Reservations.

    This resource has no nutritional value to Heat. It is intended
    for use by holistic placement tools when scheduling an entire
    stack of related resources well in advance of instantiation vs.
    one at a time, each independent of the other.
    """

    _ACCESS_TYPES = (
        SEQUENTIAL, MIXED,
    ) = (
        "sequential", "mixed",
    )

    _NETWORKING_PRIORITIES = (
        VOICE, CONTROL, DATA,
    ) = (
        "voice", "control", "data",
    )

    _NETWORKING_SCOPES = (
        LOCAL, GLOBAL,
    ) = (
        "local", "global",
    )

    _VM_TYPES = (
        ASSURED, BEST_EFFORT,
    ) = (
        "assured", "best_effort",
    )

    PROPERTIES = (
        ACCESS_TYPE, BANDWIDTH, LATENCY, IOPS, 
        NETWORKING_PRIORITY, NETWORKING_SCOPE, VM_TYPE,
    ) = (
        'access_type', 'bandwidth', 'latency', 'iops',
        'networking_priority', 'networking_scope', 'vm_type',
    )

    properties_schema = {
        ACCESS_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('Access type.'),
            constraints=[constraints.AllowedValues([SEQUENTIAL, MIXED])],
            required=True,
            update_allowed=True
        ),
        BANDWIDTH: properties.Schema(
            properties.Schema.STRING,
            _('Bandwidth. Format: (min#-max#)|# kbps|Mbps|Gbps (#% tolerance).'),
            required=True,
            update_allowed=True
        ),
        LATENCY: properties.Schema(
            properties.Schema.STRING,
            _('Latency. Format: (min#-max#)|# msec|sec|min (#% tolerance).'),
            required=True,
            update_allowed=True
        ),
        IOPS: properties.Schema(
            properties.Schema.STRING,
            _('IOPS. Format: (min#-max#)|# (#% tolerance).'),
            required=True,
            update_allowed=True
        ),
        NETWORKING_PRIORITY: properties.Schema(
            properties.Schema.STRING,
            _('Networking Priority.'),
            constraints=[constraints.AllowedValues([VOICE, CONTROL, DATA])],
            required=True,
            update_allowed=True
        ),
        NETWORKING_SCOPE: properties.Schema(
            properties.Schema.STRING,
            _('Networking Scope.'),
            constraints=[constraints.AllowedValues([LOCAL, GLOBAL])],
            required=True,
            update_allowed=True
        ),
        VM_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('VM type.'),
            constraints=[constraints.AllowedValues([ASSURED, BEST_EFFORT])],
            required=True,
            update_allowed=True
        ),
    }
    
    def handle_create(self):
        self.resource_id_set(self.physical_resource_name())

    def handle_update(self, json_snippet, templ_diff, prop_diff):
        self.resource_id_set(self.physical_resource_name())

    def handle_delete(self):
        self.resource_id_set(None)

class AttributesDeprecated(Attributes):
    """
    DEPRECATED: Use ATT::CloudQoS::Attributes instead.
    """ 
    
    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS is now ATT::CloudQoS.')
    ) 
        
def resource_mapping():
    """Map names to resources."""
    return {
       'ATT::QoS::Attributes': AttributesDeprecated,
       'ATT::CloudQoS::Attributes': Attributes
    }
