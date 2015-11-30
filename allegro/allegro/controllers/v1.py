from pecan import expose
from pecan import request
        
from allegro.controllers import errors
from allegro.controllers import tenant
    
import logging

logger = logging.getLogger(__name__)
    
        
class V1Controller(object):
    errors = errors.ErrorsController()

    @expose(generic=True, template='json')
    def index(self):
        ver = {
          "versions": [
            {
              "status": "CURRENT",
              "id": "v1.0",
              "links": [
                {
                  "href": request.application_url + "/v1/{tenant_id}/",
                  "rel": "self"
                }
              ]
            }
          ]
        }

        return ver

    @expose()
    def _lookup(self, tenant_id, *remainder):
        return tenant.TenantController(tenant_id), remainder
