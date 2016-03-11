from uuid import uuid4

# TODO: Make this a driver plugin point instead so we can pick and choose.
#from allegro.models.music import Plan, Placement
from allegro.models.sqlalchemy import Plan, Placement
from allegro.tests.controllers import is_valid_uuid4

TENANT_ID = 'e833dea42c7c47d6be25150693fe0f40'
STACK_ID = 'e624474b-fc80-4053-ab5f-45cc1030e692'
PLAN_NAME = 'foobar'


class TestPlansController(object):
    def test_get_index_no_plans(self, session):
        result = session.app.get('/v1/%s/plans/' % TENANT_ID)
        assert result.status_int == 200
        assert result.json == []

    def test_get_index_a_plan(self, session):
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/%s/plans/' % TENANT_ID).json
        assert result == [PLAN_NAME]

    def test_single_plan_should_have_one_item(self, session):
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/%s/plans/' % TENANT_ID)
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_list_a_few_plans(self, session):
        for plan_number in range(20):
            stack_id = str(uuid4())
            Plan('foo_%s' % plan_number, stack_id)
        session.commit()

        result = session.app.get('/v1/%s/plans/' % TENANT_ID)
        json = result.json
        assert result.status_int == 200
        assert len(json) == 20

class TestPlansItemController(object):
    def test_get_index_single_plan(self, session):
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/%s/plans/%s/' % (TENANT_ID, STACK_ID))
        assert result.status_int == 200

    def test_get_index_no_plan(self, session):
        result = session.app.get('/v1/%s/plans/%s/' % (TENANT_ID, STACK_ID),
                                 expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_plan_data(self, session):
        Plan(PLAN_NAME, STACK_ID)
        session.commit()
        result = session.app.get('/v1/%s/plans/%s/' % (TENANT_ID, STACK_ID))
        json = result.json
        assert is_valid_uuid4(json['id'])
        assert json['name'] == PLAN_NAME
        assert json['placements'] == {}
        assert json['stack_id'] == STACK_ID

    def test_get_plan_refs(self, session):
        plan = Plan(PLAN_NAME, STACK_ID)
        Placement(
            'placement_1', str(uuid4()),
            plan=plan,
            location='foo_1'
        )
        Placement(
            'placement_2', str(uuid4()),
            plan=plan,
            location='foo_2'
        )
        session.commit()
        result = session.app.get('/v1/%s/plans/%s/' % (TENANT_ID, STACK_ID))
        json = result.json
        assert is_valid_uuid4(json['id'])
        assert json['name'] == PLAN_NAME
        assert json['stack_id'] == STACK_ID
        assert len(json['placements']) == 2
