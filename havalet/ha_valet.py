#!/usr/bin/env python
# vi: sw=4 ts=4:
#
# ---------------------------------------------------------------------------
#   Copyright (c) 2013-2015 AT&T Intellectual Property
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ---------------------------------------------------------------------------
#

"""
        Mnemonic:   ha_valet.py
        Abstract:   High availability script for valet processes.
                    starts it's configured processes, and pings for their availability.
                    If local instances are not running, then makes the
                    current instances start. If it finds multiple instances running, then
                    determines which instance should be shut down based on priorities.

        Author:     Amnon Sagiv based on ha_tegu by Kaustubh Joshi

 ------------------------------------------------------------------------------

  Algorithm
 -----------
 The ha_valet script runs on each valet node in a continuous loop checking for
 heartbeats from all the valet nodes found in the "stand_by_list" conf property once
 every 5 secs (default). A heartbeat is obtained by invoking the "test_command"
 conf property.
 If exactly one monitored process instance is running, the script does
 nothing. If no instance is running, then the local instance is activated after
 waiting for 5*priority seconds to let a higher priority valet take over
 first. A valet monitored process's priority is determined by its conf.
 If the current node's is running and another is found, then a
 conflict resolution process is invoked whereby the priorities of both
 processes are compared, and the instance with the higher value is deactivated.

 IMPORTANT: test_command must return a value != 0, this is value should reflects
            the monitored process priority.
 """

from os import stat
from os.path import isfile
import argparse
import sys
import time
import os
import socket
import subprocess
import threading


# Directory locations
HA_VALET_ROOT = os.getenv('HA_VALET_ROOT', './')              # valet root dir
LOG_DIR = os.getenv('HA_VALET_LOGD', HA_VALET_ROOT + 'log/')
ETC_DIR = os.getenv('HA_VALET_ETCD', '.')
CONF_FILE = ETC_DIR + '/ha_valet.cfg'

# Set the maximum logfile size as Byte for time-series log files
max_log_size = 1000000
# Set the maximum number of time-series log files
max_num_of_logs = 10


PRIMARY_SETUP = 1
RETRY_COUNT = 3      # How many times to retry ping command
CONNECT_TIMEOUT = 3  # Ping timeout
MAX_QUICK_STARTS = 10        # we stop if there are > 10 restarts in quick succession
QUICK_RESTART_SEC = 150     # we consider it a quick restart if less than this

# HA Configuration
HEARTBEAT_SEC = 5                    # Heartbeat interval in seconds


NAME = 'name'
ORDER = 'order'
HOST = 'host'
PORT = 'port'
USER = 'user'
PROTOCOL = 'protocol'
PRIORITY = 'priority'
START_COMMAND = 'start_command'
STOP_COMMAND = 'stop_command'
TEST_COMMAND = 'test_command'
STAND_BY_LIST = 'stand_by_list'


def log(fd, msg):
    """Log error message on stdout with timestamp

    :param fd: log file descriptor
    :type fd: file descriptor
    :param msg: string to log
    :type msg: string
    :return: None
    :rtype:
    """

    if fd is None or fd.closed:  # risky
        return

    now = time.gmtime()
    fd.write("%4d/%02d/%02d %02d:%02d:%02d %s\n" %
                     (now.tm_year, now.tm_mon, now.tm_mday,
                      now.tm_hour, now.tm_min, now.tm_sec, msg))
    fd.flush()


def crit(fd, msg):
    """Print critical message to log

    :param fd: log file descriptor
    :type fd: file descriptor
    :param msg: string to log
    :type msg: string
    :return: None
    :rtype:
    """
    log(fd, "CRI: " + msg)


def err(fd, msg):
    """Print error message to log

    :param fd: log file descriptor
    :type fd: file descriptor
    :param msg: string to log
    :type msg: string
    :return: None
    :rtype:
    """
    log(fd, "ERR: " + msg)


def warn(fd, msg):
    """Print warning message to log

    :param fd: log file descriptor
    :type fd: file descriptor
    :param msg: string to log
    :type msg: string
    :return: None
    :rtype:
    """
    log(fd, "WRN: " + msg)


