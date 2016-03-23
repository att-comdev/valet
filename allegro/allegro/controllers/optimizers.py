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


class OptimizersController(object):

    # Dictionary of all registered optimizers
    #
    #   {
    #     "e624474b-fc80-4053-ab5f-45cc1030e692": {
    #       "name": "ostro",
    #       "version": "2.0",
    #       "ping": "ok"
    #     }
    #   }

    # GET /v1/TENANT_ID/optimizers

    @expose(generic=True, template='json')
    def index(self):
        '''Get optimizers!'''
        optimizers_array = []
        # TODO: Enumerate the optimizers.
        return optimizers_array
