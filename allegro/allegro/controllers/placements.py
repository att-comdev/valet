import simplejson

from allegro import models
from allegro.controllers import error
from allegro.models import Placement
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
        #elif request.method == 'DELETE':
        #    error('/v1/errors/not_allowed',
        #          'DELETE requests to this url are not allowed')
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
