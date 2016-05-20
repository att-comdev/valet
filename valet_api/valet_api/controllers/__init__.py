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

import logging
from os import path
import string

from valet_api.common.i18n import _
from valet_api.models import Placement

from pecan import redirect, request

LOG = logging.getLogger(__name__)

#
# Group Helpers
#

def group_name_type(value):
    '''Validator for group name type.'''
    assert set(value) <= set(string.letters + string.digits + "-._~"), \
        _("must contain only uppercase and lowercase letters, " \
        "decimal digits, hyphens, periods, underscores, and tildes " \
        "[RFC 3986, Section 2.3]")


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


def reserve_placement(placement, reserve=True):
    '''Reserve placement (set reserve=False to unreserve)'''
    if placement:
        LOG.info(_('%(rsrv)s placement of %(orch_id)s in %(loc)s.'),
                 {'rsrv': _("Reserving") if reserve else _("Unreserving"),
                  'orch_id': placement.orchestration_id,
                  'loc': placement.location})
        placement.reserved = reserve
        placement.update()

def update_placements(placements, reserve_id=None, unlock_all=False):
    '''Update placements. Optionally reserve one placement.'''
    for uuid in placements.iterkeys():
        placement = Placement.query.filter_by(  # pylint: disable=E1101
            orchestration_id=uuid).first()
        if placement:
            properties = placements[uuid]['properties']
            location = properties['host']
            if placement.location != location:
                LOG.info(_('Changing placement of %(orch_id)s ' \
                           'from %(old_loc)s to %(new_loc)s.'),
                         {'orch_id': placement.orchestration_id,
                          'old_loc': placement.location,
                          'new_loc': location})
                placement.location = location
            if unlock_all:
                reserve_placement(placement, False)
            elif reserve_id and placement.orchestration_id == reserve_id:
                reserve_placement(placement)
            else:
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
