import uuid

from sqlalchemy import Column, Integer, String, ForeignKey, Sequence
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import DetachedInstanceError

from allegro.models import Base


class Placement(Base):
    __tablename__ = 'placements'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False, unique=True, index=True) 
    orchestration_id = Column(String(36), nullable=False, unique=True, index=True)
    location = Column(String(256))

    plan_id = Column(String(36), ForeignKey('plans.id'))
    plan = relationship("Plan", backref=backref('placements',
                        cascade="all, delete-orphan", lazy='dynamic'))

    def __init__(self, name, orchestration_id, plan, location=None):
        self.name = name
        self.orchestration_id = orchestration_id
        self.plan = plan
        self.location = location

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

