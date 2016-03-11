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

import inspect
import uuid

from music import Music
from pecan import conf


class Results(list):
    def __init__(self, *args, **kwargs):
        super(Results, self).__init__(args[0])

    def all(self):
        return self

    def first(self):
        if len(self) > 0:
            return self[0]

class Query(object):
    model = None

    def __init__(self, model):
        if inspect.isclass(model):
            self.model = model
        elif isinstance(model, basestring):
            self.model = eval(model)

    def __kwargs(self):
        '''Return common keyword args.'''
        keyspace = conf.music.get('keyspace')
        kwargs = {
            'keyspace': keyspace,
            'table': self.model.__tablename__,
        }
        return kwargs

    def __rows_to_objects(self, rows):
        results = []
        pk_name = self.model.pk_name()
        for row_id, row in rows.iteritems():
            the_id = row.pop(pk_name)
            result = self.model(_insert=False, **row)
            setattr(result, pk_name, the_id)
            results.append(result)
        return Results(results)

    def all(self):
        kwargs = self.__kwargs()
        rows = conf.music.engine.read_all_rows(**kwargs)
        return self.__rows_to_objects(rows)

    def filter_by(self, **kwargs):
        # Music doesn't allow filtering on anything but the primary key.
        # We need to get all items and then go looking for what we want.
        all_items = self.all()
        filtered_items = Results([])
         
        # Only look at the first key/value.
        for key, value in kwargs.items():
            for item in all_items:
                if getattr(item, key) == value:
                    filtered_items.append(item)
        return filtered_items
                    
class Base(object):
    """
    A custom declarative base that provides some Elixir-inspired shortcuts.
    """

    @classmethod
    def __kwargs(cls):
        '''Return common keyword args.'''
        keyspace = conf.music.get('keyspace')
        kwargs = {
            'keyspace': keyspace,
            'table': cls.__tablename__,
        }
        return kwargs

    @classmethod
    def create_table(cls):
        '''Create table.'''
        kwargs = cls.__kwargs()
        kwargs['schema'] = cls.schema()
        conf.music.engine.create_table(**kwargs)

    def insert(self):
        '''Insert row.'''
        kwargs = self.__kwargs()
        kwargs['values'] = self.values()
        pk_name = self.pk_name()
        if not pk_name in kwargs['values']:
            the_id = str(uuid.uuid4())
            kwargs['values'][pk_name] = the_id
            setattr(self, pk_name, the_id)
        conf.music.engine.create_row(**kwargs)
        
    def update(self):
        '''Update row.'''
        kwargs = self.__kwargs()
        kwargs['pk_name'] = self.pk_name()
        kwargs['pk_value'] = self.pk_value()
        kwargs['values'] = self.values()
        conf.music.engine.update_row_atomically(**kwargs)

    def delete(self):
        '''Delete row.'''
        kwargs = self.__kwargs()
        kwargs['pk_name'] = self.pk_name()
        kwargs['pk_value'] = self.pk_value()
        conf.music.engine.delete_row_eventually(**kwargs)

    @classmethod
    def filter_by(cls, **kwargs):
        #return cls.query.filter_by(**kwargs)
        return Query(cls).filter_by(**kwargs)

    def flush(self, *args, **kwargs):
        #object_session(self).flush([self], *args, **kwargs)
        pass

    def delete(self, *args, **kwargs):
        #object_session(self).delete(self, *args, **kwargs)
        pass

    def as_dict(self):
        return dict((k, v) for k, v in self.__dict__.items()
                    if not k.startswith('_'))

def init_model():
    """
    This is a stub method which is called at application startup time.

    If you need to bind to a parse database configuration, set up tables or
    ORM classes, or perform any database initialization, this is the
    recommended place to do it.

    For more information working with databases, and some common recipes,
    see http://pecan.readthedocs.org/en/latest/databases.html

    For creating all metadata you would use::

        Base.metadata.create_all(conf.music.engine)

    """
    conf.music.engine = _engine_from_config(conf.music)
    keyspace = conf.music.get('keyspace')
    conf.music.engine.create_keyspace(keyspace)

def _engine_from_config(configuration):
    configuration = dict(configuration)
    kwargs = {
        'host': configuration.get('host'),
        'port': configuration.get('port')
    }
    return Music(**kwargs)

def start():
    pass

def start_read_only():
    start()

def commit():
    pass

def rollback():
    pass

def clear():
    pass

def flush():
    pass

from plans import Plan  # noqa
from placements import Placement  # noqa
from ostro import PlacementRequest, PlacementResult, Event  # noqa
