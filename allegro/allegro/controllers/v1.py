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

from allegro.controllers import error, errors, project
    
import logging
from pecan import conf, expose, redirect, request, response

logger = logging.getLogger(__name__)
    
        
class V1Controller(object):
    # /v1

    errors = errors.ErrorsController()

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    @expose()
    def _lookup(self, project_id, *remainder):
        return project.ProjectController(project_id), remainder
