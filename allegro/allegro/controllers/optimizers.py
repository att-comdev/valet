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

from allegro.controllers import error
from allegro.ostro_helper import Ostro
from pecan import expose, redirect, request, response
from pecan_notario import validate

import logging
from notario import decorators
from notario.validators import types
from webob.exc import status_map

logger = logging.getLogger(__name__)


class OptimizersController(object):

    def _ping(self):
        '''Ping the optimizer.'''
        ostro = Ostro()
        ostro.ping()
        ostro.send()

        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error('/v1/errors/invalid',
                  'Ostro error: %s' % message)
        return ostro.response

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    @index.when(method='HEAD', template='json')
    def index_head(self):
        ostro_response = self._ping()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        ostro_response = self._ping()
        response.status = 200
        return ostro_response
