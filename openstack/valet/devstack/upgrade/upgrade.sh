#!/usr/bin/env bash

# ``upgrade-valet``

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
# TODO(chdent): There used to be a 'register_db_to_save valet'
# which may wish to consider putting back in.
if grep -q 'connection *= *mongo' /etc/valet/valet.conf; then
    mongodump --db valet --out $SAVE_DIR/valet-dump.$BASE_RELEASE
fi

# Upgrade Valet
# =============
# Locate valet devstack plugin, the directory above the
# grenade plugin.
VALET_DEVSTACK_DIR=$(dirname $(dirname $0))

# Get functions from current DevStack
source $TARGET_DEVSTACK_DIR/functions
source $TARGET_DEVSTACK_DIR/stackrc
source $TARGET_DEVSTACK_DIR/lib/apache

# Get valet functions from devstack plugin
source $VALET_DEVSTACK_DIR/settings

# Print the commands being run so that we can see the command that triggers
# an error.
set -o xtrace

# Install the target valet
source $VALET_DEVSTACK_DIR/plugin.sh stack install

# calls upgrade-valet for specific release
upgrade_project valet $RUN_DIR $BASE_DEVSTACK_BRANCH $TARGET_DEVSTACK_BRANCH

# Migrate the database
# NOTE(chdent): As we evolve BIN_DIR is likely to be defined, but
# currently it is not.
VALET_BIN_DIR=$(dirname $(which valet-dbsync))
$VALET_BIN_DIR/valet-dbsync || die $LINENO "DB sync error"

# Start Valet
start_valet

# Note these are process names, not service names
ensure_services_started "valet-polling --polling-namespaces compute" \
                        "valet-polling --polling-namespaces central" \
                        "valet-polling --polling-namespaces ipmi" \
                        valet-agent-notification \
                        valet-alarm-evaluator \
                        valet-alarm-notifier \
                        valet-api \
                        valet-collector

# Save mongodb state (replace with snapshot)
if grep -q 'connection *= *mongo' /etc/valet/valet.conf; then
    mongodump --db valet --out $SAVE_DIR/valet-dump.$TARGET_RELEASE
fi


set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End $0"
echo "*********************************************************************"
