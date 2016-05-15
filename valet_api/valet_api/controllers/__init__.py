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
import string

from valet_api.models import Placement

from pecan import redirect, request


#
# Group Helpers
#

def group_name_type(value):
    '''Validator for group name type.'''
    assert set(value) <= set(string.letters + string.digits + "-._~"), \
        "must contain only uppercase and lowercase letters, " \
        "decimal digits, hyphens, periods, underscores, and tildes " \
        "[RFC 3986, Section 2.3]"


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
            location=location)
    return plan


def update_placements(placements, reserve_id=None):
    '''Update placements. Optionally reserve one placement.'''
    for uuid in placements.iterkeys():
        placement = Placement.query.filter_by(  # pylint: disable=E1101
            orchestration_id=uuid).first()
        if placement:
            properties = placements[uuid]['properties']
            location = properties['host']
            placement.location = location
            if reserve_id and placement.orchestration_id == reserve_id:
                placement.reserved = True
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
