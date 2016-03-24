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
        
from allegro.controllers import errors
from allegro.controllers import tenant
    
import logging

logger = logging.getLogger(__name__)
    
        
class V1Controller(object):
    errors = errors.ErrorsController()

    @expose(generic=True, template='json')
    def index(self):
        ver = {
          "versions": [
            {
              "status": "CURRENT",
              "id": "v1.0",
              "links": [
                {
                  "href": request.application_url + "/v1/{tenant_id}/",
                  "rel": "self"
                }
              ]
            }
          ]
        }

        return ver

    @expose()
    def _lookup(self, tenant_id, *remainder):
        return tenant.TenantController(tenant_id), remainder
