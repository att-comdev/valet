#!/usr/bin/env bash

# ``upgrade-allegro``

echo "*********************************************************************"
echo "Begin $0"
echo "*********************************************************************"

# Clean up any resources that may be in use
cleanup() {
    set +o errexit

    echo "*********************************************************************"
    echo "ERROR: Abort $0"
    echo "*********************************************************************"

    # Kill ourselves to signal any calling process
    trap 2; kill -2 $$
}

trap cleanup SIGHUP SIGINT SIGTERM

# Keep track of the grenade directory
RUN_DIR=$(cd $(dirname "$0") && pwd)

# Source params
source $GRENADE_DIR/grenaderc

# Import common functions
source $GRENADE_DIR/functions

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
set -o errexit

# Save mongodb state (replace with snapshot)
# TODO(chdent): There used to be a 'register_db_to_save allegro'
# which may wish to consider putting back in.
if grep -q 'connection *= *mongo' /etc/allegro/allegro.conf; then
    mongodump --db allegro --out $SAVE_DIR/allegro-dump.$BASE_RELEASE
fi

# Upgrade Allegro
# ===============
# Locate allegro devstack plugin, the directory above the
# grenade plugin.
ALLEGRO_DEVSTACK_DIR=$(dirname $(dirname $0))

# Get functions from current DevStack
source $TARGET_DEVSTACK_DIR/functions
source $TARGET_DEVSTACK_DIR/stackrc
source $TARGET_DEVSTACK_DIR/lib/apache

# Get allegro functions from devstack plugin
source $ALLEGRO_DEVSTACK_DIR/settings

# Print the commands being run so that we can see the command that triggers
# an error.
set -o xtrace

# Install the target allegro
source $ALLEGRO_DEVSTACK_DIR/plugin.sh stack install

# calls upgrade-allegro for specific release
upgrade_project allegro $RUN_DIR $BASE_DEVSTACK_BRANCH $TARGET_DEVSTACK_BRANCH

# Migrate the database
# NOTE(chdent): As we evolve BIN_DIR is likely to be defined, but
# currently it is not.
ALLEGRO_BIN_DIR=$(dirname $(which allegro-dbsync))
$ALLEGRO_BIN_DIR/allegro-dbsync || die $LINENO "DB sync error"

# Start Allegro
start_allegro

# Note these are process names, not service names
ensure_services_started "allegro-polling --polling-namespaces compute" \
                        "allegro-polling --polling-namespaces central" \
                        "allegro-polling --polling-namespaces ipmi" \
                        allegro-agent-notification \
                        allegro-alarm-evaluator \
                        allegro-alarm-notifier \
                        allegro-api \
                        allegro-collector

# Save mongodb state (replace with snapshot)
if grep -q 'connection *= *mongo' /etc/allegro/allegro.conf; then
    mongodump --db allegro --out $SAVE_DIR/allegro-dump.$TARGET_RELEASE
fi


set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End $0"
echo "*********************************************************************"
