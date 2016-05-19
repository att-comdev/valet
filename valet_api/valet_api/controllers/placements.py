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

from valet_api.controllers import reserve_placement
from valet_api.controllers import update_placements
from valet_api.controllers import error
from valet_api.common.i18n import _
from valet_api.models import Placement, Plan
from valet_api.common.ostro_helper import Ostro

from pecan import expose, request, response

LOG = logging.getLogger(__name__)

# pylint: disable=R0201


class PlacementsItemController(object):
    '''
    Placements Item Controller
    /v1/placements/{placement_id}
    '''

    def __init__(self, uuid4):
        '''Initializer.'''
        self.uuid = uuid4
        self.placement = Placement.query.filter_by(  # pylint: disable=E1101
            id=self.uuid).first()
        if not self.placement:
            self.placement = Placement.query.filter_by(  # pylint: disable=E1101
                orchestration_id=self.uuid).first()
            if not self.placement:
                error('/errors/not_found', _('Placement not found'))
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
        Use POST for reserving placements made by a scheduler.
        '''
        return self.placement

    @index.when(method='POST', template='json')
    def index_post(self, **kwargs):
        '''
        Reserve a placement. This and other placements may be replanned.
        Once reserved, the location effectively becomes immutable.
        '''
        LOG.info(_('Placement reservation request for orchestration id %s'),
                 self.placement.orchestration_id)
        locations = kwargs.get('locations', [])
        locations_str = ', '.join(locations)
        LOG.info(_('Candidate locations: %s'), locations_str)
        if self.placement.location in locations:
            # Ostro's placement is in the list of candidates. Good!
            reserve_placement(self.placement)
            response.status = 200
        else:
            # Ostro's placement is NOT in the list of candidates.
            # Time for Plan B.
            LOG.info(_('Placement of %(orch_id)s in %(loc)s ' \
                       'not allowed. Replanning.'),
                     {'orch_id': self.placement.orchestration_id,
                      'loc': self.placement.location})

            # Unreserve the placement in case it was previously reserved.
            reserve_placement(self.placement, False)

            # Find all the reserved placements for the related plan.
            reserved = Placement.query.filter_by(  # pylint: disable=E1101
                plan_id=self.placement.plan_id, reserved=True)

            # Keep this placement's orchestration ID handy.
            orchestration_id = self.placement.orchestration_id

            # Extract all the orchestration IDs.
            exclusions = [x.orchestration_id for x in reserved]
            if exclusions:
                exclusions_str = ', '.join(exclusions)
                LOG.info(_('Excluded orchestration IDs: %s'),
                         exclusions_str)
            else:
                LOG.info(_('No excluded orchestration IDs.'))

            # Ask Ostro to try again with new constraints.
            # We may get one or more updated placements in return.
            # One of those will be the original placement
            # we are trying to reserve.
            plan = Plan.query.filter_by(  # pylint: disable=E1101
                id=self.placement.plan_id).first()
            args = {
                "stack_id": plan.stack_id,
                "locations": locations,
                "orchestration_id": orchestration_id,
                "exclusions": exclusions,
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
            response.status = 201

        placement = Placement.query.filter_by(  # pylint: disable=E1101
            orchestration_id=self.placement.orchestration_id).first()
        return placement

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete a Placement'''
        orch_id = self.placement.orchestration_id
        self.placement.delete()
        LOG.info(_('Placement with orchestration id %s deleted.'), orch_id)
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
    def _lookup(self, uuid4, *remainder):
        '''Pecan subcontroller routing callback'''
        return PlacementsItemController(uuid4), remainder
