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
from os import path
from pecan import conf
from pecan import request, redirect

# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Placement
#from allegro.models.sqlalchemy import Placement


#
# Placement Helpers
#

def update_placements(plan, resources, placements):
    if str(conf.ostro.version) == '2.0':
        # Status message has changed from "done" to "success"
        # Version key has been removed
        # resource properties use "host" instead of "availability_zone"
        # host value reverted to host name only (Cinder results removed)
        location_key = 'host'
    else:
        location_key = 'availability_zone'

    for key in placements.iterkeys():
        if str(conf.ostro.version) == '2.0' or \
           str(conf.ostro.version) == '1.5':
            uuid = key
            name = resources[key]['name']
        else:
            name = key
            uuid = resources[key]['uuid']
        properties = placements[key]['properties']
        location = properties[location_key].split(':')[1]
        placement = Placement(
            name, uuid,
            plan=plan,
            location=location
        )
    return plan

#
# Error Helpers
#

def error(url, msg=None):
    if msg:
        request.context['error_message'] = msg
    url = path.join(url, '?error_message=%s' % msg)
    redirect(url, internal=True)
