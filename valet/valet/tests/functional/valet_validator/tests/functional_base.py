'''
Created on May 5, 2016

@author: Yael
'''

import os
from oslo_log import log as logging
import time
from valet.tests.base import Base
from valet.tests.functional.valet_validator.common.init import COLORS, CONF
from valet.tests.functional.valet_validator.common.resources import TemplateResources
from valet.tests.functional.valet_validator.compute.analyzer import Analyzer
from valet.tests.functional.valet_validator.orchestration.loader import Loader


LOG = logging.getLogger(__name__)


class FunctionalTestCase(Base):
    """Test case base class for all unit tests."""

    def __init__(self, *args, **kwds):
        ''' initializing the FunctionalTestCase - loading the logger, loader and analyzer '''
        super(FunctionalTestCase, self).__init__(*args, **kwds)

    def setUp(self):
        super(FunctionalTestCase, self).setUp()

        self.load = Loader()
        self.compute = Analyzer()

        LOG.info("%s %s Starting... %s" % (COLORS["L_PURPLE"], self.get_name(), COLORS["WHITE"]))

    def run_test(self, stack_name, template_path):
        ''' scenario -

                deletes all stacks
                create new stack
                checks if host (or rack) is the same for all instances
        '''
        # delete all stacks
        self.load.delete_all_stacks()

        # creates new stack
        my_resources = TemplateResources(template_path)
        tries = CONF.valet.TRIES_TO_CREATE
        
        res = self.load.create_stack(stack_name, my_resources)       
        while "Ostro error" in res.message and tries > 0:
            LOG.error("Ostro error - try number %d" %(CONF.valet.TRIES_TO_CREATE - tries + 2))
            self.load.delete_all_stacks()
            res = self.load.create_stack(stack_name, my_resources)
            tries -= 1
           
        self.validate(res)
#         self.validate(self.load.create_stack(stack_name, my_resources))
        time.sleep(self.CONF.heat.DELAY_DURATION)

        # validation
        self.validate(self.compute.check(my_resources))

    def get_template_path(self, template_name):
        possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir))
        return os.path.join(possible_topdir, 'tests/templates', template_name + '.yml')

    def init_template(self, test):
        self.stack_name = test.STACK_NAME
        self.template_path = self.get_template_path(test.TEMPLATE_NAME)
