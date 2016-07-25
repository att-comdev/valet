'''
Created on May 5, 2016

@author: Yael
'''

import os
from oslotest.base import BaseTestCase
from oslo_config import fixture as fixture_config
from oslo_log import log as logging
from valet_validator.common import init
from valet_validator.common.init import COLORS
from valet_validator.compute.analyzer import Analyzer
from valet_validator.orchestration.loader import Loader
from valet_validator.common.resources import TemplateResources

LOG = logging.getLogger(__name__)


class TestCase(BaseTestCase):
    """Test case base class for all unit tests."""
    
    def __init__(self, *args, **kwds):
        '''
        initializing the TestCase - loading the logger, loader and analyzer
        '''
        super(TestCase, self).__init__(*args, **kwds)
        
        self.CONF = self.useFixture(fixture_config.Config()).conf
        init.prepare(self.CONF)
        
    
    def setUp(self):
        super(TestCase, self).setUp()
                
        self.load = Loader()
        self.compute = Analyzer()

        LOG.info("%s %s Starting... %s" % (COLORS["L_PURPLE"], self.get_name(), COLORS["WHITE"]))
        
        
    def run_test(self, stack_name, template_path):
        '''
        scenario - 
                deletes all stacks
                create new stack
                checks if host (or rack) is the same for all instances
        '''
        # delete all stacks
        self.load.delete_all_stacks()
        
        # creates new stack
        my_resources = TemplateResources(template_path)
        self.validate(self.load.create_stack(stack_name, template_path, my_resources))
        
        # validation
        self.validate(self.compute.check(my_resources))
        

    def get_template_path(self, template_name):
        possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir))
        return os.path.join(possible_topdir, 'tests/templates', template_name + '.yml') 
    
    
    def init_template(self, test): 
        self.stack_name = test.STACK_NAME
        self.template_path = self.get_template_path(test.TEMPLATE_NAME)
    
    
    def validate(self, result):
        self.assertEqual(True, result.ok, result.message)
    
    
    def get_name(self):
        pass
        
        