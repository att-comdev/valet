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

import json
import requests
import sys

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class ValetAPIError(Exception): pass

class ValetAPIWrapper(object):
    def __init__(self):
        self.headers = {'Content-Type': 'application/json'}
        self.opt_group_str = 'valet'
        self.opt_name_str = 'url'
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
            raise # exception.Error(_('API Endpoint not defined.'))

    # Register options
    def _register_opts(self):
        opts = []
        option = cfg.StrOpt(self.opt_name_str, default=None,
                            help='Valet API endpoint')
        opts.append(option)

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    def _exception(self, e, exc_info, req):
        response = json.loads(req.text)
        if 'error' in response:
            error = response.get('error')
            msg = "%(explanation)s (valet-api: %(message)s)" % {
                  'explanation': response.get('explanation',
                      'No remediation available'),
                  'message': error.get('message', 'Unknown error')
            }
            raise ValetAPIError(msg)
        else:
            # TODO: Re-evaluate if this clause is necessary.
            exc_class, exc, traceback = exc_info
            msg = "%s for %s %s with body %s" % \
                  (exc, e.request.method, e.request.url, e.request.body)
            my_exc = ValetAPIError(msg)
            # traceback can be added to the end of the raise
            raise my_exc.__class__, my_exc

    def plans_create(self, stack, plan, auth_token=None):
        try:
            url = self._api_endpoint() + '/plans/'
            payload = json.dumps(plan)
            self.headers['X-Auth-Token'] = auth_token
            req = requests.post(url, data=payload, headers=self.headers)
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._exception(e, sys.exc_info(), req)

    def plans_delete(self, stack, auth_token=None):
        try:
            url = self._api_endpoint() + '/plans/' + stack.id
            self.headers['X-Auth-Token'] = auth_token
            req = requests.delete(url, headers=self.headers)
        except requests.exceptions.HTTPError as e:
            self._exception(e, sys.exc_info(), req)

    def placement(self, uuid, hosts=None, auth_token=None):
        '''
        Reserve placement previously made for an Orchestration ID.
        '''
        try:
            url = self._api_endpoint() + '/placements/' + uuid
            self.headers['X-Auth-Token'] = auth_token
            if hosts:
                kwargs = {
                    "locations": hosts
                }
                payload = json.dumps(kwargs)
                req = requests.post(url, data=payload, headers=self.headers)
            else:
                req = requests.get(url, headers=self.headers)

            # TODO: Raise an exception if the scheduler can handle it
            #req.raise_for_status()

            placement = json.loads(req.text)
        except:
            placement = None

        return placement