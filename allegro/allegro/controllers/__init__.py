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

'''Controllers Package'''

from os import path

# TODO: Make this a driver plugin point instead so we can pick and choose.
from allegro.models.music import Placement
#from allegro.models.sqlalchemy import Placement

from pecan import conf, expose, redirect, request, response


#
# Placement Helpers
#

def set_placements(plan, resources, placements):
    '''Set placements'''
    for uuid in placements.iterkeys():
        name = resources[uuid]['name']
        properties = placements[uuid]['properties']
        location = properties['host']
        _unused = Placement(  # pylint: disable=W0612
            name, uuid,
            plan=plan,
            location=location
        )
    return plan

def update_placements(placements):
    '''Update placements'''
    for uuid in placements.iterkeys():
        placement = Placement.query.filter_by(  # pylint: disable=E1101
            orchestration_id=uuid).first()
        if placement:
            properties = placements[uuid]['properties']
            location = properties['host']
            placement.location = location
            placement.update()
    return

#
# Error Helpers
#

def error(url, msg=None, **kwargs):
    '''Error handler'''
    if msg:
        request.context['error_message'] = msg
    if kwargs:
        request.context['kwargs'] = kwargs
    url = path.join(url, '?error_message=%s' % msg)
    redirect(url, internal=True)
