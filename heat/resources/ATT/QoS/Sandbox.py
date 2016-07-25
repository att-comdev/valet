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
Sandbox.py

Used to try out plugin ideas

Author: Joe D'Andrea
Contact: jdandrea@research.att.com
'''

import sys
import traceback

from oslo_log import log as logging
from requests import exceptions
import simplejson

from heat.common.i18n import _
from heat.common import exception
from heat.common import template_format
from heat.common import urlfetch
from heat.engine import attributes
from heat.engine import properties
from heat.engine.resources import stack_resource
from heat.engine import support

LOG = logging.getLogger(__name__)


class Sandbox(stack_resource.StackResource):
    '''
    Sandbox - used to try out plugin ideas.
    '''

    PROPERTIES = (
        TEMPLATE_URL, TIMEOUT_IN_MINS, PARAMETERS,
    ) = (
        'template_url', 'timeout_in_minutes', 'parameters',
    )

    properties_schema = {
        TEMPLATE_URL: properties.Schema(
            properties.Schema.STRING,
            _('The URL of a template that specifies the stack to be created '
              'as a resource.'),
            required=True,
            update_allowed=True
        ),
        TIMEOUT_IN_MINS: properties.Schema(
            properties.Schema.NUMBER,
            _('The length of time, in minutes, to wait for the nested stack '
              'creation.'),
            update_allowed=True
        ),
        PARAMETERS: properties.Schema(
            properties.Schema.MAP,
            _('The set of parameters passed to this nested stack.'),
            update_allowed=True
        ),
    }

    SCHEMES = ('http', 'https', 'file',)

    #update_allowed_keys = ('properties',)

    def child_template(self):
        try:
            template_data = urlfetch.get(self.properties[self.TEMPLATE_URL],
                                         allowed_schemes=self.SCHEMES)
        except (exceptions.RequestException, IOError) as r_exc:
            raise ValueError(_("Could not fetch remote template '%(url)s': "
                             "%(exc)s") %
                             {'url': self.properties[self.TEMPLATE_URL],
                              'exc': str(r_exc)})
        return template_format.parse(template_data)

    def child_params(self):
        return self.properties[self.PARAMETERS]

    def handle_adopt(self, resource_data=None):
        LOG.info(_('======== Landed in handle_adopt() ========'))
        return self._create_with_template(resource_adopt_data=resource_data)

    def handle_create(self):
        LOG.info(_('======== Landed in handle_create() ========'))
        return self._create_with_template()

    def _create_with_template(self, resource_adopt_data=None):
        template = self.child_template()
        return self.create_with_template(template,
                                         self.child_params(),
                                         self.properties[self.TIMEOUT_IN_MINS],
                                         adopt_data=resource_adopt_data)

    def handle_delete(self):
        LOG.info(_('======== Landed in handle_delete() ========'))
        return self.delete_nested()

    def FnGetAtt(self, key):
        if key and not key.startswith('Outputs.'):
            raise exception.InvalidTemplateAttribute(resource=self.name,
                                                     key=key)
        return self.get_output(key.partition('.')[-1])

    def FnGetRefId(self):
        return self.nested().identifier().arn()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        # Nested stack template may be changed even if the prop_diff is empty.
        LOG.info(_('======== Landed in handle_update() ========'))
        self.properties = properties.Properties(self.properties_schema,
                                     json_snippet.get('properties', {}),
                                     self.stack.resolve_runtime_data,
                                     self.name,
                                     self.context)

        template = self.child_template()

        return self.update_with_template(template,
                                         self.properties[self.PARAMETERS],
                                         self.properties[self.TIMEOUT_IN_MINS])

def resource_mapping():
    """Map names to resources."""
    #return {'ATT::QoS::Sandbox': Sandbox}
    return
