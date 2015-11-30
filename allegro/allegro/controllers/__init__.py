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
