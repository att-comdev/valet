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

'''Plan Model'''

import uuid

from sqlalchemy import Column, String
from sqlalchemy.orm.exc import DetachedInstanceError

from valet_api.models.sqlalchemy import Base


class Plan(Base):  # pylint: disable=R0903
    '''Plan Model'''
    __tablename__ = 'plans'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # pylint: disable=C0103
    name = Column(String(64), nullable=False, unique=True, index=True)
    stack_id = Column(String(36), nullable=False, unique=True, index=True)

    def __init__(self, name, stack_id):
        self.name = name
        self.stack_id = stack_id

    @property
    def orchestration_ids(self):
        '''Return a list of orchestration IDs'''
        return list(set([p.orchestration_id for p in self.placements.all()]))

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
        for placement in self.placements.all():
            json_['placements'][placement.orchestration_id] = dict(
                name=placement.name,
                location=placement.location
            )
        return json_
