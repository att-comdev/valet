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

'''Project'''

import logging

from allegro.controllers import error
from allegro.controllers.groups import GroupsController
from allegro.controllers.placements import PlacementsController
from allegro.controllers.plans import PlansController
from allegro.controllers.optimizers import OptimizersController
from allegro.i18n import _

from pecan import expose, request, response

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class ProjectController(object):
    '''
    Project Controller
    /v1/{tenant_id}

    NOTE: The term "tenant" has been superceded by "project"
    yet the OpenStack community still uses the term "tenant"
    in popular usage. "Vive la résistance!"
    '''

    plans = PlansController()
    placements = PlacementsController()
    groups = GroupsController()
    optimizers = OptimizersController()

    def __init__(self, project_id):
        '''Initializer'''
        assert project_id
        request.context['project_id'] = project_id

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
                "href": "%(url)s/v1/%(project_id)s/%(endpoint)s/" % {
                    'url': request.application_url,
                    'project_id': request.context['project_id'],
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
