'''
Created on Jun 1, 2016

@author: stack
'''

from oslo_config import cfg
from oslo_log import log as logging
from valet_validator.common.init import CONF
from valet_validator.tests.base import TestCase


opt_test_ex = [
    cfg.StrOpt('STACK_NAME', default="exclusivity_stack"),
    cfg.StrOpt('TEMPLATE_NAME', default="exclusivity-basic"),
    ]

CONF.register_opts(opt_test_ex, group="test_exclusivity")
LOG = logging.getLogger(__name__)

class TestExclusivity(TestCase):

    def setUp(self):
        '''
        Adding configuration and logging mechanism
        '''
        super(TestExclusivity, self).setUp()
        self.init_template(CONF.test_exclusivity)
 
    def test_exclusivity(self):
        self.run_test(self.stack_name, self.template_path)
        
    def get_name(self):
        return __name__