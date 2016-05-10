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
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Plans'''

import logging

from allegro.controllers import set_placements, error
from allegro.i18n import _
from allegro.models import Plan
from allegro.ostro_helper import Ostro

from notario import decorators
from notario.validators import types
from pecan import expose, request, response
from pecan_notario import validate

LOG = logging.getLogger(__name__)

CREATE_SCHEMA = (
    ('plan_name', types.string),
    ('resources', types.dictionary),
    ('stack_id', types.string),
    (decorators.optional('timeout'), types.string)
)

UPDATE_SCHEMA = (
    ('plan_name', types.string),
    ('resources', types.dictionary),
    ('resources_update', types.dictionary),
    ('stack_id', types.string),
    (decorators.optional('timeout'), types.string)
)

# pylint: disable=R0201


class PlansItemController(object):
    '''
    Plans Item Controller
    /v1/{tenant_id}/plans/{plan_id}
    '''

    placements = None

    def __init__(self, uuid4):
        self.uuid = uuid4
        self.plan = Plan.query.filter_by(  # pylint: disable=E1101
            id=self.uuid).first()
        if not self.plan:
            self.plan = Plan.query.filter_by(  # pylint: disable=E1101
                stack_id=self.uuid).first()
            if not self.plan:
                error('/errors/not_found', _('Plan not found'))
        request.context['plan_id'] = self.plan.id

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,PUT,DELETE'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Get plan'''
        return self.plan

    @index.when(method='PUT', template='json')
    @validate(UPDATE_SCHEMA, '/errors/schema')
    def index_put(self):
        '''Update a Plan'''
        # FIXME: Possible Ostro regression?
        # New placements are not being seen in the response, so
        # set_placements is currently failing as a result.
        ostro = Ostro()
        args = request.json

        kwargs = {
            'tenant_id': request.context['tenant_id'],
            'args': args
        }

        # Prepare the request. If request prep fails,
        # an error message will be in the response.
        # Though the Ostro helper reports the error,
        # we cite it as a Valet error.
        if not ostro.request(**kwargs):
            message = ostro.response['status']['message']
            error('/errors/conflict',
                  _('Valet error: %s') % message)

        ostro.send()
        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error('/errors/invalid',
                  _('Ostro error: %s') % message)

        # TODO: See if we will eventually need these for Ostro.
        #plan_name = args['plan_name']
        #stack_id = args['stack_id']
        resources = ostro.request['resources_update']
        placements = ostro.response['resources']

        set_placements(self.plan, resources, placements)
        response.status = 201

        # Flush so that the DB is current.
        self.plan.flush()
        return self.plan

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete a Plan'''
        for placement in self.plan.placements():
            placement.delete()
        self.plan.delete()
        response.status = 204

class PlansController(object):
    '''
    Plans Controller
    /v1/{tenant_id}/plans
    '''

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,POST'

    @expose(generic=True, template='json')
    def index(self):
        '''Catchall for unallowed methods'''
        message = _('The %s method is not allowed.') % request.method
        kwargs = {'allow': self.allow()}
        error('/errors/not_allowed', message, **kwargs)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Options'''
        response.headers['Allow'] = self.allow()
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Get all the plans'''
        plans_array = []
        for plan in Plan.query.all():  # pylint: disable=E1101
            plans_array.append(plan.name)
        return plans_array

    @index.when(method='POST', template='json')
    @validate(CREATE_SCHEMA, '/errors/schema')
    def index_post(self):
        '''Create a Plan'''
        ostro = Ostro()
        args = request.json

        kwargs = {
            'tenant_id': request.context['tenant_id'],
            'args': args
        }

        # Prepare the request. If request prep fails,
        # an error message will be in the response.
        # Though the Ostro helper reports the error,
        # we cite it as a Valet error.
        if not ostro.request(**kwargs):
            message = ostro.response['status']['message']
            error('/errors/conflict',
                  _('Valet error: %s') % message)

        ostro.send()
        status_type = ostro.response['status']['type']
        if status_type != 'ok':
            message = ostro.response['status']['message']
            error('/errors/server_error',
                  _('Ostro error: %s') % message)

        plan_name = args['plan_name']
        stack_id = args['stack_id']
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
            error('/errors/server_error',
                  _('Unable to create Plan.'))

    @expose()
    def _lookup(self, uuid4, *remainder):
        '''Pecan subcontroller routing callback'''
        return PlansItemController(uuid4), remainder
