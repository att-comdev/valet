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

#from sqlalchemy import Column, Integer, String, ForeignKey, Sequence
#from sqlalchemy.orm import relationship, backref
#from sqlalchemy.orm.exc import DetachedInstanceError

from . import Base, Query


class Placement(Base):
    __tablename__ = 'placements'

    id = None
    name = None
    orchestration_id = None
    location = None
    plan_id = None
    plan = None

    @classmethod
    def schema(cls):
        '''Return schema.'''
        schema = {
            'id': 'text',
            'name': 'text',
            'orchestration_id': 'text',
            'location': 'text',
            'plan_id': 'text',
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
            'orchestration_id': self.orchestration_id,
            'location': self.location,
            'plan_id': self.plan_id
        }

    def __init__(self, name, orchestration_id, plan=None,
                 plan_id=None, location=None, _insert=True):
        super(Placement, self).__init__()
        self.name = name
        self.orchestration_id = orchestration_id
        if plan_id:
            plan = Query("Plan").filter_by(id=plan_id).first()
        self.plan = plan
        self.plan_id = plan.id
        self.location = location
        if _insert:
            self.insert()

    def __repr__(self):
        try:
            return '<Plan %r>' % self.name
        except DetachedInstanceError:
            return '<Plan detached>'

    def __json__(self):
        json_ = {}
        json_['id'] = self.id
        json_['name'] = self.name
        json_['orchestration_id'] = self.orchestration_id
        json_['location'] = self.location
        json_['plan_id'] = self.plan.id
        return json_