def get_last_logfile(_loc, _max_log_size, _max_num_of_logs, _name, _last_index):

    last_logfile = _name + "_" + str(_last_index) + ".log"

    mode = None

    if isfile(_loc + last_logfile):
        statinfo = stat(_loc + last_logfile)
        if statinfo.st_size > _max_log_size:
            if (_last_index + 1) < _max_num_of_logs:
                _last_index += 1
            else:
                _last_index = 0

            last_logfile = _name + "_" + str(_last_index) + ".log"

            mode = 'w'
        else:
            mode = 'a'
    else:
        mode = 'w'

    return last_logfile, _last_index, mode


class HaValetThread (threading.Thread):

    def __init__(self, data, exit_event):
        threading.Thread.__init__(self)
        self.exitFlag = exit_event
        self.data = data
        self.last_log_index = 1
        self.log_fd = None
        self.name = "HA Valet Thread - "+data["name"]

    def set_logger(self):
        try:
            app_logfile, self.last_log_index, mode = get_last_logfile(LOG_DIR, max_log_size, max_num_of_logs,
                                                                      self.data["name"], self.last_log_index)
            self.log_fd = open(LOG_DIR + app_logfile, mode)
        except IOError as e:
            print "I/O error({}): {} while opening log file".format(e.errno, e.strerror)
            sys.exit(e.errno)

    def run(self):
        """Main function"""
        self.set_logger()
        log(self.log_fd, self.name + " - starting")

        fqdn_list = []
        this_node = socket.getfqdn()
        fqdn_list.append(this_node)

        # Read list of standby valet nodes and find us
        standby_list = []
        stand_by = self.data.get(STAND_BY_LIST, None)
        if stand_by is not None:
            standby_list = stand_by.split(",")

        while not self.exitFlag.isSet() and not len(standby_list) is 0:            # loop until we find us
            log(self.log_fd, self.data[NAME] + "- stand by list: " + str(standby_list))
            try:
                for fqdn in fqdn_list:
                    log(self.log_fd, self.data[NAME] + "- fqdn_list: " + str(fqdn_list))
                    if fqdn in standby_list:
                        this_node = fqdn
                        break
                standby_list.remove(this_node)
                self.data[STAND_BY_LIST] = standby_list
                log(self.log_fd, self.data[NAME] + "- modified stand by list: " + str(standby_list))
            except ValueError:
                log(self.log_fd, self.data[NAME] + ": host " + this_node +
                    " is not in standby list: %s - continue" % str(standby_list))
                break
        self.logger_close()

        # Loop forever sending pings
        self._main_loop(this_node)

        self.set_logger()
        log(self.log_fd, self.name + " - going down!")
        self.logger_close()

    def _main_loop(self, this_node):
        """Main heartbeat and liveness check loop

        :param this_node: host name
        :type this_node: string
        :return: None
        :rtype:
        """

        quick_start = 0           # number of restarts close together
        last_start = 0
        priority_wait = False

        """ DO NOT RENAME, DELETE, MOVE the following parameters,
         they may be referenced from within the process commands"""
        name = self.data.get(NAME, 'n/a')
        host = self.data.get(HOST, 'localhost')
        port = self.data.get(PORT, None)
        user = self.data.get(USER, None)
        protocol = self.data.get(PROTOCOL, None)
        priority = int(self.data.get(PRIORITY, 1))
        start_command = eval(self.data.get(START_COMMAND, None))
        stop_command = self.data.get(STOP_COMMAND, None)
        test_command = self.data.get(TEST_COMMAND, None)
        standby_list = self.data.get(STAND_BY_LIST)

        while not self.exitFlag.isSet():
            if not priority_wait:
                # Normal heartbeat
                time.sleep(HEARTBEAT_SEC)
            else:
                # No valet running. Wait for higher priority valet to activate.
                time.sleep(HEARTBEAT_SEC*priority)

            self.set_logger()

            log(self.log_fd, name + ': checking status here - ' + host)
            i_am_active, my_priority = self._is_active(name, eval(test_command))
            log(self.log_fd, name + ': i am active = ' + str(i_am_active) + ', ' + str(my_priority))
            any_active = i_am_active
            log(self.log_fd, name + ': any active = ' + str(any_active))

            # Check for active valets
            if standby_list is not None:
                log(self.log_fd, name + "- main loop: standby_list is not empty " + str(standby_list))
                for host_in_list in standby_list:
                    if host_in_list == this_node:
                        log(self.log_fd, name + "- host_in_list is this_node - skipping")
                        continue
                    
                    log(self.log_fd, name + ': checking status on - ' + host_in_list)
                    host = host_in_list
                    host_active, host_priority = self._is_active(name, eval(test_command))
                    host = self.data.get(HOST, 'localhost')
                    log(self.log_fd, name + ': ' + host_in_list + ' - host_active-' + str(host_active) + ', ' +
                        str(host_priority))
                    # Check for split brain: 2 valets active
                    if i_am_active and host_active:
                        log(self.log_fd, name + ": found two live instances, checking priorities")
                        should_be_active = self._should_be_active(host_priority, my_priority)
                        if should_be_active:
                            log(self.log_fd, name + ": deactivate myself, " + host_in_list + " already running")
                            self._deactivate_process(name, eval(stop_command))     # Deactivate myself
                            i_am_active = False
                        else:
                            log(self.log_fd, name + ": deactivate " + host_in_list + ", already running here")
                            host = host_in_list
                            self._deactivate_process(name, eval(stop_command))  # Deactivate other valet
                            host = self.data.get(HOST, 'localhost')

                    # Track that at-least one valet is active
                    any_active = any_active or host_active

            # If no active process or I'm primary, then we must try to start one
            if not any_active or (not i_am_active and priority == PRIMARY_SETUP):
                log(self.log_fd, name + "- there is no instance up  - OR  - I'm primary and down")
                if priority_wait or priority == 0:
                    now = int(time.time())
                    if now - last_start < QUICK_RESTART_SEC:           # quick restart (crash?)
                        quick_start += 1
                        if quick_start > MAX_QUICK_STARTS:
                            crit(self.log_fd, "refusing to restart "+name+": too many restarts in quick succession.")
                            # kill ourselves [if there is a watch dog it will restart us]
                            self.exitFlag.set()
                            return
                    else:
                        quick_start = 0               # reset if it's been a while since last restart

                    if last_start == 0:
                        diff = "never by this instance"
                    else:
                        diff = "%d seconds ago" % (now - last_start)

                    last_start = now
                    priority_wait = False
                    if (not i_am_active and priority == PRIMARY_SETUP) or (standby_list is not None):
                        log(self.log_fd, "no running " + name + " found, starting here; last start %s" % diff)
                        self._activate_process(name, start_command)
                    else:
                        host = standby_list[0]
                        log(self.log_fd, "no running " + name + " found, starting on %s; last start %s" % (host, diff))
                        self._activate_process(name, start_command)
                        host = self.data.get(HOST, 'localhost')
                else:
                    priority_wait = True
            else:
                log(self.log_fd, "up and running")

            self.logger_close()
        # end loop

    def logger_close(self):
        if self.log_fd is not None:
            self.log_fd.close()

    def _should_be_active(self, host_priority, my_priority):
        """Returns True if host should be active as opposed to current node, based on the hosts priorities.
           Lower value means higher Priority,
           0 (zero) - invalid priority (e.g. process is down)

        :param host_priority: other host's priority
        :type host_priority: int
        :param my_priority: my priority
        :type my_priority: int
        :return: True/False
        :rtype: bool
        """
        log(self.log_fd, 'my priority is %d, remote priority is %d' % (my_priority, host_priority))
        return host_priority < my_priority

    def _is_active(self, name, call):
        """Return 'True, Priority' if valet is running on host
           'False, None' Otherwise."""

        # must use no-proxy to avoid proxy servers gumming up the works
        for i in xrange(RETRY_COUNT):
            try:
                log(self.log_fd, name + ' ping (retry %d): %s' % (i, call))
                priority = subprocess.call(call, stdout=self.log_fd, stderr=self.log_fd, shell=True)
                log(self.log_fd, name + ' ping result (should be > 0): %s' % (str(priority)))
                return (priority > 0), priority
            except subprocess.CalledProcessError:
                continue
        return False, None

    def _deactivate_process(self, name, deactivate_command):
        """ Deactivate valet on a given host. If host is omitted, local
            valet is stopped. Returns True if successful, False on error."""

        try:
            # call = "'" + deactivate_command % (PROTO, host, port) + "'"
            log(self.log_fd, name + ': deactivate_command: ' + deactivate_command)
            subprocess.check_call(deactivate_command, stdout=self.log_fd, stderr=self.log_fd, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _activate_process(self, name, activate_command):
        """ Activate valet on a given host. If host is omitted, local
            valet is started. Returns True if successful, False on error."""

        try:
            log(self.log_fd, name + ': activate_command: ' + activate_command)
            subprocess.check_call(activate_command, stdout=self.log_fd, stderr=self.log_fd, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False


class HAValet:

    def __init__(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

    def _parse_valet_conf(self, conf_file_name='./ha_valet.cfg', process=''):
        """ This function reads the valet config file and returns configuration
        attributes in key/value format

        :param conf_file_name: config file name
        :type conf_file_name: string
        :param process: specific process name
                        when not supplied - the module launches all the processes in the configuration
        :type process: string
        :return: dictionary of configured monitored processes
        :rtype: dict
        """

        cdata = {}
        section = ''

        try:
            with open(conf_file_name, 'r') as valet_conf_file:
                for line in valet_conf_file.readlines():
                    if line.strip(' \t\r\n')[:1] == '#' or line.__len__() == 2:
                        continue
                    elif line.lstrip(' \t\r\n')[:1] == ':':
                        tokens = line.lstrip(' \t\n\r').split(' ')
                        section = tokens[0][1:].strip('\n\r\n')
                        cdata[section] = {}
                        cdata[section][NAME] = section
                    else:
                        if line[:1] == '\n':
                            continue
                        tokens = line.split('=')
                        key = tokens[0].strip(' \t\n\r')
                        value = tokens[1].strip(' \t\n\r')
                        cdata[section][key] = value

            # if need to run a specific process
            # remove all others
            if process is not '':
                for key in cdata.keys():
                    if key != process:
                        del cdata[key]

            return cdata
        except OSError:
            print('unable to open %s file for some reason' % conf_file_name)
        return cdata

    def _valid_process_conf_data(self, process_data):
        """verify all mandatory parameters are found in the monitored process configuration
           only standby_list is optional

        :param process_data: specific process configuration parameters
        :type process_data: dict
        :return: are all mandatory parameters are found
        :rtype: bool
        """
        if (process_data.get(HOST) is not None and process_data.get(PORT) is not None and
            process_data.get(PROTOCOL) is not None and process_data.get(PRIORITY) is not None and
            process_data.get(START_COMMAND) is not None and process_data.get(STOP_COMMAND) is not None and
            process_data.get(TEST_COMMAND) is not None):
                return True
        else:
            return False

    def start(self):
        """Start valet HA - Main function"""
        print 'ha_valet v1.1 starting'

        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--process', help='process name to monitor', default='')
        args = parser.parse_args()

        conf_data = self._parse_valet_conf(process=args.process)

        # if a specific process was asked for..
        # remove all others
        if args.process is not '':
            for key in conf_data.keys():
                if key != args.process:
                    del conf_data[key]

            if conf_data.get(args.process) is None:
                print args.process, ' - process not found in conf.'

        if len(conf_data.keys()) is 0:
            print 'Processes list is empty - leaving.'
            return

        threads = []
        exit_event = threading.Event()

        # sort by launching order
        proc_sorted = sorted(conf_data.values(), key=lambda d: d[ORDER])

        for proc in proc_sorted:
            if self._valid_process_conf_data(proc):
                print 'Launching:', proc[NAME], ', order:', proc[ORDER]
                thread = HaValetThread(proc, exit_event)
                time.sleep(HEARTBEAT_SEC)
                thread.start()
                threads.append(thread)
            else:
                print proc[NAME] + " section is missing mandatory parameter."
                continue

        print 'Type "quit" to exit.'

        while not exit_event.isSet():
            time.sleep(HEARTBEAT_SEC)
            line = raw_input('PROMPT> ')
            if line == 'quit':
                exit_event.set()
                print 'exit event fired'

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print 'ha_valet v1.1 exiting'

if __name__ == '__main__' or __name__ == "main":
    HAValet().start()
