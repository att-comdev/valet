'''
Created on Sep 19, 2016

@author: stack
'''

import mock
import valet.api.v1.controllers.placements as placements
from valet.api.v1.controllers.placements import PlacementsController, PlacementsItemController
from valet.tests.base import Base
from valet.api.db.models.music import Query, Results
from valet.api.db.models import Placement, Plan


def mock_error(url, msg=None, **kwargs):
    TestPlacements.response = msg


class TestPlacements(Base):
    '''Unit tests for valet.api.v1.controllers.placements '''

    def setUp(self):
        super(TestPlacements, self).setUp()

        self.placements_controller = PlacementsController()
        self.placements_item_controller = self.init_PlacementsItemController()
        TestPlacements.response = None

    @mock.patch.object(placements, 'error', mock_error)
    @mock.patch.object(Query, 'filter_by')
    @mock.patch.object(placements, 'request')
    def init_PlacementsItemController(self, mock_request, mock_filter):
        mock_request.context = {}
        mock_filter.return_value = Results(["", "second"])
        try:
            PlacementsItemController("uuid4")
        except Exception as e:
            self.validate_test("'str' object has no attribute 'id'" in e)
        self.validate_test("Placement not found" in TestPlacements.response)

        mock_filter.return_value = Results([
            Placement("test_name", "test_orchestration_id", plan=Plan("plan_name", "stack_id", _insert=False), location="test_location", _insert=False)])

        return PlacementsItemController("uuid4")

    def test_allow(self):
        self.validate_test(self.placements_controller.allow() == 'GET')

        self.validate_test(self.placements_item_controller.allow() == 'GET,POST,DELETE')

    @mock.patch.object(placements, 'error', mock_error)
    @mock.patch.object(placements, 'request')
    def test_index(self, mock_request):
        mock_request.method = "POST"
        self.placements_controller.index()
        self.validate_test("The POST method is not allowed" in TestPlacements.response)

        mock_request.method = "PUT"
        self.placements_item_controller.index()
        self.validate_test("The PUT method is not allowed" in TestPlacements.response)

    def test_index_options(self):
        self.placements_controller.index_options()
        self.validate_test(placements.response.status == 204)

        self.placements_item_controller.index_options()
        self.validate_test(placements.response.status == 204)

    @mock.patch.object(Query, 'all')
    def test_index_get(self, mock_all):
        all_groups = ["group1", "group2", "group3"]
        mock_all.return_value = all_groups
        response = self.placements_controller.index_get()

        self.validate_test(len(response) == 1)
        self.validate_test(len(response["placements"]) == len(all_groups))
        self.validate_test(all_groups == response["placements"])

        response = self.placements_item_controller.index_get()

        self.validate_test("test_name" in response['placement'].name)
        self.validate_test("test_orchestration_id" in response['placement'].orchestration_id)
        self.validate_test("plan_name" in response['placement'].plan.name)
        self.validate_test("stack_id" in response['placement'].plan.stack_id)

    @mock.patch.object(placements, 'error', mock_error)
    @mock.patch.object(Query, 'filter_by', mock.MagicMock)
    @mock.patch.object(placements, 'update_placements')
    def test_index_post(self, mock_plcment):
        kwargs = {'resource_id': "resource_id", 'locations': ["test_location"]}
        self.placements_item_controller.index_post(**kwargs)
        self.validate_test(placements.response.status == 201)

        with mock.patch('valet.api.v1.controllers.placements.Ostro') as mock_ostro:
            kwargs = {'resource_id': "resource_id", 'locations': [""]}
            self.placements_item_controller.index_post(**kwargs)
            self.validate_test("Ostro error:" in TestPlacements.response)

            mock_plcment.return_value = None

            status_type = mock.MagicMock()
            status_type.response = {"status": {"type": "ok"}, "resources": {"iterkeys": []}}
            mock_ostro.return_value = status_type

            self.placements_item_controller.index_post(**kwargs)
            self.validate_test(placements.response.status == 201)

    def test_index_delete(self):
        self.placements_item_controller.index_delete()
        self.validate_test(placements.response.status == 204)