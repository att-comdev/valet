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

'''v1'''

import logging

from allegro.controllers import error
#from allegro.controllers import project
from allegro.controllers.groups import GroupsController
from allegro.controllers.placements import PlacementsController
from allegro.controllers.plans import PlansController
from allegro.controllers.optimizers import OptimizersController
from allegro.i18n import _

from pecan import conf, expose, request
from pecan.secure import SecureController

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class V1Controller(SecureController):
    '''
    v1 Controller
    /v1
    '''

    plans = PlansController()
    placements = PlacementsController()
    groups = GroupsController()
    optimizers = OptimizersController()

    @classmethod
    def check_permissions(cls):
        '''SecureController permission check callback'''
        auth_token = request.headers.get('X-Auth-Token')
        if auth_token and conf.identity.engine.is_admin(auth_token):
            return True
        error('/errors/unauthorized')

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET'

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

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Get canonical URL for each endpoint'''
        endpoints = ["groups", "optimizers", "plans", "placements"]
        links = []
        for endpoint in endpoints:
            links.append({
                "href": "%(url)s/v1/%(endpoint)s/" % {
                    'url': request.application_url,
                    'endpoint': endpoint
                },
                "rel": "self"
            })
        ver = {
            "versions": [
                {
                    "status": "CURRENT",
                    "id": "v1.0",
                    "links": links
                }
            ]
        }

        return ver
