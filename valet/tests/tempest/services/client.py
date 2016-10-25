#!/usr/bin/env python
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

import json

from tempest_lib.common import rest_client


class ValetClient(rest_client.RestClient):

    """Tempest REST client for Valet.

    Implements create, delete, update, list and show groups for Valet.
    """

    def _resp_helper(self, resp, body=None):
        if body:
            body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_groups(self):
        resp, body = self.get('/groups')
        self.expected_success(200, resp.status)
        return self._resp_helper(resp, body)

    def create_group(self, name, group_type, description):
        params = {
            "name": name,
            "type": group_type,
            "description": description,
        }
        req_body = json.dumps(params)
        resp, body = self.post('/groups', req_body)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def delete_group(self, group_id):
        resp, body = self.delete('/groups/%s' % str(group_id))
        self.expected_success(204, resp.status)
        return self._resp_helper(resp, body)

    def update_group(self, group_id, description):
        params = {
            'description': description
        }
        req_body = json.dumps(params)
        resp, body = self.put('/groups/%s' % group_id, req_body)
        self.expected_success(201, resp.status)
        return self._resp_helper(resp, body)

    def show_group(self, group_id):
        resp, body = self.get('/groups/%s' % group_id)
        self.expected_success(200, resp.status)
        return self._resp_helper(resp, body)
