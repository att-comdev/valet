'''
Created on Aug 17, 2016

@author: YB
'''

from valet.engine.optimizer.ostro_server.configuration import Config
from valet.tests.base import Base


class TestConfig(Base):

    def setUp(self):
        super(TestConfig, self).setUp()

    def test_simple_config(self):
        self.config = Config()
        config_status = self.config.configure()
        print(config_status)
        self.validate_test(config_status == "success")

    def test_unhappy_config_io(self):
        self.config = Config("../../../tests/unit/engine/unhappy.cfg")
        config_status = self.config.configure()
        print(config_status)
        self.validate_test("I/O error" in config_status)

    def test_unhappy_config(self):
        self.config = Config("../../../tests/unit/engine/invalid.cfg")
        config_status = self.config.configure()
        print(config_status)
        self.validate_test("Unexpected error while parsing system parameters" in config_status)

#     def test_empty_config(self):
#         self.config = Config("../../../tests/unit/engine/empty.cfg")
#         config_status = self.config.configure()
#         print(config_status)
#         self.validate_test("Unexpected error while parsing system parameters" in config_status)

    def test_unhappy_config_no_auth(self):
        self.config = Config("../../../tests/unit/engine/test_ostro.cfg")
        config_status = self.config.configure()
        print(config_status)
        self.validate_test("I/O error" in config_status)

    def test_unhappy_config_bad_auth(self):
        self.config = Config("../../../tests/unit/engine/test_ostro_with_auth.cfg")
        config_status = self.config.configure()
        print("../../../tests/unit/engine/test_ostro_with_auth.cfg")
        print(__file__)
        print(config_status)
        self.validate_test("Unexpected error while parsing authentication parameters" in config_status)
