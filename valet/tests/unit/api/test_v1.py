'''
Created on Sep 22, 2016

@author: stack
'''

import mock
import pecan
import valet.api.v1.controllers.v1 as v1
from valet.api.v1.controllers.v1 import V1Controller
from valet.tests.unit.api.api_base import ApiBase


class TestV1(ApiBase):

    @mock.patch.object(pecan, 'conf')
    def setUp(self, mock_conf):
        super(TestV1, self).setUp()
#         TestV1.response = None

#         mock_conf.identity.engine = mock.MagicMock

        mock_conf.identity.engine.validate_token.return_value = True
        mock_conf.identity.engine.is_token_admin.return_value = True
        mock_conf.identity.engine.tenant_from_token.return_value = "tenant_id"
        mock_conf.identity.engine.user_from_token.return_value = "user_id"

    @mock.patch.object(v1, 'request')
    def test_check_permissions(self, mock_request):
        mock_request.headers.get.return_value = "auth_token"
        mock_request.path.return_value = "bla bla bla"
        mock_request.json.return_value = {"action": "create"}
        mock_request.context = {}

        self.validate_test(V1Controller.check_permissions() is True)

    @mock.patch.object(v1, 'error', ApiBase.mock_error)
    @mock.patch.object(v1, 'request')
    def test_check_permissions_auth_unhappy(self, mock_request):
        mock_request.headers.get.return_value = None
        mock_request.path.return_value = "bla bla bla"
        mock_request.json.return_value = {"action": "create"}
        mock_request.context = {}

        V1Controller.check_permissions()
        self.validate_test("Unauthorized - No auth token" in TestV1.response)

    @mock.patch.object(v1, 'error', ApiBase.mock_error)
    @mock.patch.object(v1, 'request')
    def test_check_permissions_admin_unhappy(self, mock_request):
        mock_request.headers.get.return_value = "auth_token"
        mock_request.path.return_value = "bla bla group bla"
        mock_request.json.return_value = {"action": "create"}
        mock_request.context = {}
        print("path is: %s" % mock_request.path.return_value)

        x = V1Controller.check_permissions()
        print(x)
#         self.validate_test("Unauthorized - Permission was not granted" in TestV1.response)
