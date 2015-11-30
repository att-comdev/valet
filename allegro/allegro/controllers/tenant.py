from pecan import expose
from pecan import request
        
from allegro.controllers import plans, placements
    
import logging

logger = logging.getLogger(__name__)
    
        
class TenantController(object):
    plans = plans.PlansController()
    placements = placements.PlacementsController()

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        # TODO: Tie to Keystone
        assert self.tenant_id

    @expose(generic=True, template='json')
    def index(self):
        ver = {
          "versions": [
            {
              "status": "CURRENT",
              "id": "v1.0",
              "links": [
                {
                  "href": request.application_url + "/v1/{tenant_id}/plans/",
                  "rel": "self"
                },
                {
                  "href": request.application_url + "/v1/{tenant_id}/placements/",
                  "rel": "self"
                }
              ]
            }
          ]
        }

        return ver
