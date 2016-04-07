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

from pecan import conf
from pecan import expose
from pecan import request
from pecan.secure import SecureController, secure
from webob.exc import status_map

from allegro.controllers import v1
from allegro.controllers.errors import error_wrapper

import logging

logger = logging.getLogger(__name__)


class RootController(SecureController):
    v1 = v1.V1Controller()

    @classmethod
    def check_permissions(cls):
        auth_token = request.headers.get('X-Auth-Token')
        if auth_token:
            return conf.identity.engine.is_admin(auth_token)
        return False

    # TODO: No need to respond to this endpont. Throw a 404.
    @expose(generic=True, template='json')
    def index(self):
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
