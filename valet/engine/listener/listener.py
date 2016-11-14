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

'''
Ostro-specific OpenStack Event Listener
'''

# Based on work by Pramod Jamkhedkar and Jon Wright

# TODO(GY): Get rid of globals, turn into package/classes

# from __future__ import print_function

import argparse
import ConfigParser
from datetime import datetime
import json
import logging
import os
import pika
import pprint
import stat
import sys
from urlparse import urlparse
from valet.api.db.models.music import Music
from valet.engine.listener.oslo_messages import OsloMessage
import yaml


LOG = logging.getLogger('OstroListener')

LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_ARGS = None
MUSIC = None  # Database Engine


def store_message(message):
    '''Store message in Music'''
    timestamp = datetime.now().isoformat()
    args = json.dumps(message.get('args', None))
    exchange = _ARGS.exchange
    method = message.get('method', None)

    kwargs = {
        'timestamp': timestamp,
        'args': args,
        'exchange': exchange,
        'method': method,
        'database': MUSIC,
    }
    OsloMessage(**kwargs)  # pylint: disable=W0612


def is_message_wanted(message):
    ''' Based on markers from Ostro, determine if this is a wanted message. '''
    method = message.get('method', None)
    args = message.get('args', None)
    if not method or not args:
        return False

    if method == 'object_action':
        if 'objinst' in args.keys():
            objinst = args['objinst']
            if 'nova_object.name' in objinst.keys():
                nova_object_name = objinst['nova_object.name']
                if nova_object_name == 'Instance':
                    if 'nova_object.changes' in objinst.keys() and \
                       'nova_object.data' in objinst.keys():
                        change_list = objinst['nova_object.changes']
                        change_data = objinst['nova_object.data']
                        if 'vm_state' in change_list and \
                           'vm_state' in change_data.keys():
                            if change_data['vm_state'] == 'deleted' or change_data['vm_state'] == 'active':
                                return True
                elif nova_object_name == 'ComputeNode':
                    if 'nova_object.changes' in objinst.keys() and \
                       'nova_object.data' in objinst.keys():
                        return True

    elif method == 'build_and_run_instance':
        if 'filter_properties' in args.keys() and \
           'instance' in args.keys():
            instance = args['instance']
            if 'nova_object.data' in instance.keys():
                return True

    return False


def on_message(channel, method_frame, header_frame, body):  # pylint: disable=W0613
    '''Specify the action to be taken on a message received'''
    message = yaml.load(body)
    if 'oslo.message' in message.keys():
        message = yaml.load(message['oslo.message'])
    if is_message_wanted(message):
        if MUSIC and MUSIC.get('engine'):
            store_message(message)
    else:
        return

    LOG.debug("\nMessage No: %s\n", method_frame.delivery_tag)
    message_obj = yaml.load(body)
    if 'oslo.message' in message_obj.keys():
        message_obj = yaml.load(message_obj['oslo.message'])
    if _ARGS.output_format == 'json':
        LOG.debug(json.dumps(message_obj, sort_keys=True, indent=2))
    elif _ARGS.output_format == 'yaml':
        LOG.debug(yaml.dump(message_obj))
    else:
        LOG.debug(pprint.pformat(message_obj))
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def safe_file(filename):
    '''Determine if a file is safe to read'''
    status = os.stat(filename)
    if bool(status.st_mode & stat.S_IRGRP) or \
       bool(status.st_mode & stat.S_IWGRP) or \
       bool(status.st_mode & stat.S_IXGRP) or \
       bool(status.st_mode & stat.S_IXOTH) or \
       bool(status.st_mode & stat.S_IROTH) or \
       bool(status.st_mode & stat.S_IWOTH):
        return False
    return True


