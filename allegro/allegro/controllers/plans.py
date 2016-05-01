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

from allegro import models
from allegro.controllers import set_placements, error
# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Plan, Placement
#from allegro.models.sqlalchemy import Plan, Placement 
from allegro.ostro_helper import Ostro
from pecan import expose, redirect, request, response
from pecan_notario import validate

import logging
from notario import decorators
from notario.validators import types
from webob.exc import status_map

logger = logging.getLogger(__name__)

create_schema = (
    ('plan_name', types.string),
    ('resources', types.dictionary),
    ('stack_id', types.string),
    (decorators.optional('timeout'), types.string)
)

update_schema = (
    ('plan_name', types.string),
    ('resources', types.dictionary),
    ('resources_update', types.dictionary),
    ('stack_id', types.string),
    (decorators.optional('timeout'), types.string)
)


class PlansItemController(object):
    placements = None

    def __init__(self, uuid4):
        self.uuid = uuid4
        self.plan = Plan.query.filter_by(id=self.uuid).first()
        if not self.plan:
            self.plan = Plan.query.filter_by(stack_id=self.uuid).first()
            if not self.plan:
                error('/v1/errors/not_found',
                    'Plan not found')
        request.context['plan_id'] = self.plan.id

    @expose(generic=True, template='json')
    def index(self):
        if request.method == 'POST':
            error('/v1/errors/not_allowed',
                  'POST requests to this url are not allowed')
        return self.plan

    @index.when(method='PUT', template='json')
    @validate(update_schema, '/v1/errors/schema')
    def index_put(self, **kw):
        """Update a Plan"""
        # FIXME: Possible Ostro regression or missing code for updates?
        # New placements are not being seen in the response, so
        # set_placements is currently failing as a result.
        kwargs = request.json
        ostro = Ostro()
        ostro.request(**kwargs)
        ostro.send()

        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error('/v1/errors/invalid',
                  'Ostro error: %s' % message)

        plan_name = kwargs['plan_name']
        stack_id = kwargs['stack_id']
        resources = ostro.request['resources_update']
        placements = ostro.response['resources']

        set_placements(self.plan, resources, placements)
        response.status = 201

        # Flush so that the DB is current.
        self.plan.flush()
        return self.plan

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kw):
        """Delete a Plan"""
        for placement in self.plan.placements():
            placement.delete()
        self.plan.delete()
        response.status = 204

class PlansController(object):
    # Get all the plans /v1/PROJECT_ID/plans

    @expose(generic=True, template='json')
    def index(self):
        '''Get plans!'''
        plans_array = []
        for plan in Plan.query.all():
            plans_array.append(plan.name)
        return plans_array
    
    @index.when(method='POST', template='json')
    @validate(create_schema, '/v1/errors/schema')
    def index_post(self, **kw):
        """Create a Plan"""
        kwargs = request.json
        ostro = Ostro()
        ostro.request(**kwargs)
        ostro.send()

        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error('/v1/errors/server_error',
                  'Ostro error: %s' % message)

        plan_name = kwargs['plan_name']
        stack_id = kwargs['stack_id']
        resources = ostro.request['resources']
        placements = ostro.response['resources']

        plan = Plan(plan_name, stack_id) 
        if plan:
            set_placements(plan, resources, placements)
            response.status = 201

            # Flush so that the DB is current.
            plan.flush()
            return plan
        else:
            error('/v1/errors/server_error',
                  'Unable to create Plan.')

    @expose()
    def _lookup(self, uuid4, *remainder):
        return PlansItemController(uuid4), remainder
