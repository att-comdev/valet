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

from allegro.ostro_helper import Ostro
from pecan import expose, redirect, request, response
from pecan_notario import validate

import logging
from notario import decorators
from notario.validators import types
from webob.exc import status_map

logger = logging.getLogger(__name__)


class GroupsController(object):

    # Dictionary of all groups
    # Type can be exclusivity, affinity, or diversity
    #
    #   {
    #     "c7a6014f-b348-4a1f-a08a-fe02786b2936": {
    #       "name": "group",
    #       "description": "My Awesome Group",
    #       "type": "exclusivity",
    #       "members": [
    #         "922c5cab-6a1b-4e1e-bb10-331633090c41",
    #         "b71bedad-dd57-4942-a7bd-ab074b72d652"
    #       ]
    #     }
    #   }

    # POST /v1/TENANT_ID/groups
    # GET /v1/TENANT_ID/groups
    # GET /v1/TENANT_ID/groups/GROUP_ID
    # UPDATE /v1/TENANT_ID/groups/GROUP_ID
    # DELETE /v1/TENANT_ID/groups/GROUP_ID

    @expose(generic=True, template='json')
    def index(self):
        '''Get groups!'''
        groups_array = []
        # TODO: Enumerate the groups.
        return groups_array
