'''
Created on Nov 10, 2016

@author: Yael
'''

from oslo_log import log as logging

LOG = logging.getLogger(__name__)

COLORS = \
    {
        "WHITE": '\033[0;37m',
        "L_RED": '\033[1;31m',
        "L_PURPLE": '\033[1;35m',
        "L_GREEN": '\033[0;32m',
        "L_BLUE": '\033[1;34m',
        "Yellow": '\033[0;33m'
    }


class GeneralLogger(object):

    def __init__(self, name):
        self.test_name = name

    def log_info(self, msg):
        LOG.info("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name, COLORS["L_GREEN"], msg, COLORS["WHITE"]))

    def log_error(self, msg, trc_back=None):
        LOG.error("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name, COLORS["L_RED"], msg, COLORS["WHITE"]))
        if trc_back:
            LOG.error("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name, COLORS["L_RED"], trc_back, COLORS["WHITE"]))

    def log_debug(self, msg):
        LOG.debug("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name, COLORS["L_BLUE"], msg, COLORS["WHITE"]))

    def log_group(self, msg):
        LOG.info("%s %s - %s %s %s" % (COLORS["L_PURPLE"], self.test_name, COLORS["Yellow"], msg, COLORS["WHITE"]))
