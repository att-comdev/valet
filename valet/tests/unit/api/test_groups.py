
import mock
import pecan
from pecan import core
from valet.api.db.models.music.groups import Group
from valet.api.db.models.music import Query
import valet.api.v1.controllers.groups as groups
from valet.api.v1.controllers.groups import GroupsController, MembersController
from valet.tests.base import Base


class TestGroups(Base):
    ''' Unit tests for valet.api.v1.controllers.groups '''

    def setUp(self):
        super(TestGroups, self).setUp()
        self.tenant_id = "testprojectid"

        # Testing class GroupsController
        self.groups_controller = GroupsController()

        # Testing class MembersController
        self.members_controller = MembersController()

        self.response = None
        core.state = mock.MagicMock()
        pecan.conf.music = mock.MagicMock()

    def mock_error(url, msg=None, **kwargs):
        TestGroups.response = msg

    def mock_empty(url, msg=None, **kwargs):
        pass

    def test_allow(self):
        self.validate_test(self.groups_controller.allow() == 'GET,POST')

        self.validate_test(self.members_controller.allow() == 'PUT,DELETE')

    @mock.patch.object(groups, 'error', mock_error)
    @mock.patch.object(groups, 'request')
    def test_index(self, mock_request):
        mock_request.method = "HEAD"
        self.groups_controller.index()
        self.validate_test("The HEAD method is not allowed" in TestGroups.response)

        mock_request.method = "GET"
        self.members_controller.index()
        self.validate_test("The GET method is not allowed" in TestGroups.response)

    @mock.patch.object(groups, 'request')
    def index_put(self, mock_request):
        pecan.conf.identity = mock.MagicMock()
        pecan.conf.identity.engine.is_tenant_list_valid.return_value = True

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        r = self.members_controller.index_put(members=[self.tenant_id])

        self.validate_test(groups.response.status == 201)
        self.validate_test(r.members[0] == self.tenant_id)

        return r

    @mock.patch.object(groups, 'error', mock_error)
    @mock.patch.object(groups, 'request')
    def test_index_put_unhappy(self, mock_request):
        pecan.conf.identity = mock.MagicMock()
        pecan.conf.identity.engine.is_tenant_list_valid.return_value = False

        mock_request.context = {'group': Group("test_name", "test_description", "test_type", None)}
        self.members_controller.index_put(members=[self.tenant_id])

        self.validate_test("Member list contains invalid tenant IDs" in TestGroups.response)

    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_put_delete(self, mock_request, mock_func):
        grp_with_member = self.index_put()

        mock_request.context = {'group': grp_with_member}
        mock_func.return_value = None
        self.members_controller.index_delete()

        self.validate_test(groups.response.status == 204)
        self.validate_test(grp_with_member.members == [])

    @mock.patch.object(groups, 'error', mock_error)
    @mock.patch.object(groups, 'tenant_servers_in_group')
    @mock.patch.object(groups, 'request')
    def test_index_delete_unhappy(self, mock_request, mock_func):
        grp_with_member = self.index_put()

        mock_request.context = {'group': grp_with_member}
        mock_func.return_value = "Servers"
        self.members_controller.index_delete()

        self.validate_test("has servers in group" in TestGroups.response)

    @mock.patch.object(Query, 'all')
    def test_index_get(self, mock_request):
        all_groups = ["group1", "group2", "group3"]
        mock_request.return_value = all_groups
        response = self.groups_controller.index_get()

        self.validate_test(len(response) == 1)
        self.validate_test(len(response["groups"]) == len(all_groups))
        self.validate_test(all_groups == response["groups"])

    def test_index_post(self):
        group = self.groups_controller.index_post(name="testgroup", description="test description", type="testtype")

        self.validate_test(groups.response.status == 201)
        self.validate_test(group.name == "testgroup")

    @mock.patch.object(groups, 'error', mock_error)
    def test_index_post_unhappy(self):
        pecan.conf.music = None
        self.groups_controller.index_post(name="testgroup", description="test description", type="testtype")

        self.validate_test("Unable to create Group" in TestGroups.response)
