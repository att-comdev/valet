from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import scoped_session, sessionmaker, object_session, mapper
from sqlalchemy.ext.declarative import declarative_base
from pecan import conf


class _EntityBase(object):
    """
    A custom declarative base that provides some Elixir-inspired shortcuts.
    """

    # FIXME: Either SQLAlchemy doesn't pass utf8 down to MySQL as
    # requested in config.py, or MySQL is ignoring the setting outright,
    # so we're forcing it here. Alas, that means we have MySQL-specific
    # stuff in here for now.
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    @classmethod
    def filter_by(cls, *args, **kwargs):
        return cls.query.filter_by(*args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.query.get(*args, **kwargs)

    def flush(self, *args, **kwargs):
        object_session(self).flush([self], *args, **kwargs)

    def delete(self, *args, **kwargs):
        object_session(self).delete(self, *args, **kwargs)

    def as_dict(self):
        return dict((k, v) for k, v in self.__dict__.items()
                    if not k.startswith('_'))

Session = scoped_session(sessionmaker())
metadata = MetaData()
Base = declarative_base(cls=_EntityBase)
Base.query = Session.query_property()

# Listeners

@event.listens_for(mapper, 'init')
def auto_add(target, args, kwargs):
    Session.add(target)

# Utilities

def get_or_create(model, **kwargs):
    instance = model.filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        commit()
        return instance

def init_model():
    """
    This is a stub method which is called at application startup time.

    If you need to bind to a parse database configuration, set up tables or
    ORM classes, or perform any database initialization, this is the
    recommended place to do it.

    For more information working with databases, and some common recipes,
    see http://pecan.readthedocs.org/en/latest/databases.html

    For creating all metadata you would use::

        Base.metadata.create_all(conf.sqlalchemy.engine)

    """
    conf.sqlalchemy.engine = _engine_from_config(conf.sqlalchemy)
    Session.configure(bind=conf.sqlalchemy.engine)

def _engine_from_config(configuration):
    configuration = dict(configuration)
    url = configuration.pop('url')
    return create_engine(url, **configuration)

def start():
    Session()
    metadata.bind = conf.sqlalchemy.engine

def start_read_only():
    start()

def commit():
    Session.commit()

def rollback():
    Session.rollback()

def clear():
    Session.remove()
    Session.close()

def flush():
    Session.flush()

from plans import Plan  # noqa
from placements import Placement  # noqa
