'''
OpenStack Heat convenience class
'''

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
