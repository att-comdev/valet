#!/usr/bin/env python
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

from tempest.lib.common.utils import data_utils
from tempest.lib.services.identity.v2 import tenants_client
from tempest import test
from valet.tests.tempest.api import base


class ValetGroupsMembersTest(base.BaseValetTest):

    @classmethod
    def setup_clients(cls):
        super(ValetGroupsMembersTest, cls).setup_clients()
        cls.client = cls.valet_client
        cls.TenantsClient = cls.os.tenants_public_client
        cls.UsersClient = cls.os.users_v3_client
        cls.RolesClient = cls.os.roles_v3_client

    def _create_group(self):
        group_name = data_utils.rand_name('membergroup')
        resp = self.client.create_group(name=group_name,
                                        group_type='exclusivity',
                                        description='Test Member Group')
        group_id = resp['id']
        self.addCleanup(self._delete_group, group_id)
        return group_id

    def _delete_group(self, group_id):
        self.client.delete_all_members(group_id)
        self.client.delete_group(group_id)

    def _create_tenant(self):
        self.TenantsClient.endpoint_type = 'adminURL'
        _tenant = tenants_client.TenantsClient(
            self.TenantsClient.auth_provider,
            self.TenantsClient.service,
            self.TenantsClient.region,
            self.TenantsClient.endpoint_type)
        tenant_name = data_utils.rand_name(name='tenant')
        tenant_desc = data_utils.rand_name(name='desc')
        body = _tenant.create_tenant(name=tenant_name, description=tenant_desc)
        tenant_id = body['tenant']['id']
        self.addCleanup(_tenant.delete_tenant, tenant_id)
        return tenant_id

    def _create_member(self, tenant_id):
        username = data_utils.rand_name(name='member')
        email = username + '@test.valet'
        password = data_utils.rand_password()
        body = self.UsersClient.create_user(user_name=username,
                                            password=password,
                                            project_id=tenant_id,
                                            email=email)
        member_id = body['user']['id']
        self.addCleanup(self.UsersClient.delete_user, member_id)
        return member_id

    def _get_admin_member_roles_id(self):
        admin_member_roles_id = {}
        # Retrieve the admin role ID
        body = self.RolesClient.list_roles()
        for roles in body['roles']:
            if roles['name'] == 'admin':
                admin_member_roles_id['admin'] = roles['id']
        # Retrieve the admin user ID
        body = self.UsersClient.list_users()
        for users in body['users']:
            if users['name'] == 'admin':
                admin_member_roles_id['admin_id'] = users['id']
        return admin_member_roles_id

    @test.idempotent_id('5aeec320-65d5-11e6-8b77-86f30ca893d3')
    def test_add_single_member_to_a_group(self):
        # Create a tenant
        tenants = []
        tenant_id = self._create_tenant()
        tenants.append(tenant_id)
        # Create a member
        member_id = self._create_member(tenant_id)
        # Get the Instance Specific admin role id
        admin_member_roles = self._get_admin_member_roles_id()
        # Assign the user with role admin to the newly
        # created tenant
        self.RolesClient.assign_user_role_on_project(
            tenant_id,
            member_id,
            admin_member_roles['admin'])
        # Create a group
        group_id = self._create_group()
        # Add the newly created tenant to the group
        resp = self.client.add_members(group_id, tenants)
        # Retrieve the relevant response information
        members = resp['members']
        groupid = resp['id']
        self.assertEqual(members[0], tenants[0])
        self.assertEqual(group_id, groupid)
        self.assertIn('description', resp)
        self.assertIn('type', resp)
        self.assertIn('name', resp)

    @test.idempotent_id('5aeec6f4-65d5-11e6-8b77-86f30ca893d3')
    def test_add_multiple_members_to_a_group(self):
        # Get the Instance Specific admin role id
        admin_member_roles = self._get_admin_member_roles_id()
        # Create multiple tenants
        tenants = []
        for count in range(0, 4):
            tenant_id = self._create_tenant()
            tenants.append(tenant_id)
            # Create a member
            member_id = self._create_member(tenant_id)
            # Assign the user with role admin to the newly
            # created tenant
            self.RolesClient.assign_user_role_on_project(
                tenant_id,
                member_id,
                admin_member_roles['admin'])
        # Create a group
        group_id = self._create_group()
        # Add the newly created tenant to the group
        resp = self.client.add_members(group_id, tenants)
        # Retrieve the relevant response information
        groupid = resp['id']
        members = resp['members']
        self.assertItemsEqual(members, tenants)
        self.assertEqual(group_id, groupid)
        self.assertIn('description', resp)
        self.assertIn('type', resp)
        self.assertIn('name', resp)
        self.assertIn('members', resp)

    @test.idempotent_id('5aeec8b6-65d5-11e6-8b77-86f30ca893d3')
    def test_add_single_member_to_a_group_and_verify_membership(self):
        # Create a tenant
        tenants = []
        tenant_id = self._create_tenant()
        tenants.append(tenant_id)
        # Create a member
        member_id = self._create_member(tenant_id)
        # Get the Instance Specific admin role id
        admin_member_roles = self._get_admin_member_roles_id()
        # Assign the user with role admin to the newly
        # created tenant
        self.RolesClient.assign_user_role_on_project(
            tenant_id,
            member_id,
            admin_member_roles['admin'])
        # Create a group
        group_id = self._create_group()
        # Add the newly created tenant to the group
        self.client.add_members(group_id, tenants)
        # Verify membership
        resp = self.client.verify_membership(group_id, tenant_id)
        status = int(resp.response['status'])
        self.assertEqual(204, status)

    @test.idempotent_id('5aeec99c-65d5-11e6-8b77-86f30ca893d3')
    def test_delete_member_from_group(self):
        # Get the Instance Specific admin role id
        admin_member_roles = self._get_admin_member_roles_id()
        # Create multiple tenants
        tenants = []
        for count in range(0, 4):
            tenant_id = self._create_tenant()
            tenants.append(tenant_id)
            # Create a member
            member_id = self._create_member(tenant_id)
            # Assign the user with role admin to the newly
            # created tenant
            self.RolesClient.assign_user_role_on_project(
                tenant_id,
                member_id,
                admin_member_roles['admin'])
        # Create a group
        group_id = self._create_group()
        # Add the newly created tenant to the group
        resp = self.client.add_members(group_id, tenants)
        groupid = resp['id']
        resp = self.client.delete_member(groupid, tenants[2])
        status = int(resp.response['status'])
        self.assertEqual(204, status)

    @test.idempotent_id('5aeecb68-65d5-11e6-8b77-86f30ca893d3')
    def test_delete_all_members_from_group(self):
        # Get the Instance Specific admin role id
        admin_member_roles = self._get_admin_member_roles_id()
        # Create multiple tenants
        tenants = []
        for count in range(0, 4):
            tenant_id = self._create_tenant()
            tenants.append(tenant_id)
            # Create a member
            member_id = self._create_member(tenant_id)
            # Assign the user with role admin to the newly
            # created tenant
            self.RolesClient.assign_user_role_on_project(
                tenant_id,
                member_id,
                admin_member_roles['admin'])
        # Create a group
        group_id = self._create_group()
        # Add the newly created tenant to the group
        resp = self.client.add_members(group_id, tenants)
        groupid = resp['id']
        resp = self.client.delete_all_members(groupid)
        status = int(resp.response['status'])
        self.assertEqual(204, status)
