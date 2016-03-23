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
    for key in placements.iterkeys():
        uuid = key
        name = resources[key]['name']
        properties = placements[key]['properties']
        location = properties['host']
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
