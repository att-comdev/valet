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
#import uuid

#from sqlalchemy import Column, Integer, String, Sequence
#from sqlalchemy.orm import relationship, backref
#from sqlalchemy.orm.exc import DetachedInstanceError

from allegro.models.music import Base, Query
#from allegro.models.sqlalchemy import Base


class Group(Base):
    __tablename__ = 'groups'

    id = None
    name = None
    description = None
    type = None
    members = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'id': 'text',
            'name': 'text',
            'description': 'text',
            'type': 'text',
            'members': 'text',
            'PRIMARY KEY': '(id)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'id'

    def pk_value(self):
        return self.id

    def values(self):
        # Lists aren't directly supported in Music, so we have to
        # convert to/from json on the way out/in.
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'members': simplejson.dumps(self.members)
        }

    def __init__(self, name, description, type, members, _insert=True):
        super(Group, self).__init__()
        self.name = name
        self.description = description
        self.type = type
        if _insert:
            self.members = []  # members ignored at init time
            self.insert()
        else:
            # TODO: Support lists in Music
            self.members = simplejson.loads(members)

    def __repr__(self):
        try:
            return '<Group %r>' % self.name
        except DetachedInstanceError:
            return '<Group detached>'

    def __json__(self):
        json_ = {}
        json_['id'] = self.id
        json_['name'] = self.name
        json_['description'] = self.description
        json_['type'] = self.type
        json_['members'] = self.members
        return json_
