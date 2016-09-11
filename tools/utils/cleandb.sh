#!/usr/bin/env bash

# drop keyspace
echo "drop valet keyspace"
sudo /opt/valet/apache-cassandra-2.1.1/bin/cqlsh  -e "DROP KEYSPACE valet_test;"

sleep 5

# populate tables
echo "populate valet tables"
sudo /opt/valet/apache-cassandra-2.1.1/bin/cqlsh  -f /opt/valet/populate.cql

sudo /opt/valet/apache-cassandra-2.1.1/bin/cqlsh  -e "DESCRIBE KEYSPACE valet_test;"

echo "Done populating"
