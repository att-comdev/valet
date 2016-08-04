#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''Ostro Event Listener Daemon'''

from daemon import runner
import logging
import os
import sys
import valet.engine.listener.listener as listener


PIDFILE_PATH = os.environ.get('PIDFILE_PATH')
PIDFILE_TIMEOUT = int(os.environ.get('PIDFILE_TIMEOUT', 5))
LOGFILE = os.environ.get('LOGFILE')
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOG = logging.getLogger('OstroListener')

# pylint: disable=R0903


class App(object):
    '''Ostro Event Listener App Wrapper'''

    def __init__(self):
        '''Initializer'''
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = PIDFILE_PATH
        self.pidfile_timeout = PIDFILE_TIMEOUT

    def run(self):  # pylint: disable=R0201
        '''Run loop'''
        # python-daemon doesn't slurp these out, so we do it.
        for option in ('start', 'stop', 'restart'):
            if option in sys.argv:
                sys.argv.remove(option)
        listener.main()


def main():
    # Preserve logger file handle so it isn't closed during daemonization
    if not PIDFILE_PATH or not LOGFILE:
        print("Must specify PIDFILE_PATH and LOGFILE in environment.")
        exit(1)
    app = App()
    handler = listener.setup_logging(LOGFORMAT, LOGFILE)
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.daemon_context.files_preserve = [handler.stream]
    daemon_runner.do_action()

if __name__ == '__main__':
    main()
