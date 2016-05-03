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

from allegro import models
from allegro.controllers import error
# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Group
#from allegro.models.sqlalchemy import Group

import logging
from notario import decorators
from notario.validators import types
from pecan import conf, expose, redirect, request, response
from pecan_notario import validate
from webob.exc import status_map

logger = logging.getLogger(__name__)

groups_schema = (
    ('description', types.string),
    ('name', types.string),
    (decorators.optional('type'), types.string)
)

update_groups_schema = (
    (decorators.optional('description'), types.string),
    (decorators.optional('name'), types.string),
    (decorators.optional('type'), types.string)
)

members_schema = (
    ('members', types.array)
)


class MembersItemController(object):
    # /v1/PROJECT_ID/groups/GROUP_ID/members/MEMBER_ID

    def __init__(self, member_id):
        """Initialize group member"""
        group = request.context['group']
        if not member_id in group.members:
            error('/errors/not_found',
                  'Member not found in group')
        request.context['member_id'] = member_id

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/errors/not_allowed', message)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Supported methods'''
        response.headers['Allow'] = 'GET,DELETE'
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''Verify group member'''
        response.status = 204

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kw):
        """Delete group member"""
        group = request.context['group']
        member_id = request.context['member_id']
        group.members.remove(member_id)
        group.update()
        response.status = 204

class MembersController(object):
    # /v1/PROJECT_ID/groups/GROUP_ID/members

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/errors/not_allowed', message)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Supported methods'''
        response.headers['Allow'] = 'GET,POST,PUT,DELETE'
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''List group members'''
        group = request.context['group']
        return {'members': group.members}

    @index.when(method='POST', template='json')
    @validate(members_schema, '/errors/schema')
    def index_post(self, **kwargs):
        """Set/replace all group members"""
        new_members = kwargs.get('members', [])

        if not conf.identity.engine.is_tenant_list_valid(new_members):
            error('/errors/conflict',
                  'Member list contains invalid tenant IDs')

        group = request.context['group']
        group.members = new_members
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='PUT', template='json')
    @validate(members_schema, '/errors/schema')
    def index_put(self, **kwargs):
        """Add one or more members to a group"""
        new_members = kwargs.get('members', None)

        if not conf.identity.engine.is_tenant_list_valid(new_members):
            error('/errors/conflict',
                  'Member list contains invalid tenant IDs')

        group = request.context['group']
        group.members = list(set(group.members + new_members))
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self, **kw):
        """Delete all group members"""
        group = request.context['group']
        group.members = []
        group.update()
        response.status = 204

    @expose()
    def _lookup(self, member_id, *remainder):
        return MembersItemController(member_id), remainder

class GroupsItemController(object):
    # /v1/PROJECT_ID/groups/GROUP_ID
    members = MembersController()

    def __init__(self, group_id):
        """Initialize group"""
        group = Group.query.filter_by(id=group_id).first()
        if not group:
            error('/errors/not_found', 'Group not found')
        request.context['group'] = group

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/errors/not_allowed', message)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Supported methods'''
        response.headers['Allow'] = 'GET,PUT,DELETE'
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        """Display a group"""
        return request.context['group']

    @index.when(method='PUT', template='json')
    @validate(update_groups_schema, '/errors/schema')
    def index_put(self, **kwargs):
        """Update a group"""
        # Members are updated in the /v1/groups/members controller.
        group = request.context['group']
        group.name = \
            kwargs.get('name', group.name)
        group.description = \
            kwargs.get('description', group.description)
        group.type = \
            kwargs.get('type', group.type)
        group.update()
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        """Delete a group"""
        group = request.context['group']
        if type(group.members) is list and len(group.members) > 0:
            error('/errors/conflict',
                  'Unable to delete a Group with members.')
        group.delete()
        response.status = 204

class GroupsController(object):
    # /v1/PROJECT_ID/groups

    @expose(generic=True, template='json')
    def index(self):
        message = 'The %s method is not allowed.' % request.method
        error('/errors/not_allowed', message)

    @index.when(method='OPTIONS', template='json')
    def index_options(self):
        '''Supported methods'''
        response.headers['Allow'] = 'GET,POST'
        response.status = 204

    @index.when(method='GET', template='json')
    def index_get(self):
        '''List groups'''
        groups_array = []
        for group in Group.query.all():
            groups_array.append(group.id)
        return {'groups': groups_array}

    @index.when(method='POST', template='json')
    @validate(groups_schema, '/errors/schema')
    def index_post(self, **kwargs):
        """Create a group"""
        group_name = kwargs.get('name', None)
        description = kwargs.get('description', None)
        group_type = kwargs.get('type', None)
        members = []  # Use /v1/groups/members endpoint to add members

        group = Group(group_name, description, group_type, members)
        if group:
            response.status = 201

            # Flush so that the DB is current.
            group.flush()
            return group
        else:
            error('/errors/server_error',
                  'Unable to create Group.')

    @expose()
    def _lookup(self, group_id, *remainder):
        return GroupsItemController(group_id), remainder
