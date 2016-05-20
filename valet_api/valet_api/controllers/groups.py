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

'''Groups'''

import logging

from valet_api.controllers import error, group_name_type, notify
from valet_api.common.i18n import _
from valet_api.models import Group

from notario import decorators
from notario.validators import types
from pecan import conf, expose, request, response
from pecan_notario import validate

LOG = logging.getLogger(__name__)

GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string),
    ('name', group_name_type),
    ('type', types.string)
)

UPDATE_GROUPS_SCHEMA = (
    (decorators.optional('description'), types.string)
)

MEMBERS_SCHEMA = (
    ('members', types.array)
)

# pylint: disable=R0201


class MembersItemController(object):
    '''
    Members Item Controller
    /v1/groups/{group_id}/members/{member_id}
    '''

    def __init__(self, member_id):
        '''Initialize group member'''
        group = request.context['group']
        if not member_id in group.members:
            error('/errors/not_found',
                  _('Member not found in group'))
        request.context['member_id'] = member_id

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'GET,DELETE'

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
        '''Verify group member'''
        response.status = 204

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete group member'''
        group = request.context['group']
        member_id = request.context['member_id']
        group.members.remove(member_id)
        group.update()
        notify(sub_event_type='group.update', data=group)
        response.status = 204

class MembersController(object):
    '''
    Members Controller
    /v1/groups/{group_id}/members
    '''

    @classmethod
    def allow(cls):
        '''Allowed methods'''
        return 'PUT,DELETE'

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

    @index.when(method='PUT', template='json')
    @validate(MEMBERS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        '''Add one or more members to a group'''
        new_members = kwargs.get('members', None)

        if not conf.identity.engine.is_tenant_list_valid(new_members):
            error('/errors/conflict',
                  _('Member list contains invalid tenant IDs'))

        group = request.context['group']
        group.members = list(set(group.members + new_members))
        group.update()
        notify(sub_event_type='group.update', data=group)
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete all group members'''
        group = request.context['group']
        group.members = []
        group.update()
        notify(sub_event_type='group.update', data=group)
        response.status = 204

    @expose()
    def _lookup(self, member_id, *remainder):
        '''Pecan subcontroller routing callback'''
        return MembersItemController(member_id), remainder

class GroupsItemController(object):
    '''
    Groups Item Controller
    /v1/groups/{group_id}
    '''

    members = MembersController()

    def __init__(self, group_id):
        '''Initialize group'''
        group = Group.query.filter_by(  # pylint: disable=E1101
            id=group_id).first()
        if not group:
            error('/errors/not_found', _('Group not found'))
        request.context['group'] = group

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
        '''Display a group'''
        return {"group": request.context['group']}

    @index.when(method='PUT', template='json')
    @validate(UPDATE_GROUPS_SCHEMA, '/errors/schema')
    def index_put(self, **kwargs):
        '''Update a group'''
        # Name and type are immutable.
        # Group Members are updated in MembersController.
        group = request.context['group']
        group.description = kwargs.get('description', group.description)
        group.update()
        notify(sub_event_type='group.update', data=group)
        response.status = 201

        # Flush so that the DB is current.
        group.flush()
        return group

    @index.when(method='DELETE', template='json')
    def index_delete(self):
        '''Delete a group'''
        group = request.context['group']
        if isinstance(group.members, list) and len(group.members) > 0:
            error('/errors/conflict',
                  _('Unable to delete a Group with members.'))
        notify(sub_event_type='group.delete', data=group)
        group.delete()
        response.status = 204

class GroupsController(object):
    '''
    Groups Controller
    /v1/groups
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
        '''List groups'''
        groups_array = []
        for group in Group.query.all():  # pylint: disable=E1101
            groups_array.append(group)
        return {'groups': groups_array}

    @index.when(method='POST', template='json')
    @validate(GROUPS_SCHEMA, '/errors/schema')
    def index_post(self, **kwargs):
        '''Create a group'''
        group_name = kwargs.get('name', None)
        description = kwargs.get('description', None)
        group_type = kwargs.get('type', None)
        members = []  # Use /v1/groups/members endpoint to add members

        group = Group(group_name, description, group_type, members)
        if group:
            response.status = 201
            notify(sub_event_type='group.create', data=group)

            # Flush so that the DB is current.
            group.flush()
            return group
        else:
            error('/errors/server_error',
                  _('Unable to create Group.'))

    @expose()
    def _lookup(self, group_id, *remainder):
        '''Pecan subcontroller routing callback'''
        return GroupsItemController(group_id), remainder
