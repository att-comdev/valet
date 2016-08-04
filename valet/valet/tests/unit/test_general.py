
from valet.tests.functional.valet_validator.tests.base import TestCase


class TestGeneral(TestCase):

    def setUp(self):
        super(TestGeneral, self).setUp()

    def test_general(self):
        self.validate_test(True)
#        self.assertEqual(True, False, "successful test")
