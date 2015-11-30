#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

'''
Planner.py (stub)

Author: Joe D'Andrea
Created: 11 July 2014
Contact: jdandrea@research.att.com
'''

import simplejson as json

from heat.common.i18n import _
    
# As a stub, we blindy set the AZ for all supported resources
SUPPORTED_RESOURCE_TYPES = [
    'OS::Nova::Server',
    'OS::Cinder::Volume',
    'OS::Trove::Instance',
]

VERSION = '0.1'

def _finish(result, status='Unknown', message=None):
    result['status'] = {'type': status, 'message': message}
    return json.dumps(result, sort_keys=True, indent=2 * ' ')
    
def _success(result, message='Yay!'):
    return _finish(result, 'success', message)
    
def _error(result, message='Unknown Error'):
    return _finish(result, 'error', message)

def do(job, az='nova'):
    result = {'version': '0.1'}
    try:
        payload = json.loads(job)

        f = open('/tmp/planner-dump.txt', 'w')
        print >>f, json.dumps(payload, sort_keys=True, indent=2 * ' ')
        f.close()
    except:
        return _error(result, 'Payload must be valid JSON')

    if 'version' not in payload or payload['version'] != VERSION:
        return _error(result, 'Payload version not set. Must be set to ' + VERSION)
        
    if 'resources' in payload:
        resource_mods = {}
        for k,v in payload['resources'].iteritems():
            if 'Type' in v and v['Type'] in SUPPORTED_RESOURCE_TYPES:
                resource_mods[k] = {
                    'properties': {
                        'availability_zone': az,
                    },
                }
        result['resources'] = resource_mods
        return _success(result, 'Yay!')
    else:
        return _error(result, 'No resources in payload')
