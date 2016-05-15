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

'''Placements'''

import logging

from allegro.controllers import update_placements, error
from allegro.i18n import _
from allegro.models import Placement
from allegro.ostro_helper import Ostro

from pecan import expose, request, response

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class PlacementsItemController(object):
    '''
    Placements Item Controller
    /v1/placements/{placement_id}
    '''

    def __init__(self, orchestration_id):
        '''Initializer'''
        self.orchestration_id = orchestration_id
        self.placement = Placement.query.filter_by(  # pylint: disable=E1101
            orchestration_id=self.orchestration_id).first()
        if not self.placement:
            error('/errors/not_found',
                  _('Placement not found'))
        request.context['placement_id'] = self.placement.id

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,POST,DELETE'

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
        '''
        Inspect a placement.
        Use POST for confirming placements from a scheduler.
        '''
        return self.placement

    @index.when(method='POST', template='json')
    def index_post(self, **kwargs):
        '''
        Reserve a placement. This and other placements may be replanned.
        Once reserved, the location effectively becomes immutable.
        '''
        locations = kwargs.get('locations', [])
        if self.placement.location in locations:
            # Ostro's placement is in the list of candidates. Good!
            response.status = 200
            return self.placement
        else:
            # Ostro's placement is NOT in the list of candidates.
            # Time for Plan B.

            # Find all the reserved placements for the related plan.
            reserved = Placement.query.filter_by(  # pylint: disable=E1101
                plan_id=self.placement.plan_id, reserved=True)

            # Extract all the orchestration IDs.
            # Keep this placement's orchestration ID handy.
            exclusions = [x.orchestration_id for x in reserved]
            orchestration_id = self.placement.orchestration_id

            # Ask Ostro to try again with new constraints.
            # We may get one or more updated placements in return.
            # One of those will be the original placement
            # we are trying to reserve.
            args = {
                "stack_id": self.placement.plan_id,
                "locations": locations,
                "orchestration_id": orchestration_id,
                "exclusions": exclusions
            }
            ostro_kwargs = {
                "args": args,
            }
            ostro = Ostro()
            ostro.replan(**ostro_kwargs)
            ostro.send()

            status_type = ostro.response['status']['type']
            if status_type != 'ok':
                message = ostro.response['status']['message']
                error(ostro.error_uri, _('Ostro error: %s') % message)

            # Update all affected placements. Reserve the original one.
            placements = ostro.response['resources']
            update_placements(placements, reserve_id=orchestration_id)
            placement = Placement.query.filter_by(  # pylint: disable=E1101
                orchestration_id=orchestration_id).first()

            response.status = 201

            return placement

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete a Placement'''
        self.placement.delete()
        response.status = 204


class PlacementsController(object):
    '''
    Placements Controller
    /v1/placements
    '''

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET'

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
        '''Get placements.'''
        placements_array = []
        for placement in Placement.query.all():  # pylint: disable=E1101
            placements_array.append(placement)
        return placements_array

    @expose()
    def _lookup(self, orchestration_id, *remainder):
        '''Pecan subcontroller routing callback'''
        return PlacementsItemController(orchestration_id), remainder
