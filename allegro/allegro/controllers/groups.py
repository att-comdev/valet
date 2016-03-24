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
from allegro.controllers import error
# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Group, Query
#from allegro.models.sqlalchemy import Group
from pecan import expose, redirect, request, response
from pecan_notario import validate

import logging
from notario import decorators
from notario.validators import types
from webob.exc import status_map

logger = logging.getLogger(__name__)

create_schema = (
    ('description', types.string),
    ('members', types.array),
    ('name', types.string),
    (decorators.optional('type'), types.string)
)

update_schema = (
    ('description', types.string),
    ('members', types.array),
    ('name', types.string),
    (decorators.optional('type'), types.string)
)


class GroupsItemController(object):
    placements = None

    def __init__(self, uuid4):
        self.uuid = uuid4
        self.group = Group.query.filter_by(id=self.uuid).first()
        if not self.group:
            error('/v1/errors/not_found', 'Group not found')
        request.context['group_id'] = self.group.id

    @expose(generic=True, template='json')
    def index(self):
        if request.method == 'POST':
            error('/v1/errors/not_allowed',
                  'POST requests to this url are not allowed')
        return self.group

    @index.when(method='PUT', template='json')
    @validate(update_schema, '/v1/errors/schema')
    def index_put(self, **kw):
        """Update a Group"""
        kwargs = request.json

        group_name = kwargs['name']
        description = kwargs['description']
        group_type = kwargs['type']
        members = kwargs['members']

        # TODO: Update the group
        response.status = 201

        # Flush so that the DB is current.
        self.group.flush()
        return self.group

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kw):
        """Delete a Group"""
        self.group.delete()
        response.status = 204

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
        for group in Group.query.all():
            groups_array.append(group.name)
        return groups_array

    @index.when(method='POST', template='json')
    @validate(create_schema, '/v1/errors/schema')
    def index_post(self, **kw):
        """Create a group"""
        kwargs = request.json

        group_name = kwargs['name']
        description = kwargs['description']
        group_type = kwargs['type']
        members = kwargs['members']

        group = Group(group_name, description, group_type, members)
        if group:
            response.status = 201

            # Flush so that the DB is current.
            group.flush()
            return group
        else:
            error('/v1/errors/invalid',
                  'Unable to create Group.')

    @expose()
    def _lookup(self, uuid4, *remainder):
        return GroupsItemController(uuid4), remainder
