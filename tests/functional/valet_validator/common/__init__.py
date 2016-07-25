import time
from valet_validator.common.init import CONF, COLORS
from oslo_log import log as logging
import sys

LOG = logging.getLogger(__name__)

class Result:
    ok = False
    message = ""
    
    def __init__(self, ok = True, msg = ""):
        self.ok = ok
        self.message = msg


class General(object):
    @staticmethod
    def delay(duration = None):
        time.sleep(duration or CONF.heat.DELAY_DURATION)
    
    @staticmethod
    def log_info(msg):
        LOG.info("%s %s %s" % (COLORS["L_GREEN"], msg, COLORS["WHITE"]))
    
    @staticmethod
    def log_error(msg, trc_back = ""):
        LOG.error("%s %s %s" % (COLORS["L_RED"], msg, COLORS["WHITE"]))
        LOG.error("%s %s %s" % (COLORS["L_RED"], trc_back, COLORS["WHITE"]))
#         sys.exit(1)
    
    @staticmethod
    def log_debug(msg):
        LOG.debug("%s %s %s" % (COLORS["L_BLUE"], msg, COLORS["WHITE"]))
    
    
    @staticmethod
    def log_group(msg):
        LOG.info("%s %s %s" % (COLORS["Yellow"], msg, COLORS["WHITE"]))