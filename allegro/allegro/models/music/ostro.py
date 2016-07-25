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

from . import Base, Query


class PlacementRequest(Base):
    __tablename__ = 'placement_requests'

    stack_id = None
    request = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'stack_id': 'text',
            'request': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'stack_id'

    def pk_value(self):
        return self.stack_id

    def values(self):
        return {
            'stack_id': self.stack_id,
            'request': self.request,
        }

    def __init__(self, request, stack_id=None, _insert=True):
        super(PlacementRequest, self).__init__()
        self.stack_id = stack_id
        self.request = request
        if _insert:
            self.insert()

    def __repr__(self):
        try:
            return '<PlacementRequest %r>' % self.name
        except DetachedInstanceError:
            return '<PlacementRequest detached>'

    def __json__(self):
        json_ = {}
        json_['stack_id'] = self.stack_id
        json_['request'] = self.request

class PlacementResult(Base):
    __tablename__ = 'placement_results'

    stack_id = None
    placement = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'stack_id': 'text',
            'placement': 'text',
            'PRIMARY KEY': '(stack_id)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'stack_id'

    def pk_value(self):
        return self.stack_id

    def values(self):
        return {
            'stack_id': self.stack_id,
            'placement': self.placement,
        }

    def __init__(self, placement, stack_id=None, _insert=True):
        super(PlacementResult, self).__init__()
        self.stack_id = stack_id
        self.placement = placement
        if _insert:
            self.insert()

    def __repr__(self):
        try:
            return '<PlacementResult %r>' % self.stack_id
        except DetachedInstanceError:
            return '<PlacementResult detached>'

    def __json__(self):
        json_ = {}
        json_['stack_id'] = self.stack_id
        json_['placement'] = self.placement
        return json_

class Event(Base):
    __tablename__ = 'events'

    event_id = None
    event = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'event_id': 'text',
            'event': 'text',
            'PRIMARY KEY': '(event_id)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'event_id'

    def pk_value(self):
        return self.event_id

    def values(self):
        return {
            'event_id': self.event_id,
            'event': self.event,
        }

    def __init__(self, event, event_id=None, _insert=True):
        super(Event, self).__init__()
        self.event_id = event_id
        self.event = event
        if _insert:
            self.insert()

    def __repr__(self):
        try:
            return '<Event %r>' % self.event_id
        except DetachedInstanceError:
            return '<Event detached>'

    def __json__(self):
        json_ = {}
        json_['event_id'] = self.event_id
        json_['event'] = self.event