def _parse_arguments():
    '''Parse arguments'''

    # http://blog.vwelch.com/2011/04/
    #    combining-configparser-and-argparse.html
    # Turn off help, so we print all options in response to -h
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument("-c", "--conf_file",
                             help="Defaults to env[OSTRO_LISTENER_CONFIG]",
                             metavar="OSTRO_LISTENER_CONFIG")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {
        'exchange': 'nova',
        'exchange_type': 'topic',
        'auto_delete': False,
        'host': 'localhost',
        'port': 5672,
        'username': 'guest',
        'passwdfile': 'passwd',
        'output_format': 'dict',
        'store': False,
        'music': 'http://127.0.0.1:8080/',
        'keyspace': 'valet',
        'replication_factor': 3}

    # Command line-supplied config overrides the environment
    conf_file = None
    if args.conf_file:
        conf_file = args.conf_file
    else:
        conf_file = os.environ.get('OSTRO_LISTENER_CONFIG')
    if conf_file:
        LOG.info('Config file is %s', conf_file)

    if conf_file:
        config = ConfigParser.SafeConfigParser()
        config.read([conf_file])
        section = "DEFAULT"
        defaults = dict(config.items(section))
        for bool_opt in ('auto_delete', 'store'):
            if config.has_option(section, bool_opt):
                defaults[bool_opt] = config.getboolean(section, bool_opt)

    # Don't surpress add_help here so it will handle -h.
    parser = argparse.ArgumentParser(parents=[conf_parser], description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # Inherit options from config_parser,
    # print script description with -h/--help,
    # and don't mess with the description format.
    parser.set_defaults(**defaults)

    parser.add_argument(
        '-x', '--exchange', type=str, dest='exchange',
        help='rabbit exchange to listen to')
    parser.add_argument(
        '-t', '--exchange_type', type=str, dest='exchange_type',
        help='type of exchange (default="topic")',
        choices=['topic', 'fanout'])
    parser.add_argument(
        '-a', '--auto_delete', dest='auto_delete', action='store_true',
        help='autodelete exchange (default=False)')
    parser.add_argument(
        '-H', '--host', type=str, dest='host',
        help='compute node on which rabbitmq is running')
    parser.add_argument(
        '-p', '--port', type=int, dest='port',
        help='port on which rabbitmq is running')
    parser.add_argument(
        '-u', '--username', type=str, dest='username',
        help='rabbitmq username (default="guest")')
    parser.add_argument(
        '-P', '--passwdfile', type=str, dest='passwdfile',
        help='file containing host rabbitmq passwords')
    parser.add_argument(
        '-o', '--output_format', type=str, dest='output_format',
        help='output format (default="dict")',
        choices=['yaml', 'json', 'dict'])
    parser.add_argument(
        '-s', '--store', dest='store', action='store_true',
        help='store messages in music (default=False)')
    parser.add_argument(
        '-m', '--music', type=str, dest='music',
        help='music endpoint')
    parser.add_argument(
        '-k', '--keyspace', type=str, dest='keyspace',
        help='music keyspace')
    parser.add_argument(
        '-r', '--replication_factor', type=int, dest='replication_factor',
        help='music replication factor')
    return parser.parse_args(remaining_argv)


def setup_logging(logformat, logfile=None):
    '''Setup Logging and return handler'''
    LOG.setLevel(logging.DEBUG)
    LOG.propagate = False
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(logformat)
    handler.setFormatter(formatter)
    LOG.addHandler(handler)
    return handler


def main():
    '''Entry point'''
    global _ARGS  # pylint: disable=W0603
    global MUSIC  # pylint: disable=W0603

    _ARGS = _parse_arguments()

    # Connect to the localhost rabbitmq servers
    # use username:password@ipaddress:port. The port is typically 5672,
    # and the default username and password are guest and guest.
    # credentials = pika.PlainCredentials("guest", "PASSWORD")

    # Check for safety of rabbitmq password file
    passwd = ''
    if os.path.exists(_ARGS.passwdfile):
        if not safe_file(_ARGS.passwdfile):
            LOG.error('ERROR: existing password file %s is readable/writable by group/other',
                      _ARGS.passwdfile)
            sys.exit(1)
        with open(_ARGS.passwdfile, 'rb') as filed:
            for line in filed:
                line = line.strip()
                if len(line) == 0:
                    continue
                flds = line.split(' ')
                if _ARGS.host.startswith(flds[0]) or \
                        flds[0].startswith(_ARGS.host):
                    passwd = flds[1]
    if passwd == '':
        LOG.error('ERROR: Host %s not found in password file %s',
                  _ARGS.host, _ARGS.passwdfile)
        sys.exit(2)

    if _ARGS.store:
        music_args = urlparse(_ARGS.music)
        kwargs = {
            'host': music_args.hostname,
            'port': music_args.port,
            'replication_factor': _ARGS.replication_factor,
        }
        engine = Music(**kwargs)
        engine.create_keyspace(_ARGS.keyspace)
        MUSIC = {'engine': engine, 'keyspace': _ARGS.keyspace}
        print('storing in music on %s, keyspace %s' %
              (_ARGS.music, _ARGS.keyspace))

    # with open(_ARGS.passwdfile, 'rb') as fd:
    credentials = pika.PlainCredentials(_ARGS.username, passwd)
    parameters = pika.ConnectionParameters(
        _ARGS.host, _ARGS.port, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Select the exchange we want our queue to connect to
    exchange_name = _ARGS.exchange

    # Select the exchange type
    exchange_type = _ARGS.exchange_type

    # Select the exchange auto_delete mode
    auto_delete = _ARGS.auto_delete

    # Use the binding key to select what type of messages you want
    # to receive. '#' is a wild card -- meaning receive all messages
    binding_key = "#"

    # Check whether or not an exchange with the given name and type exists
    # Make sure that the exchange is multicast "fanout" or "topic" type
    # otherwise our queue will consume the messages intended for other queues
    channel.exchange_declare(exchange=exchange_name,
                             exchange_type=exchange_type,
                             auto_delete=auto_delete)

    # Create an empty queue
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    # Bind the queue to the selected exchange
    channel.queue_bind(exchange=exchange_name, queue=queue_name,
                       routing_key=binding_key)
    LOG.info('Channel is bound, listening on %s %s',
             _ARGS.host, _ARGS.exchange)

    # Start consuming messages
    channel.basic_consume(on_message, queue_name)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    # Close the channel on keyboard interrupt
    channel.close()
    connection.close()


def main_cmd():
    # Leave this level of indirection. Daemon sets up its own logging.
    setup_logging(LOGFORMAT)
    main()

if __name__ == '__main__':
    main_cmd()
