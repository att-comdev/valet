# Must run as root due to rabbitmq password file
./listener.py -x nova -t topic -s -k valet_test -r 3
