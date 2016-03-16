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
ResourceGroup.py

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


class ResourceGroup(resource.Resource):
    """
    A QoS Resource Group describes one or more resources classified
    as a particular type of group. Resource Groups can include other
    groups, so long as there are no circular references.

    This resource has no nutritional value to Heat. It is intended
    for use by holistic placement tools when scheduling an entire
    stack of related resources well in advance of instantiation vs.
    one at a time, each independent of the other.

    Note that the name of this resource is similar to that of
    OS::Heat::ResourceGroup but they do not describe the same thing.
    A more distinct name may be more desirable in a future revision.
    """

    _RELATIONSHIP_TYPES = (
        AFFINITY, DIVERSITY, EXCLUSIVITY,
    ) = (
        "affinity", "diversity", "exclusivity",
    )

    PROPERTIES = (
        NAME, RELATIONSHIP, LEVEL, RESOURCES,
    ) = (
        'name', 'relationship', 'level', 'resources',
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of relationship. Required for exclusivity groups.'),
            # TODO: Add a custom constraint that ensures a valid
            # and allowed name when an exclusivity group is in use.
            update_allowed=True
        ),
        RELATIONSHIP: properties.Schema(
            properties.Schema.STRING,
            _('Grouping relationship.'),
            constraints=[
                constraints.AllowedValues([AFFINITY, DIVERSITY, EXCLUSIVITY])
            ],
            required=True,
            update_allowed=True
            ),
        LEVEL: properties.Schema(
            properties.Schema.STRING,
            _('Level of relationship between resources.'),
            constraints=[
                constraints.AllowedValues(['host', 'rack', 'cluster', 'any']),
            ],
            update_allowed=True
        ),
        RESOURCES: properties.Schema(
            properties.Schema.LIST,
            _('List of one or more resource IDs.'),
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

class ResourceGroupDeprecated(ResourceGroup):
    """
    DEPRECATED: Use ATT::CloudQoS::ResourceGroup instead.
    """

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS is now ATT::CloudQoS.')
    )

def resource_mapping():
    """Map names to resources."""
    return {
       'ATT::QoS::ResourceGroup': ResourceGroupDeprecated,
       'ATT::CloudQoS::ResourceGroup': ResourceGroup
    }
