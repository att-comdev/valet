#
# Copyright 2014-2017 AT&T Intellectual Property
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test Root."""

import mock
import valet.api.v1.controllers.root as root
from valet.api.v1.controllers.root import RootController
from valet.tests.unit.api.v1.api_base import ApiBase


class TestRoot(ApiBase):
    """Unit tests for valet.api.v1.controllers.root."""

    def setUp(self):
        """Setup Test Root Class and set RootController."""
        super(TestRoot, self).setUp()

        self.root_controller = RootController()

    def test_allow(self):
        """Test root_controller allow method with GET."""
        self.validate_test(self.root_controller.allow() == 'GET')

    @mock.patch.object(root, 'error', ApiBase.mock_error)
    @mock.patch.object(root, 'request')
    def test_index(self, mock_request):
        """Test root_controller index method with incorrect (PUT) method."""
        mock_request.method = "PUT"
        self.root_controller.index()
        self.validate_test("The PUT method is not allowed" in ApiBase.response)

    def test_index_options(self):
        """Test root_controller index_options method."""
        self.root_controller.index_options()
        self.validate_test(root.response.status == 204)

    @mock.patch.object(root, 'request')
    def test_index_get(self, mock_request):
        """Test root_controller index_get method."""
        mock_request.application_url.return_value = "application_url"
        response = self.root_controller.index_get()

        self.validate_test(response['versions'][0])
        self.validate_test(response['versions'][0]['links'])
