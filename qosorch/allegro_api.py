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
allegro.py

Author: Joe D'Andrea
Created: 1 June 2015
Contact: jdandrea@research.att.com
'''

import json
import requests
import sys

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class AllegroAPIWrapperError(Exception): pass

class AllegroAPIWrapper(object):
    def __init__(self):
        self.headers = {'Content-Type': 'application/json'}
        self.opt_group_str = 'allegro'
        self.opt_name_str = 'allegro_api_server_url'
        self._register_opts()

    def _api_endpoint(self):
        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            endpoint = opt[self.opt_name_str]
            if endpoint:
                return endpoint
            else:
                raise
        except:
            raise # exception.Error(_('Allegro API Endpoint not defined.'))

    # Register options
    def _register_opts(self):
        opts = []
        option = cfg.StrOpt(self.opt_name_str, default=None,
                            help='API endpoint for Allegro')
        opts.append(option)

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    def plans_create(self, stack, plan):
        payload = json.dumps(plan)
        url = self._api_endpoint() + '/' + stack.tenant_id + '/plans/'
        try:
            req = requests.post(url, data=payload, headers=self.headers)
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # TODO: Move this into allegro proper and don't raise for status?
            exc_class, exc, traceback = sys.exc_info()
            msg = "%s for %s %s with body %s" % \
                  (exc, e.request.method, e.request.url, e.request.body)
            my_exc = AllegroAPIWrapperError(msg)
            # traceback can be added to the end of the raise
            raise my_exc.__class__, my_exc

    def plans_delete(self, stack):
        # FIXME: Must put trailing slash on end or else
        # Allegro does a 302 redirect and then a _GET_ vs a DELETE.
        # When we try this with Postman the redirect remains a DELETE.
        url = self._api_endpoint() + '/' + stack.tenant_id + \
              '/plans/' + stack.id + '/'
        req = requests.delete(url)

    def placement(self, uuid):
        """Call Allegro API to get placement for an Orchestration ID."""

        # TODO: Get tenant_id from the heat stack?
        tenant_id = 'e833dea42c7c47d6be25150693fe0f40'
        url = self._api_endpoint() + '/' + tenant_id + '/placements/' + uuid
        req = requests.get(url, headers=self.headers)

        # TODO: If not 200 or timeout, do alternate scheduling
        #req.raise_for_status()

        # TODO: Test key.
        placement = json.loads(req.text)
        return placement
