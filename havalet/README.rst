===============================
High Availability Valet tools.
===============================


Features
--------
this tool monitors all (or a specific) configured processes for high availability


launching command line:
python ./ha_valet.py [-p name]


ha_valeta.cfg explained:

list of dictionaries of valet monitored processes.
the list keys are logical processes names.
the list value is a dictionary which MUST have the following properties:
    'host'
    'user'
    'port'
    'protocol'
    'start_command'
    'stop_command'
    'test_command'

IMPORTANT:
    "test_command" - MUST return a value != 0, this value should reflects
        the monitored process priority.

    "process's priority" - used for active/stand-by scenarios.
        MUST be greater than 0 - lower number means higher priority.
        e.g. instance which returns '1', as its response to "test_command" invocation,
        will get precedence over instance which returns '2' as its priority.
        priority 0 means thr process is down.

    "stand_by_list" - OPTIONAL property. comma delimited hosts list.
        used on active/stand-by scenarios.
        ha_valet will attempt to restart the instance with the lower priority value,
        only if the instance fails to start, ha_valet will try to restart the process
        on the following host in the list.
        
    "priority" - is the mean to set primary/secondary hierarchy,
        must be greater than 0 - lower value means higher priority

#Host A:
#=======================
:Ostro
    host = Host_A
    stand_by = Host_A,Host_B
    user = stack
    port = 8091
    protocol = http
    priority = 1
    start_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py start'" % (user, host)
    stop_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py stop'" % (user, host)
    test_command="ssh %s@%s 'exit $(@OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py status ; echo $?)'" % (user, host)

:Allegro
    host = Host_A
    user = stack
    port = 8090
    protocol = http
    priority = 1
    start_command="sudo python @ALLEGRO_WSGI_DIR@/wsgi.py &"
    stop_command="sudo pkill -f wsgi"
    test_command="netstat -nap  | grep %s | grep LISTEN | wc -l | exit $(awk \'{print $1}\')" % (port)



#Host B (172.20.90.130):
#=======================
:Ostro
    host = Host_B
    stand_by = Host_A,Host_B
    user = stack
    port = 8091
    protocol = http
    priority = 2
    start_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py start'" % (user, host)
    stop_command="ssh %s@%s 'cd @OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py stop'" % (user, host)
    test_command="ssh %s@%s 'exit $(@OSTRO_SERVER_DIR@ ; sudo python ./ostro_daemon.py status ; echo $?)'" % (user, host)

:Allegro
    host = Host_B
    user = stack
    port = 8090
    protocol = http
    priority = 1
    start_command="sudo python @ALLEGRO_WSGI_DIR@/wsgi.py &"
    stop_command="sudo pkill -f wsgi"
    test_command="netstat -nap  | grep %s | grep LISTEN | wc -l | exit $(awk \'{print $1}\')" % (port)
