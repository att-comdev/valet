#!/usr/bin/python

# Author: Pramod Jamkhedkar, Jon Wright
# initial version: September 21, 2014
# Last Modified: October 10, 2014

from __future__ import print_function
import pika
import sys
import os
import stat
import pprint
import yaml
import argparse
import pdb

# Method which speficies the action to be taken on a message received
import pdb
def on_message(channel, method_frame, header_frame, body):
    print("\nMessage No:", method_frame.delivery_tag)
    #print body
    message_obj =  yaml.load(body)
    if 'oslo.message' in message_obj.keys():
    	message_obj = yaml.load(message_obj['oslo.message'])
    #if "admin" in message_obj['_context_roles']:
    pprint.pprint(message_obj)
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

def safe_file(f):
    if bool(st.st_mode & stat.S_IRGRP) or \
       bool(st.st_mode & stat.S_IWGRP) or \
       bool(st.st_mode & stat.S_IXGRP) or \
       bool(st.st_mode & stat.S_IXOTH) or \
       bool(st.st_mode & stat.S_IROTH) or \
       bool(st.st_mode & stat.S_IWOTH):
           return False
    return True

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-x', '--exchange', type=str, dest='exchange',
            help='rabbit exchange to listen to', default='nova')
    parser.add_argument(
            '-H', '--host', type=str, dest='host',
            help='compute node on which rabbitmq is running', default='sds101.research.att.com')
    parser.add_argument(
            '-p', '--port', type=int, dest='port',
            help='port on which rabbitmq is running', default=5672)
    parser.add_argument(
            '-u', '--username', type=str, dest='user',
            help='rabbitmq username (default="guest")', default='guest')
    parser.add_argument(
            '-P', '--passwdfile', type=str, dest='passwdfile',
            help='file containing host rabbitmq passwords', default='/usr/local/share/sds/rabbitmqpasswords')
    return parser.parse_args()

if __name__ == '__main__':
    args = _parse_arguments()
    #Connect to the localhost rabbitmq servers 
    # use username:password@ipaddress:port. The port is typically 5672, 
    #and the default username and password are guest and guest  
    #credentials = pika.PlainCredentials("guest","bybyg33!")
    #credentials = pika.PlainCredentials("guest","w1seguys")

    # check for safety of rabbitmq password file
    passwd=''
    if os.path.exists(args.passwdfile):
        st = os.stat(args.passwdfile)
        if not safe_file(args.passwdfile):
            print(
                    'ERROR: exiting password file', 
                    args.passwdfile, 
                    'is readable/writable by group/other', 
                    file=sys.stderr)
            sys.exit(1)
        with open(args.passwdfile, 'rb') as fd:
            for l in fd:
                l = l.strip()
                if len(l) == 0:
                    continue
                flds = l.split(' ')
                if args.host.startswith(flds[0]) or flds[0].startswith(args.host):
                    passwd = flds[1]
    if passwd == '':
        print(
                'ERROR: Host', 
                args.host, 
                'not found in password file',  
                args.passwdfile, 
                file=sys.stderr)
        sys.exit(2)


    #with open(args.passwdfile, 'rb') as fd:
    credentials = pika.PlainCredentials(args.user, passwd)
    parameters = pika.ConnectionParameters(args.host,args.port,'/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Select the exchange we want our queue to connect to
    exchange_name=args.exchange

    # Use the binding key to select what type of messages you want to receive. 
    # # is a wild card -- meaning receive all messages
    binding_key = "#"

    # Check whether or not an exchange with the given name and type exists
    # Make sure that the exchange is multicast "fanout" or "topic" type
    # otherwise our queue will consume the messages intended for other queues
    channel.exchange_declare(exchange=exchange_name, type='topic')

    # Create an empty queue
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    #Bind the queue to the selected exchange
    channel.queue_bind(exchange=exchange_name,queue=queue_name,routing_key=binding_key)
    print('channel is bound!!!')
    print('listening on', args.host, args.exchange)

    # Start consuming messages
    channel.basic_consume(on_message, queue_name )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    # Close the channel on keyboard interrupt
    channel.close()
    connection.close()


