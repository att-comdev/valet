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
Pipe.py

Author: Joe D'Andrea
Created: 26 June 2014
Contact: jdandrea@research.att.com
'''

import re

from oslo_config import cfg
from oslo_log import log as logging
from qosorch import plugins

from heat.common import exception
from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.engine import support

LOG = logging.getLogger(__name__)


class Pipe(resource.Resource):
    '''
    A pipe enforces QoS requirements across one or more resources.
    QoS across specific resource types are supported by Pipe Plugins.
    '''

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('Deprecated. Use ATT::QoS::Reservation and ATT::QoS::Attributes.')
    )

    _RANGE_KEYS = (
        MIN, MAX, TOLERANCE, UNITS,
    ) = (
        "min", "max", "tolerance", "units",
    )

    _BANDWIDTH_UNITS = (
        KBPS, MBPS, GBPS, TBPS,
    ) = (
        "kbps", "Mbps", "Gbps", "Tbps",
    )

    _VOLUME_ACCESS_TYPES = (
        SEQUENTIAL, MIXED, ANY,
    ) = (
        "sequential", "mixed", "any",
    )

    PROPERTIES = (
        RESOURCES, IOPS, BANDWIDTH, LATENCY, ACCESS_TYPE,
    ) = (
        'resources', 'iops', 'bandwidth', 'latency', 'access_type'
    )

    properties_schema = {
        RESOURCES: properties.Schema(
            properties.Schema.LIST,
            _('List of associated resource IDs.'),
            required=True,
            update_allowed=True
        ),
        IOPS: properties.Schema(
            properties.Schema.MAP,
            _('If a Volume resource is provided, the desired input/output '
              'operations per second. The bandwidth property takes '
              'precedence if it is provided.'),
            schema={
                MIN: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                MAX: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                TOLERANCE: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=1,
                    required=False
                ),
            },
            required=False,
            update_allowed=True
        ),
        BANDWIDTH: properties.Schema(
            properties.Schema.MAP,
            _('Desired bandwidth in HOT format.'),
            schema={
                MIN: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                MAX: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                TOLERANCE: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=1,
                    required=False
                ),
                UNITS: properties.Schema(
                    properties.Schema.STRING,
                    constraints=[constraints.AllowedValues([KBPS, MBPS,
                                                            GBPS, TBPS])],
                    default=MBPS,
                    required=False
                ),
            },
            required=False,
            update_allowed=True
        ),
        LATENCY: properties.Schema(
            properties.Schema.MAP,
            _('Desired latency in HOT format.'),
            schema={
                MIN: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                MAX: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=0,
                    required=False
                ),
                TOLERANCE: properties.Schema(
                    properties.Schema.NUMBER,
                    constraints=[constraints.Range(min=0)],
                    default=1,
                    required=False
                ),
            },
            required=False,
            update_allowed=True
            ),
        ACCESS_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('If a Volume resource is provided, the desired access type.'),
            constraints=[constraints.AllowedValues([SEQUENTIAL, MIXED, ANY])],
            default=MIXED,
            required=False,
            update_allowed=True
            ),
    }

    ATTRIBUTES = (
        ATTRIBUTE_SHOW,
    ) = (
        'show',
    )

    attributes_schema = {
        ATTRIBUTE_SHOW: attributes.Schema(
            _('A dict of all QoS request/response details '
              'as returned by the responding plugin(s).'),
        ),
    }

    def __init__(self, name, json_snippet, stack):
        super(Pipe, self).__init__(name, json_snippet, stack)

        self._opt_group_str = None
        self._plugins = {}
        self._register_plugins()

    def handle_create(self):
        """Create Resource"""

        resource_ids = self.properties.get(self.RESOURCES)
        if len(resource_ids) < 1:
            raise exception.Error(_('Must provide at least one resource UUID.'))

        # TODO: Ask each plugin if it supports the resources. If none do, honk!
        # TODO: id or resource_id? also check name and type() and identifier.
        # TODO: res.has_interface('OS::Nova::Server') may make more sense here.
        #for res_id in resource_ids:
        #    res = self._find_resource(res_id)
        #    res_type = res.type()
        #    if res_type not in self.SUPPORTED_RESOURCE_TYPES:
        #        exc = exception.Error(_('%s unsupported. Must be one of: %s.'
        #            % res_type, ",".join(self.SUPPORTED_RESOURCE_TYPES)))
        #        raise exc

        # TODO: Combine all handler calls into a common method.
        for dummy_name, the_plugin in self._plugins.iteritems():
            try:
                handle_create = the_plugin.handle_create
            except AttributeError:
                pass
            else:
                handle_create(resource_ids)

        self.resource_id_set(self.physical_resource_name())

    def handle_delete(self):
        """Delete Resource"""

        # Let each plugin choose to handle the delete.
        # TODO: Combine all handler calls into a common method.
        for dummy_name, the_plugin in self._plugins.iteritems():
            try:
                handle_delete = the_plugin.handle_delete
            except AttributeError:
                pass
            else:
                handle_delete()
        return

    def _resolve_attribute(self, name):
        """Resolve Attribute"""
            
        # TODO: Should pipes bubble up outputs into common attributes?

        # Offer access to all raw data.
        if name == self.ATTRIBUTE_SHOW:            
            # Let each plugin choose to handle the attribute resolution.        
            outputs = {}
            for dummy_name, the_plugin in self._plugins.iteritems():
                try:
                    handle_resolve_attribute = the_plugin._resolve_attribute
                except AttributeError:
                    pass
                else:
                    output = handle_resolve_attribute(name)
                    if output:
                        outputs[dummy_name] = output
            return outputs

    @property
    def opt_group_str(self):
        """
        Heat Config Option group name for pipe service endpoints.
        This is the Pipe resource plugin name, lower-cased,
        with underscore separators.
        """
        if self._opt_group_str:
            return self._opt_group_str

        pattern = re.compile('::')
        plugin_type = self.type()
        self._opt_group_str = pattern.sub('_', plugin_type.lower())
        return self._opt_group_str

    def _register_plugins(self):
        """ Register Plugins """

        # TODO: Combine all handler calls into a common method.
        self._plugins = {}
        opts = []
        for name in plugins.__all__:
            the_plugin = getattr(plugins, name)
            try:
                # see if the plugin has a 'register' attribute
                register_plugin = the_plugin.register
            except AttributeError:
                # raise an exception, log a message,
                # or just ignore the problem
                pass
            else:
                # try to call it, without catching any errors
                registration = register_plugin()
                for the_name, the_plugin in registration.iteritems():
                    # Instantiate each plugin's entry point with a Reservation.
                    instance = the_plugin(self)
                    service_name = instance.service_name
                    opt_name_str = instance.opt_name_str

                    # Yes, technically it has already been registered.
                    LOG.info(_('Registering Reservation Plugin: %(name)s' % {
                        'name': service_name,
                    }))

                    # Set up a config option for the pipe's service.
                    option = cfg.StrOpt(opt_name_str, default=None,
                             help='API endpoint for %s' % service_name)
                    opts.append(option)

                    self._plugins[the_name] = instance

        # Register all the options so they are available via heat.conf
        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

class PipeDeprecated(Pipe):
    """
    DEPRECATED: Use ATT::CloudQoS::Pipe instead.
    """

    support_status = support.SupportStatus(
        support.DEPRECATED,
        _('ATT::QoS is now ATT::CloudQoS.')
    )

def resource_mapping():
    """Map names to resources."""
    return {
       'ATT::QoS::Pipe': PipeDeprecated,
       'ATT::CloudQoS::Pipe': Pipe
    }
