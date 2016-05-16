# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python daemon.py start

# standard python libs
import logging
import os
import sys
import time

import listener

from daemon import runner

PIDFILE_PATH = os.environ.get('PIDFILE_PATH', 'ostro-listener.pid')
PIDFILE_TIMEOUT = int(os.environ.get('PIDFILE_TIMEOUT', 5))
LOGFILE = os.environ.get('LOGFILE', 'ostro-listener.log')
LOGNAME = "OstroListener"
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class App():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = PIDFILE_PATH
        self.pidfile_timeout = PIDFILE_TIMEOUT
            
    def run(self):
        # python-daemon doesn't slurp these out, so we do it.
        for option in ('start', 'stop', 'restart'):
            if option in sys.argv:
                sys.argv.remove(option)
        listener.main()

# TODO: Move all of this log stuff into listener
# TODO: Allow log level in config
logger = logging.getLogger(LOGNAME)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(LOGFORMAT)
handler = logging.FileHandler(LOGFILE)
handler.setFormatter(formatter)
logger.addHandler(handler)
'''
logger.debug("Debug message")
logger.info("Info message")
logger.warn("Warning message")
logger.error("Error message")
'''

# Preserve the logger file handle so it isn't closed during daemonization
app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
