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
#import uuid

#from sqlalchemy import Column, Integer, String, Sequence
#from sqlalchemy.orm import relationship, backref
#from sqlalchemy.orm.exc import DetachedInstanceError

from allegro.models.music import Base, Query
#from allegro.models.sqlalchemy import Base


class Plan(Base):
    __tablename__ = 'plans'

    id = None
    name = None
    stack_id = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'id': 'text',
            'name': 'text',
            'stack_id': 'text',
            'PRIMARY KEY': '(id)'
        }
        return schema

    @classmethod
    def pk_name(cls):
        return 'id'

    def pk_value(self):
        return self.id

    def values(self):
        return {
            'name': self.name,
            'stack_id': self.stack_id,
        }

    def __init__(self, name, stack_id, _insert=True):
        self.name = name
        self.stack_id = stack_id
        if _insert:
            self.insert()

    def placements(self):
        all_results = Query("Placement").all()
        results = []
        for placement in all_results:
            if placement.plan_id == self.id:
                results.append(placement)
        return results

    @property
    def orchestration_ids(self):
        #return list(set([p.orchestration_id for p in self.placements.all()]))
        return list(set([p.orchestration_id for p in self.placements()]))

    def __repr__(self):
        try:
            return '<Plan %r>' % self.name
        except DetachedInstanceError:
            return '<Plan detached>'

    def __json__(self):
        json_ = {}
        json_['id'] = self.id
        json_['stack_id'] = self.stack_id
        json_['name'] = self.name
        json_['placements'] = {}
        #for placement in self.placements.all():
        for placement in self.placements():
            json_['placements'][placement.orchestration_id] = dict(
                name=placement.name,
                location=placement.location
            )
        return json_
