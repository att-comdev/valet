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
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Valet Nova Scheduler Filter'''

from oslo_config import cfg
from oslo_log import log as logging

from keystoneclient.v2_0 import client
from nova.i18n import _LI, _LW
from nova.scheduler import filters

from valet_os.common import valet_api

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class ValetFilter(filters.BaseHostFilter):
    '''Filter on Valet assignment.'''

    # Host state does not change within a request
    run_filter_once_per_request = True

    # Used to authenticate request. Update via _authorize()
    _auth_token = None

    def __init__(self):
        '''Initializer'''
        self.api = valet_api.ValetAPIWrapper()
        self.opt_group_str = 'valet'
        self.opt_project_name_str = 'admin_tenant_name'
        self.opt_username_str = 'admin_username'
        self.opt_password_str = 'admin_password'
        self.opt_auth_uri_str = 'admin_auth_url'
        self._register_opts()

    def _authorize(self):
        '''Keystone AuthN'''
        opt = getattr(cfg.CONF, self.opt_group_str)
        project_name = opt[self.opt_project_name_str]
        username = opt[self.opt_username_str]
        password = opt[self.opt_password_str]
        auth_uri = opt[self.opt_auth_uri_str]

        kwargs = {
            'username': username,
            'password': password,
            'tenant_name': project_name,
            'auth_url': auth_uri
        }
        keystone_client = client.Client(**kwargs)
        self._auth_token = keystone_client.auth_token

    def _is_same_host(self, host, location):  # pylint: disable=R0201
        '''Returns true if host matches location'''
        return host == location

    def _register_opts(self):
        '''Register Options'''
        opts = []
        option = cfg.StrOpt(self.opt_project_name_str, default=None,
                            help='Valet Project Name')
        opts.append(option)
        option = cfg.StrOpt(self.opt_username_str, default=None,
                            help='Valet Username')
        opts.append(option)
        option = cfg.StrOpt(self.opt_password_str, default=None,
                            help='Valet Password')
        opts.append(option)
        option = cfg.StrOpt(self.opt_auth_uri_str, default=None,
                            help='Keystone Authorization API Endpoint')
        opts.append(option)

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    # TODO: Factor out common code to a qosorch library
    def filter_all(self, filter_obj_list, filter_properties):
        '''Filter all hosts in one swell foop'''
        hints_key = 'scheduler_hints'
        uuid_key = 'heat_resource_uuid'

        yield_all = False
        location = None
        uuid = None

        # If we don't have hints to process, yield (pass) all hosts
        # so other plugins have a fair shot. TODO: This will go away
        # once ostro can handle on-the-fly scheduling, except for cases
        # where we can't reach Valet at all, then we may opt to fail
        # all hosts depending on a TBD config flag.
        if not filter_properties.get(hints_key, {}).has_key(uuid_key):
            LOG.warn(_LW("Valet: Heat Stack Lifecycle Scheduler Hints " \
                     "not found. Abstaining from placement."))
            yield_all = True
        else:
            uuid = filter_properties[hints_key][uuid_key]
            self._authorize()
            hosts = [obj.host for obj in filter_obj_list]
            placement = self.api.placement(uuid, hosts=hosts,
                                           auth_token=self._auth_token)

            # Ostro will give a matching format
            if placement and placement.get('location'):
                location = placement['location']

            if not location:
                LOG.warn(_LW("Valet placement unknown " \
                         "for resource: %s.") % uuid)
                yield_all = True

        # Yield the hosts that pass.
        # Like the Highlander, there can (should) be only one.
        # TODO: If no hosts pass, do alternate scheduling.
        # If we can't be sure of a placement, yield all hosts for now.
        for obj in filter_obj_list:
            if location:
                match = self._is_same_host(obj.host, location)
                if match:
                    LOG.info(_LI("Valet placement for resource %s: %s." % \
                              (uuid, obj.host)))
            if yield_all or match:
                yield obj

    def host_passes(self, host_state, filter_properties):  # pylint: disable=W0613,R0201
        '''Individual host pass check'''
        # Intentionally let filter_all() handle in one swell foop.
        return False
