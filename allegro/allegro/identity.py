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
from datetime import datetime
import iso8601
import json
import pytz
import time

from keystoneclient.v2_0 import client
from keystoneclient.exceptions import AuthorizationFailure, Unauthorized

 
def utcnow():
    return datetime.now(tz=pytz.utc)
 
class Keystone(object):
    AUTH_URL = 'auth_url'
    PASSWORD = 'password'
    USERNAME = 'username'
    TENANT_NAME = 'tenant_name'

    def __init__(self, **kwargs):
        self.auth_url = kwargs.get('auth_url', 'http://mtmac1:5000/v2.0')
        self.password = kwargs.get('password', 'password')
        self.username = kwargs.get('username', 'allegro')
        self.tenant_name = kwargs.get('tenant_name', 'service')
        self._client = None

    @property
    def client(self):
        # TODO: Or if token is expired.
        if not self._client:
            kwargs = {
                'auth_url': self.auth_url,
                'username': self.username,
                'password': self.password,
                'tenant_name': self.tenant_name,
            }
            self._client = client.Client(**kwargs)
        return self._client

    @property
    def expired(self):
        timestamp = self._client.auth_ref['token']['expires']
        return iso8601.parse_date(timestamp) <= utcnow()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Please provide a Keystone token. Example syntax:")
        print("keystone token-get 2>/dev/null | grep ' id ' | awk '{print $4}'")
        exit(1)

    kwargs = {}
    keystone = Keystone(**kwargs)
    client = keystone.client

    auth_token = sys.argv[1]
    tenant_id = 'e833dea42c7c47d6be25150693fe0f40'

    print('Client Auth Token: %s' % client.auth_token)
    print('User Auth Token: %s' % auth_token)
    print

    while True:
        if keystone.expired:
            print "Client expired!"
            exit(1)

        try:
            auth_result = client.tokens.authenticate(token=auth_token,
                                                     tenant_id=tenant_id)
            if auth_result:
                #print json.dumps(auth_result.to_dict())
                print('The user auth token is valid')
                print('Token expiration: %s' % (auth_result.expires))

                timenow = utcnow().isoformat()
                print('Time now: %s' % (timenow))
        except:
            print('The user auth token is invalid or has expired.')
            exit(1)

        print('Sleeping for 60 seconds.')
        time.sleep(60)
        print
