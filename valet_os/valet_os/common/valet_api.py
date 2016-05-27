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

'''Valet API Wrapper'''

import json
import sys

from heat.common.i18n import _

from oslo_config import cfg
from oslo_log import log as logging
import requests

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


def _exception(exc, exc_info, req):
    '''Handle an exception'''
    response = json.loads(req.text)
    if 'error' in response:
        error = response.get('error')
        msg = "%(explanation)s (valet-api: %(message)s)" % {
            'explanation': response.get('explanation',
                                        _('No remediation available')),
            'message': error.get('message', _('Unknown error'))
        }
        raise ValetAPIError(msg)
    else:
        # TODO: Re-evaluate if this clause is necessary.
        exc_class, exc, traceback = exc_info  # pylint: disable=W0612
        msg = _("%s for %s %s with body %s") % \
              (exc, exc.request.method,
               exc.request.url, exc.request.body)
        my_exc = ValetAPIError(msg)
        # traceback can be added to the end of the raise
        raise my_exc.__class__, my_exc


# TODO: Improve exception reporting back up to heat
class ValetAPIError(Exception):
    '''Valet API Error'''
    pass

class ValetAPIWrapper(object):
    '''Valet API Wrapper'''

    def __init__(self):
        '''Initializer'''
        self.headers = {'Content-Type': 'application/json'}
        self.opt_group_str = 'valet'
        self.opt_name_str = 'url'
        self._register_opts()

    def _api_endpoint(self):
        '''Returns API endpoint'''
        try:
            opt = getattr(cfg.CONF, self.opt_group_str)
            endpoint = opt[self.opt_name_str]
            if endpoint:
                return endpoint
            else:
                # FIXME: Possibly not wanted (misplaced-bare-raise)
                raise  # pylint: disable=E0704
        except:
            raise # exception.Error(_('API Endpoint not defined.'))

    def _register_opts(self):
        '''Register options'''
        opts = []
        option = cfg.StrOpt(self.opt_name_str, default=None,
                            help=_('Valet API endpoint'))
        opts.append(option)

        opt_group = cfg.OptGroup(self.opt_group_str)
        cfg.CONF.register_group(opt_group)
        cfg.CONF.register_opts(opts, group=opt_group)

    # TODO: Keep stack param for now. We may need it again.
    def plans_create(self, stack, plan, auth_token=None):  # pylint: disable=W0613
        '''Create a plan'''
        try:
            url = self._api_endpoint() + '/plans/'
            payload = json.dumps(plan)
            self.headers['X-Auth-Token'] = auth_token
            req = requests.post(url, data=payload, headers=self.headers)
            req.raise_for_status()
            response = json.loads(req.text)
        except requests.exceptions.HTTPError as exc:
            _exception(exc, sys.exc_info(), req)
        return response

    # TODO: Keep stack param for now. We may need it again.
    def plans_delete(self, stack, auth_token=None):  # pylint: disable=W0613
        '''Delete a plan'''
        try:
            url = self._api_endpoint() + '/plans/' + stack.id
            self.headers['X-Auth-Token'] = auth_token
            req = requests.delete(url, headers=self.headers)
        except requests.exceptions.HTTPError as exc:
            _exception(exc, sys.exc_info(), req)
        # Delete does not return a response body.

    def placement(self, orch_id, res_id, hosts=None, auth_token=None):
        '''
        Reserve previously made placement.
        '''
        try:
            url = self._api_endpoint() + '/placements/' + orch_id
            self.headers['X-Auth-Token'] = auth_token
            if hosts:
                kwargs = {
                    "locations": hosts,
                    "resource_id": res_id
                }
                payload = json.dumps(kwargs)
                req = requests.post(url, data=payload, headers=self.headers)
            else:
                req = requests.get(url, headers=self.headers)

            # TODO: Raise an exception IFF the scheduler can handle it
            #req.raise_for_status()

            response = json.loads(req.text)
        except:  # pylint: disable=W0702
            # FIXME: Find which exceptions we should really handle here.
            response = None

        return response
