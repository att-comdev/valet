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
from allegro.controllers import update_placements, error
# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Placement
#from allegro.models.sqlalchemy import Placement
from allegro.ostro_helper import Ostro
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
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    @index.when(method='GET', template='json')
    def index_get(self):
        """Request a Placement"""
        return self.placement

    @index.when(method='POST', template='json')
    def index_post(self, **kwargs):
        """Request a Placement with possible replanning"""
        locations = kwargs.get('locations', [])
        if self.placement.location in locations:
            # Ostro's placement is in the list of candidates. Good!
            response.status = 200
            return self.placement
        else:
            # Time for Plan B. Ask Ostro to try again with new constraints.
            orchestration_id = self.placement.orchestration_id
            ostro_kwargs = {
                "action": "replan",
                "stack_id": self.placement.plan_id,
                "locations": locations,
                "orchestration_id": orchestration_id,
            }
            ostro = Ostro()
            ostro.request(**ostro_kwargs)
            ostro.send()

            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error('/v1/errors/server_error',
                      'Ostro error: %s' % message)

            #ostro.response = {
            #    "resources": {
            #        "b71bedad-dd57-4942-a7bd-ab074b72d652": {
            #            "properties": {
            #                "host": "qos101"
            #            }
            #        }
            #    }
	    #}

            placements = ostro.response['resources']
    
            update_placements(self.placement.plan, placements)
            placement = Placement.query.filter_by(
                            orchestration_id=orchestration_id).first()
            response.status = 201
        
            return placement

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kwargs):
        """Delete a Placement"""
        self.placement.delete()
        response.status = 204

class PlacementsController(object):
    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/v1/errors/not_allowed', message)

    # Get all the placements /v1/PROJECT_ID/placements
    @index.when(method='GET', template='json')
    def index_get(self):
        '''Get placements!'''
        placements_array = []
        for placement in Placement.query.all():
            placements_array.append(placement)
        return placements_array
    
    @expose()
    def _lookup(self, orchestration_id, *remainder):
        return PlacementsItemController(orchestration_id), remainder
