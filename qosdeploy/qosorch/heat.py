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

# http://docs.openstack.org/developer/python-heatclient/ref/v1/index.html
# http://developer.openstack.org/api-ref-orchestration-v1.html

import os

from keystoneclient.v2_0 import client as ksclient
from heatclient import client as htclient
from heatclient.common import utils

class Heat(object):
    ''' OpenStack Heat convenience class. '''

    def __init__(self):
        ''' Initialization. '''
        self.client = self._client()

    def _client(self):
        ''' Instantiates a Heat Client object '''

        # Get a keystone client
        keystone = ksclient.Client(
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            tenant_name=os.environ['OS_TENANT_NAME'],
            auth_url=os.environ['OS_AUTH_URL'],
        )

        # Get a heat client
        auth_token = keystone.auth_token
        heat_endpoint = keystone.service_catalog.url_for(
            service_type='orchestration',
            endpoint_type='publicURL',
        )
        return htclient.Client('1', endpoint=heat_endpoint, token=auth_token)

# TODO: If Heat (Icehouse) works without this, we can remove it for good.
#
#    def list_stacks(self):
#        ''' List available stacks. '''
#        stacks = self.client.stacks.list()
#        fields = ['id', 'stack_name', 'stack_status', 'creation_time']
#        utils.print_list(stacks, fields, sortby=3)

    def load_template(self, template_file):
        ''' Load a Heat template from a file. '''
        stream = open(template_file)
        template = utils.yaml.load(stream)
        stream.close()
        return template
