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
# See the License for the specific language governing permissions and
# limitations under the License.
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

    def _api_endpoint(self, tenant_id='e833dea42c7c47d6be25150693fe0f40'):
        # TODO: Require tenant id, else honk
        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            endpoint = opt[self.opt_name_str] + '/' + tenant_id
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

    def _exception(self, e, exc_info, req):
        # TODO: Move into allegro proper and don't raise for status?
        exc_class, exc, traceback = exc_info
        response = json.loads(req.text)
        errors = response.get('errors')
        if errors and len(errors) > 0:
            error = errors[0]
            msg = "%(userMessage)s (allegro-api: %(internalMessage)s)" % {
                  'userMessage': error.get('userMessage'),
                  'internalMessage': error.get('internalMessage')
            }
            my_exc = AllegroAPIWrapperError(msg)
        else:
            msg = "%s for %s %s with body %s" % \
                  (exc, e.request.method, e.request.url, e.request.body)
            my_exc = AllegroAPIWrapperError(msg)
            # traceback can be added to the end of the raise
        raise my_exc.__class__, my_exc

    def plans_create(self, stack, plan, tenant_id=None, auth_token=None):
        try:
            url = self._api_endpoint(tenant_id) + '/plans/'
            payload = json.dumps(plan)
            self.headers['X-Auth-Token'] = auth_token
            req = requests.post(url, data=payload, headers=self.headers)
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._exception(e, sys.exc_info(), req)

    def plans_delete(self, stack, tenant_id=None, auth_token=None):
        try:
            url = self._api_endpoint(tenant_id) + '/plans/' + \
                  stack.id
            self.headers['X-Auth-Token'] = auth_token
            req = requests.delete(url, headers=self.headers)
        except requests.exceptions.HTTPError as e:
            self._exception(e, sys.exc_info(), req)

    def placement(self, uuid, hosts=None, tenant_id=None, auth_token=None):
        """Call Allegro API to get placement for an Orchestration ID."""
        try:
            url = self._api_endpoint(tenant_id) + '/placements/' + uuid
            self.headers['X-Auth-Token'] = auth_token
            if hosts:
                kwargs = {
                    "locations": hosts
                }
                payload = json.dumps(kwargs)
                req = requests.post(url, data=payload, headers=self.headers)
            else:
                req = requests.get(url, headers=self.headers)

            # TODO: If not 200 or timeout, honk
            #req.raise_for_status()

            # TODO: Test key.
            placement = json.loads(req.text)
        except:
            placement = None

        return placement
