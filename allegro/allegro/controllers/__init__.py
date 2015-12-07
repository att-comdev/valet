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

from allegro.models import Placement


#
# Placement Helpers
#

def update_placements(plan, resources, placements):
    for key in placements.iterkeys():
        if str(conf.ostro.version) == '1.5':
            uuid = key
            name = resources[key]['name']
        else:
            name = key
            uuid = resources[key]['uuid']
        properties = placements[key]['properties']
        location = properties['availability_zone'].split(':')[1]
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
