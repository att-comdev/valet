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

"""Test Identity."""

import mock
from valet.api.common.identity import Identity
from valet.tests.unit.api.v1.api_base import ApiBase


class TestIdentity(ApiBase):
    """Test Identity Class."""

    def setUp(self):
        """Setup Test Identity."""
        super(TestIdentity, self).setUp()

        kwargs = {'username': 'admin',
                  'tenant_name': 'demo',
                  'password': 'qwer4321',
                  'auth_url': 'http://controller:5000/v2.0'}

        self.identity = Identity(**kwargs)

    def test_is_token_admin(self):
        """Test if passed in token is an Admin."""
        self.validate_test(self.identity.is_token_admin(TokenT))
        self.validate_test(not self.identity.is_token_admin(TokenF))

    def test_tenant_from_token(self):
        """Test tenant from ID in Token."""
        self.validate_test(
            self.identity.tenant_from_token(TokenT) ==
            "cb9c9997fc6e41cc87186de92aa0a099")

    def test_user_from_token(self):
        """Test identity from user ID from token."""
        self.validate_test(
            self.identity.user_from_token(TokenT) ==
            "cb9c9997fc6e41cc87186de92aa0a099")

    def test_client(self):
        """Test Client."""
        with mock.patch('valet.api.common.identity.client'):
            self.identity.client()

    def test_validate_token(self):
        """Validate identity auth token."""
        self.validate_test(self.identity.validate_token("auth_token") is None)

        with mock.patch('valet.api.common.identity.client'):
            self.validate_test(
                self.identity.validate_token("auth_token") is not None)

    def test_is_tenant_list_validself(self):
        """Test to see if tenant list is valid."""
        with mock.patch('valet.api.common.identity.client'):
            self.validate_test(
                self.identity.is_tenant_list_valid(["a", "b"]) is False)


class TokenT(object):
    """Token for User and Tenant with user roles filled."""

    user = {'roles': [{'name': 'user'},
                      {'name': 'heat_stack_owner'},
                      {'name': 'admin'}],
            'id': 'cb9c9997fc6e41cc87186de92aa0a099'}
    tenant = {'description': 'Demo Project',
              'enabled': True,
              'id': 'cb9c9997fc6e41cc87186de92aa0a099'}


class TokenF(object):
    """Token for User and Tenant with empty user role list."""

    user = {'roles': []}
    tenant = {'description': 'Demo Project',
              'enabled': True,
              'id': 'cb9c9997fc6e41cc87186de92aa0a099'}
