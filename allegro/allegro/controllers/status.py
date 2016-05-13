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

'''Status'''

import logging

from allegro.controllers import error
from allegro.i18n import _
from allegro.ostro_helper import Ostro

from pecan import expose, request, response

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class StatusController(object):
    '''
    Status Controller
    /v1/{tenant_id}/status
    '''

    def _ping(self):
        '''Ping the optimizer.'''
        ostro = Ostro()
        ostro.ping()
        ostro.send()

        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error(ostro.error_uri, _('Ostro error: %s') % message)
        return ostro.response

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'HEAD,GET'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='HEAD', template='json')
    def index_head(self):
        '''Ping Ostro'''
        _unused = self._ping()  # pylint: disable=W0612
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Ping Ostro and return the response'''
        ostro_response = self._ping()
        response.status = 200
        return ostro_response
