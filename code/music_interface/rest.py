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

'''Voting App Example for Music.'''

import json

import requests


class REST(object):
    '''Helper class for REST operations.'''

    host = None
    port = None
    path = None

    def __init__(self, host='localhost', port=8080, path='/'):
        '''Initializer. Accepts target host, port, and path.'''

        self.host = host  # IP or FQDN
        self.port = port  # Port Number
        self.path = path  # Path starting with /

    @property
    def __url(self):
        '''Returns a URL using the host/port/path.'''

        # Must end without a slash
        return 'http://%(host)s:%(port)s%(path)s' % {
                'host': self.host,
                'port': self.port,
                'path': self.path
            }

    @staticmethod
    def __headers(content_type='application/json'):
        '''Returns HTTP request headers.'''
        headers = {
            'accept': content_type,
            'content-type': content_type
        }
        return headers

    def request(self, method='get', content_type='application/json',
                path='/', data=None):
        '''Performs HTTP request.'''
        if method not in ('post', 'get', 'put', 'delete'):
            raise KeyError("Method must be one of post, get, put, or delete.")
        method_fn = getattr(requests, method)

        url = self.__url + path
        response = method_fn(url, data=json.dumps(data),
                             headers=self.__headers(content_type))
        response.raise_for_status()
        return response


