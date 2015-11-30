import uuid

from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import DetachedInstanceError

from allegro.models import Base


class Plan(Base):
    __tablename__ = 'plans'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False, unique=True, index=True)
    stack_id = Column(String(36), nullable=False, unique=True, index=True)

    def __init__(self, name, stack_id):
        self.name = name
        self.stack_id = stack_id

    @property
    def orchestration_ids(self):
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
