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
DiversityZone.py

Author: Joe D'Andrea
Created: 18 July 2014
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


class DiversityZone(resource.Resource):
    """
    DEPRECATED: Use ATT::QoS::ResourceGroup instead.

    A diversity zone describes the deployment level and minimum spacing
    of a set of deployable resources (e.g., VMs, Volumes, Databases).
    
    Resources are deployed at one of the following levels, if appropriate.

    cloud: Across clouds, one resource per availability_zone.
    availability_zone: Across availability_zones, one resource per rack.
    rack: Across racks, one resource per host.
    host: All resources on a single host.
    any: I just want to deploy my resources. Surprise me. :)

    Use "spacing" to describe the minimum number of clouds,
    availability zones, racks, or hosts within which to deploy resources.
    """

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS::DiversityZone is unsupported and will be removed in a '
          'future release of CloudQoS. Use ATT::QoS::ResourceGroup to '
          'specify a diversity relationship.')
    )

    _LEVEL_TYPES = (
        CLOUD, AVAILABILITY_ZONE, RACK, HOST, ANY,
    ) = (
        "cloud", "availability_zone", "rack", "host", "any",
    )

    PROPERTIES = (
        NAME, LEVEL, RESOURCES, SPACING,
    ) = (
        'name', 'level', 'resources', 'spacing',
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the diversity zone.'),
            required=True,
            update_allowed=True
        ),
        LEVEL: properties.Schema(
            properties.Schema.STRING,
            _('Level across which resources should be distributed.'),
            constraints=[constraints.AllowedValues([CLOUD,
                         AVAILABILITY_ZONE, RACK, HOST, ANY])],
            default=ANY,
            required=False,
            update_allowed=True
            ),
        RESOURCES: properties.Schema(
            properties.Schema.LIST,
            _('List of resource IDs associated with the zone.'),
            required=True,
            update_allowed=True
        ),
        SPACING: properties.Schema(
            properties.Schema.NUMBER,
            _('Minimum number of zone level instances '+
              'in which to place resources.'),
            constraints=[constraints.Range(min=1)],
            default=1,
            required=False
        ),
    }
    
    def handle_create(self):
        self.resource_id_set(self.properties[self.NAME])

    def handle_update(self, json_snippet, templ_diff, prop_diff):
        self.resource_id_set(self.properties[self.NAME])

    def handle_delete(self):
        self.resource_id_set(None)

class DiversityZoneDeprecated(DiversityZone):
    """
    DEPRECATED: Use ATT::CloudQoS::DiversityZone instead.
    """

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS is now ATT::CloudQoS.')
    )

def resource_mapping():
    """Map names to resources."""
    return {
       'ATT::QoS::DiversityZone': DiversityZoneDeprecated,
       'ATT::CloudQoS::DiversityZone': DiversityZone
    }
