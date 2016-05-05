# OpenStack Event Listener for Ostro

This script is based on a RabbitMQ message bus listener. It has been modified to listen for specific messages needed by Ostro and persist digested versions of the messages to Music.

This version of the listener does not use oslo.messages. It listens directly to the message transport. Future revisions are expected to use oslo.message in order to keep the means of transport abstract.

This script is not yet daemonized or packaged for pip installation.

## Usage

```
usage: listener.py [-h] [-x EXCHANGE] [-t {topic,fanout}] [-a] [-H HOST]
                   [-p PORT] [-u USER] [-P PASSWDFILE] [-o {yaml,json,dict}]
                   [-s] [-m MUSIC] [-k KEYSPACE] [-r REPLICATION_FACTOR]

optional arguments:
  -h, --help            show this help message and exit
  -x EXCHANGE, --exchange EXCHANGE
                        rabbit exchange to listen to
  -t {topic,fanout}, --exchange_type {topic,fanout}
                        type of exchange (default="topic")
  -a, --auto_delete     autodelete exchange (default=False)
  -H HOST, --host HOST  compute node on which rabbitmq is running
  -p PORT, --port PORT  port on which rabbitmq is running
  -u USER, --username USER
                        rabbitmq username (default="guest")
  -P PASSWDFILE, --passwdfile PASSWDFILE
                        file containing host rabbitmq passwords
  -o {yaml,json,dict}, --output_format {yaml,json,dict}
                        output format (default="dict")
  -s, --store           store messages in music (default=False)
  -m MUSIC, --music MUSIC
                        music endpoint
  -k KEYSPACE, --keyspace KEYSPACE
                        music keyspace
  -r REPLICATION_FACTOR, --replication_factor REPLICATION_FACTOR
                        music replication factor
```

## Example Invocation

Split across lines for readability.

```
./listener.py -x nova -t topic -s -r 3
              -k KEYSPACE -H RABBITMQ -u USERNAME
              -P PASSWDFILE -m MUSICURL
```

Where:

**-x nova:** Listen to the rabbitmq exchange 'nova'
**-t topic:** The rabbitmq exchange type is 'topic'
**-s:** Store messages in Music
**-r 3:** Use a Music replication factor of 3

Implied/default options:

**-p 5672:** The rabbitmq port
**-o dict:** Output to the console in python dictionary format

Other options that must be set based on the individual setup:

**-k KEYSPACE:** Use the KEYSPACE keyspace
**-H RABBITMQ:** The rabbitmq domain/ip
**-u USERNAME:** The rabbitmq username
**-P PASSWDFILE:** File with rabbitmq username/password pairs
**-m MUSICURL:** Music API endpoint/port

## Password File

The password file must not be readable by group/other. It is often set to root ownership.

Separate usernames and passwords with a single space. For example:

```
127.0.0.1 password
localhost password
myhost password
myhost.at.att.com password
```
