from pecan import conf
from pecan import expose
from pecan import request
from webob.exc import status_map

from allegro.controllers import v1
from allegro.controllers.errors import error_wrapper

import logging

logger = logging.getLogger(__name__)


class RootController(object):
    v1 = v1.V1Controller()

    def __init__(self):
        return

    @expose(generic=True, template='json')
    def index(self):
        ver = {
          "versions": [
            {
              "status": "CURRENT",
              "id": "v1.0",
              "links": [
                {
                  "href": request.application_url + "/v1/",
                  "rel": "self"
                }
              ]
            }
          ]
        }

        return ver

    @expose('error.html')
    @error_wrapper
    def error(self, status):
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)
