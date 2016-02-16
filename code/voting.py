#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2016 AT&T
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

import json
import time

import requests


class REST:
    host = None
    port = None
    path = None

    def __init__(self, host='localhost', port=8080, path='/'):
        # FIXME: Ensure values are legit
        self.host = host # IP or FQDN
        self.port = port # Port Number
        self.path = path # Path starting with /

    @property
    def __url(self):
        # Must end without a slash
        return 'http://%(host)s:%(port)s%(path)s' % {
                'host': self.host,
                'port': self.port,
                'path': self.path
            }

    def __headers(self, content_type='application/json'):
        headers = {
            'accept': content_type,
            'content-type': content_type
        }
        return headers

    def request(self, method='get', content_type='application/json',
                path='/', data={}):
        if method not in ('post', 'get', 'put', 'delete'):
            raise KeyError("Method must be one of post, get, put, or delete.")
        fn = getattr(requests, method)

        # FIXME: Ensure path starts with /
        url = self.__url + path
        r = fn(url, data=json.dumps(data),
               headers=self.__headers(content_type))
        r.raise_for_status()
        return r


class MusicApp:
    current_time_millis = lambda self: int(round(time.time()*1000))

    keyspace_name = None
    lock_names = None
    table_name = None
    pk_name = None

    lock_timeout = None # Maximum time in seconds to acquire a lock

    rest = REST(path='/MUSIC/rest')

    def __init__(self, name='App', lock_timeout=10):
        # Randomize the name so that people don't step on each other.
        self.keyspace_name = name + str(self.current_time_millis()/100)
        self.lock_names = []
        self.lock_timeout = lock_timeout

    def create_keyspace(self):
        data = {
            'replicationInfo': {
                'class': 'SimpleStrategy',
                'replication_factor': 1
            },
            'durabilityOfWrites': True,
            'consistencyInfo': {
                'type': 'eventual'
            }
        }

        path = '/keyspaces/%s' % self.keyspace_name
        r = self.rest.request(method='post', path=path, data=data)

    def use_table(self, table_name, pk_name):
        self.table_name = table_name
        self.pk_name = pk_name.strip('()')

    def create_table(self, table_name=None, schema={}):
        data = {
            'fields': schema,
            'consistencyInfo': {
                'type': 'eventual'
            }
        }

        path = '/keyspaces/%(keyspace_name)s/tables/%(table_name)s/' % {
                   'keyspace_name': self.keyspace_name,
                   'table_name': table_name
               }
        r = self.rest.request(method='post', path=path, data=data)
        self.use_table(table_name, schema['PRIMARY KEY'])

    def check_music_version(self):
        path = '/version'
        r = self.rest.request(method='get',
                              content_type='text/plain', path=path)
        # print "Output from Server .... \n" + r.text

    def create_row(self, values={}):
        data = {
            'values': values,
            'consistencyInfo': {
                'type': 'eventual'
            }
        }

        path = '/keyspaces/%(keyspace_name)s/tables/%(table_name)s/rows' % {
                   'keyspace_name': self.keyspace_name,
                   'table_name': self.table_name
               }
        r = self.rest.request(method='post', path=path, data=data)

    def create_lock(self, lock_name='lock'):
        path = '/locks/create/%s' % lock_name
        r = self.rest.request(method='post',
                              content_type='text/plain', path=path)
        return r.text

    def acquire_lock(self, lock_id):
        path = '/locks/acquire/%s' % lock_id
        r = self.rest.request(method='get',
                              content_type='text/plain', path=path)

        status = (r.text.lower() == 'true')
        # print "Server response .... \n" + r.text

        return status

    def unlock(self, lock_id):
        path = '/locks/release/%s' % lock_id
        r = self.rest.request(method='delete',
                              content_type='text/plain', path=path)

    def __row_url_path(self, pk_value=None):
        path = '/keyspaces/%(keyspace_name)s/tables/%(table_name)s/rows' % {
                   'keyspace_name': self.keyspace_name,
                   'table_name': self.table_name
               }
        if self.pk_name and pk_value:
            path += '?%s=%s' % (self.pk_name, pk_value)
        return path

    def update_row_atomically(self, pk_value='value',
                              values={}):
        # Create lock for the candidate. The Music API dictates that the
        # lock name must be of the form keyspace.table.primary_key
        lock_name = '%(keyspace)s.%(table)s.%(primary_key)s' % {
            'keyspace': self.keyspace_name,
            'table': self.table_name,
            'primary_key': pk_value
        }
        self.lock_names.append(lock_name)
        lock_id = self.create_lock(lock_name)
        # print "Server response .... \n" + lock_id

        time_now = time.time()
        while not self.acquire_lock(lock_id):
            if time.time() - time_now > self.lock_timeout:
                raise IndexError('Lock acquire timeout: %s' % lock_name)
            pass

        # Update entry now that we have the lock.
        data = {
            'values': values,
            'consistencyInfo': {
                'type': 'atomic',
                'lockId': lock_id
            }
        }

        path = self.__row_url_path(pk_value)
        r = self.rest.request(method='put', path=path, data=data)

	# Release lock now that the operation is done.
        self.unlock(lock_id)
        # TODO: Wouldn't we delete the lock at this point?

    def read_row(self, pk_value=None):
        path = self.__row_url_path(pk_value)
        r = self.rest.request(path=path)
        return r.json()

    def read_all_rows(self):
        return self.read_row()

    def drop_key_space(self):
        data = {
            'consistencyInfo': {
                'type': 'eventual'
            }
        }

        path = '/keyspaces/%s' % self.keyspace_name
        r = self.rest.request(method='delete', path=path, data=data)

    def delete_lock(self, lock_name):
        path = '/locks/delete/%s' % lock_name
        r = self.rest.request(content_type='text/plain',
                              method='delete', path=path)
        # print "Server response .... \n" + r.text

    def delete_all_locks(self):
        for lock_name in self.lock_names:
            self.delete_lock(lock_name)

def main():
    app = MusicApp('NewVotingApp')
    print app.keyspace_name

    app.check_music_version()
    app.create_keyspace()

    # Note: Creating a table has the side effect of making it
    # (and the primary key) active for future operations.
    # This is how the example python works. It's not to do with Music.
    schema = {
        'name': 'text',
        'count': 'varint',
        'PRIMARY KEY': '(name)'
    }
    app.create_table('votecount', schema=schema)

    # Create an entry in the voting table for each candidate
    # and with a vote count of 0.
    app.create_row(values={'name': 'Trump', 'count': 0})
    app.create_row(values={'name': 'Bush', 'count': 0})
    app.create_row(values={'name': 'Jeb', 'count': 0})
    app.create_row(values={'name': 'Clinton', 'count': 0})

    # Update each candidate's count atomically.
    app.update_row_atomically('Trump', values={'count': 5})
    app.update_row_atomically('Bush', values={'count': 7})
    app.update_row_atomically('Jeb', values={'count': 8})
    app.update_row_atomically('Clinton', values={'count': 2})

    # Read vote count.
    print app.read_row('Trump')
    print app.read_all_rows()

    # Cleanup.
    # app.drop_key_space(); # Do not use. See Bharath for notes.
    app.delete_all_locks()

if __name__ == "__main__":
    main()
