
# import webob
from groups import GroupsController
import mock
import pecan
from pecan import core
from valet.api.db.models.music import Query
import valet.api.v1.controllers.groups as groups
from valet.tests.base import Base


class TestGroups(Base):

    def setUp(self):
        super(TestGroups, self).setUp()
        self.groups_controller = GroupsController()
        self.response = None
        core.state = mock.MagicMock()
        pecan.conf.music = mock.MagicMock()

    def test_allow(self):
        self.validate_test(self.groups_controller.allow() == 'GET,POST')

    def mock_error(url, msg=None, **kwargs):
        TestGroups.response = msg

    @mock.patch.object(groups, 'error', mock_error)
    @mock.patch.object(groups, 'request')
    def test_index(self, mock_request):
        mock_request.method = "HEAD"
        self.groups_controller.index()
        self.validate_test("The HEAD method is not allowed" in TestGroups.response)

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
