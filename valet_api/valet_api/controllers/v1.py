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

from valet_api.controllers import error
from valet_api.controllers.groups import GroupsController
from valet_api.controllers.placements import PlacementsController
from valet_api.controllers.plans import PlansController
from valet_api.controllers.status import StatusController
from valet_api.i18n import _

from pecan import conf, expose, request
from pecan.secure import SecureController

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class V1Controller(SecureController):
    '''
    v1 Controller
    /v1
    '''

    groups = GroupsController()
    placements = PlacementsController()
    plans = PlansController()
    status = StatusController()

    endpoints = ["groups", "placements", "plans", "status"]

    @classmethod
    def check_permissions(cls):
        '''SecureController permission check callback'''
        auth_token = request.headers.get('X-Auth-Token')
        if auth_token:
            # The token must have an admin role
            # and be associated with a tenant.
            token = conf.identity.engine.validate_token(auth_token)
            if token and conf.identity.engine.is_token_admin(token):
                tenant_id = \
                    conf.identity.engine.tenant_from_token(token)
                if tenant_id:
                    request.context['tenant_id'] = tenant_id
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
        links = []
        for endpoint in V1Controller.endpoints:
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
