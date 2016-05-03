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

from allegro.controllers import error, v1
from allegro.controllers.errors import error_wrapper

import logging
from pecan import conf, expose, redirect, request, response
from pecan.secure import SecureController
from webob.exc import status_map

logger = logging.getLogger(__name__)


class RootController(SecureController):
    v1 = v1.V1Controller()

    @classmethod
    def check_permissions(cls):
        auth_token = request.headers.get('X-Auth-Token')
        if auth_token:
            return conf.identity.engine.is_admin(auth_token)
        return False

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Supported methods'''
        response.headers['Allow'] = 'GET'
        response.status = 204

    # TODO: No need to respond to this endpont?
    @index.when(method='GET', template='json')
    def index_get(self):
        ver = {
          "versions": [
            {
              "status": "CURRENT",
              "id": "v1.0",
              "links": [
                {
                  "href": request.application_url + "/v1/",
                  "rel": "self"
                }
              ]
            }
          ]
        }

        return ver

    @expose('error.html')
    @error_wrapper
    def error(self, status):
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)
