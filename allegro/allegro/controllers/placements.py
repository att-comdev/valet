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

import simplejson

from allegro import models
from allegro.controllers import error
# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Placement, Query
#from allegro.models.sqlalchemy import Placement
from pecan import expose, redirect, request, response
from webob.exc import status_map

import logging

logger = logging.getLogger(__name__)


class PlacementsItemController(object):
    def __init__(self, orchestration_id):
        self.orchestration_id = orchestration_id
        self.placement = Placement.query.filter_by(
                             orchestration_id=self.orchestration_id).first()
        if not self.placement:
            error('/v1/errors/not_found',
                  'Placement not found')
        request.context['placement_id'] = self.placement.id

    @expose(generic=True, template='json')
    def index(self):
        if request.method == 'POST':
            error('/v1/errors/not_allowed',
                  'POST requests to this url are not allowed')
        return self.placement

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kw):
        """Delete a Placement"""
        self.placement.delete()
        response.status = 204

class PlacementsController(object):
    # Get all the placements /v1/{tenant_id}/placements

    @expose(generic=True, template='json')
    def index(self):
        '''Get placements!'''
        placements_array = []
        for placement in Placement.query.all():
            placements_array.append(placement)
        return placements_array
    
    @expose()
    def _lookup(self, orchestration_id, *remainder):
        return PlacementsItemController(orchestration_id), remainder
