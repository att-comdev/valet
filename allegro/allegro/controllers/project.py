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

from pecan import expose
from pecan import request

from allegro.controllers import plans, placements, groups, optimizers
    
import logging

logger = logging.getLogger(__name__)
    
        
class ProjectController(object):
    plans = plans.PlansController()
    placements = placements.PlacementsController()
    groups = groups.GroupsController()
    optimizers = optimizers.OptimizersController()

    def __init__(self, project_id):
        assert project_id
        request.context['project_id'] = project_id

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    @index.when(method='GET', template='json')
    def index_get(self):
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
