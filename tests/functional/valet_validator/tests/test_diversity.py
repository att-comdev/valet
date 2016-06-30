'''
Created on May 4, 2016
 
@author: root
'''
 
from oslo_config import cfg
from oslo_log import log as logging
from valet_validator.common.init import CONF
from valet_validator.tests.base import TestCase


opt_test_div = [
    cfg.StrOpt('STACK_NAME', default="diversity_stack"),
    cfg.StrOpt('TEMPLATE_NAME', default="diversity1"),
    ]
 
CONF.register_opts(opt_test_div, group="test_diversity")
LOG = logging.getLogger(__name__)


class TestDiversity(TestCase):
  
    def setUp(self):
        '''
        Adding configuration and logging mechanism
        '''
        super(TestDiversity, self).setUp()
        self.init_template(CONF.test_diversity)

         
    def test_diversity(self):

        self.run_test(self.stack_name, self.template_path)

    
    def get_name(self):
        return __name__
        