# Install and start **Valet** service in devstack
#
# To enable Valet in devstack add an entry to local.conf that
# looks like
#
# [[local|localrc]]
# enable_plugin valet git://git.openstack.org/openstack/valet
#
# By default all valet services are started (see
# devstack/settings). To disable a specific service use the
# disable_service function. For example to turn off alarming:
#
# disable_service valet-alarm-notifier valet-alarm-evaluator
#
# NOTE: Currently, there are two ways to get the IPMI based meters in
# OpenStack. One way is to configure Ironic conductor to report those meters
# for the nodes managed by Ironic and to have Valet notification
# agent to collect them. Ironic by default does NOT enable that reporting
# functionality. So in order to do so, users need to set the option of
# conductor.send_sensor_data to true in the ironic.conf configuration file
# for the Ironic conductor service, and also enable the
# valet-anotification service. If you do this disable the IPMI
# polling agent:
#
# disable_service valet-aipmi
#
# The other way is to use Valet ipmi agent only to get the IPMI based
# meters. To avoid duplicated meters, users need to make sure to set the
# option of conductor.send_sensor_data to false in the ironic.conf
# configuration file if the node on which Valet ipmi agent is running
# is also managed by Ironic.
#
# Several variables set in the localrc section adjust common behaviors
# of Valet (see within for additional settings):
#
#   VALET_PIPELINE_INTERVAL:  Seconds between pipeline processing runs. Default 600.
#   VALET_BACKEND:            Database backend (e.g. 'mysql', 'mongodb', 'es')
#   VALET_COORDINATION_URL:   URL for group membership service provided by tooz.
#   VALET_EVENTS:             Set to True to enable event collection
#   VALET_EVENT_ALARM:        Set to True to enable publisher for event alarming

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

# Support potential entry-points console scripts in VENV or not
if [[ ${USE_VENV} = True ]]; then
    PROJECT_VENV["valet"]=${VALET_DIR}.venv
    VALET_BIN_DIR=${PROJECT_VENV["valet"]}/bin
else
    VALET_BIN_DIR=$(get_python_exec_prefix)
fi

# Test if any Valet services are enabled
# is_valet_enabled
function is_valet_enabled {
    [[ ,${ENABLED_SERVICES} =~ ,"valet-" ]] && return 0
    return 1
}

function valet_service_url {
    echo "$VALET_SERVICE_PROTOCOL://$VALET_SERVICE_HOST:$VALET_SERVICE_PORT"
}


# _valet_install_mongdb - Install mongodb and python lib.
function _valet_install_mongodb {
    # Server package is the same on all
    local packages=mongodb-server

    if is_fedora; then
        # mongodb client
        packages="${packages} mongodb"
    fi

    install_package ${packages}

    if is_fedora; then
        restart_service mongod
    else
        restart_service mongodb
    fi

    # give time for service to restart
    sleep 5
}

# _valet_install_redis() - Install the redis server and python lib.
function _valet_install_redis {
    if is_ubuntu; then
        install_package redis-server
        restart_service redis-server
    else
        # This will fail (correctly) where a redis package is unavailable
        install_package redis
        restart_service redis
    fi

    pip_install_gr redis
}

# Configure mod_wsgi
function _valet_config_apache_wsgi {
    sudo mkdir -p $VALET_WSGI_DIR

    local valet_apache_conf=$(apache_site_config_for valet)
    local apache_version=$(get_apache_version)
    local venv_path=""

    # Copy proxy vhost and wsgi file
    sudo cp $VALET_DIR/valet/api/app.wsgi $VALET_WSGI_DIR/app

    if [[ ${USE_VENV} = True ]]; then
        venv_path="python-path=${PROJECT_VENV["valet"]}/lib/$(python_version)/site-packages"
    fi

    sudo cp $VALET_DIR/devstack/apache-valet.template $valet_apache_conf
    sudo sed -e "
        s|%PORT%|$VALET_SERVICE_PORT|g;
        s|%APACHE_NAME%|$APACHE_NAME|g;
        s|%WSGIAPP%|$VALET_WSGI_DIR/app|g;
        s|%USER%|$STACK_USER|g;
        s|%VIRTUALENV%|$venv_path|g
    " -i $valet_apache_conf
}

# Install required services for coordination
function _valet_prepare_coordination {
    if echo $VALET_COORDINATION_URL | grep -q '^memcached:'; then
        install_package memcached
    elif echo $VALET_COORDINATION_URL | grep -q '^redis:'; then
        _valet_install_redis
    fi
}

# Install required services for storage backends
function _valet_prepare_storage_backend {
    if [ "$VALET_BACKEND" = 'mongodb' ] ; then
        pip_install_gr pymongo
        _valet_install_mongodb
    fi

    if [ "$VALET_BACKEND" = 'es' ] ; then
        ${TOP_DIR}/pkg/elasticsearch.sh download
        ${TOP_DIR}/pkg/elasticsearch.sh install
    fi
}


# Install the python modules for inspecting nova virt instances
function _valet_prepare_virt_drivers {
    # Only install virt drivers if we're running nova compute
    if is_service_enabled n-cpu ; then
        if [[ "$VIRT_DRIVER" = 'libvirt' ]]; then
            pip_install_gr libvirt-python
        fi

        if [[ "$VIRT_DRIVER" = 'vsphere' ]]; then
            pip_install_gr oslo.vmware
        fi
    fi
}


# Create valet related accounts in Keystone
function _valet_create_accounts {
    if is_service_enabled valet-api; then

        create_service_user "valet" "admin"

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
            get_or_create_service "valet" "metering" "OpenStack Telemetry Service"
            get_or_create_endpoint "metering" \
                "$REGION_NAME" \
                "$(valet_service_url)/" \
                "$(valet_service_url)/" \
                "$(valet_service_url)/"
        fi
        if is_service_enabled swift; then
            # Valet needs ResellerAdmin role to access Swift account stats.
            get_or_add_user_project_role "ResellerAdmin" "valet" $SERVICE_TENANT_NAME
        fi
    fi
}

# Activities to do before valet has been installed.
function preinstall_valet {
    echo_summary "Preinstall not in virtualenv context. Skipping."
}

# Remove WSGI files, disable and remove Apache vhost file
function _valet_cleanup_apache_wsgi {
    sudo rm -f $VALET_WSGI_DIR/*
    sudo rm -f $(apache_site_config_for valet)
}

# cleanup_valet() - Remove residual data files, anything left over
# from previous runs that a clean run would need to clean up
function cleanup_valet {
    if [ "$VALET_BACKEND" = 'mongodb' ] ; then
        mongo valet --eval "db.dropDatabase();"
    elif [ "$VALET_BACKEND" = 'es' ] ; then
        curl -XDELETE "localhost:9200/events_*"
    fi
    if [ "$VALET_USE_MOD_WSGI" == "True" ]; then
        _valet_cleanup_apache_wsgi
    fi
}

# Set configuration for storage backend.
function _valet_configure_storage_backend {
    if [ "$VALET_BACKEND" = 'mysql' ] || [ "$VALET_BACKEND" = 'postgresql' ] ; then
        iniset $VALET_CONF database alarm_connection $(database_connection_url valet)
        iniset $VALET_CONF database event_connection $(database_connection_url valet)
        iniset $VALET_CONF database metering_connection $(database_connection_url valet)
        iniset $VALET_CONF DEFAULT collector_workers $API_WORKERS
    elif [ "$VALET_BACKEND" = 'es' ] ; then
        # es is only supported for events. we will use sql for alarming/metering.
        iniset $VALET_CONF database alarm_connection $(database_connection_url valet)
        iniset $VALET_CONF database event_connection es://localhost:9200
        iniset $VALET_CONF database metering_connection $(database_connection_url valet)
        iniset $VALET_CONF DEFAULT collector_workers $API_WORKERS
        ${TOP_DIR}/pkg/elasticsearch.sh start
        cleanup_valet
    elif [ "$VALET_BACKEND" = 'mongodb' ] ; then
        iniset $VALET_CONF database alarm_connection mongodb://localhost:27017/valet
        iniset $VALET_CONF database event_connection mongodb://localhost:27017/valet
        iniset $VALET_CONF database metering_connection mongodb://localhost:27017/valet
        cleanup_valet
    else
        die $LINENO "Unable to configure unknown VALET_BACKEND $VALET_BACKEND"
    fi
}

# Configure Valet
function configure_valet {

    iniset_rpc_backend valet $VALET_CONF

    iniset $VALET_CONF DEFAULT notification_topics "$VALET_NOTIFICATION_TOPICS"
    iniset $VALET_CONF DEFAULT verbose True
    iniset $VALET_CONF DEFAULT debug "$ENABLE_DEBUG_LOG_LEVEL"

    if [[ -n "$VALET_COORDINATION_URL" ]]; then
        iniset $VALET_CONF coordination backend_url $VALET_COORDINATION_URL
        iniset $VALET_CONF compute workload_partitioning True
    fi

    # Install the policy file for the API server
    cp $VALET_DIR/etc/valet/policy.json $VALET_CONF_DIR
    iniset $VALET_CONF oslo_policy policy_file $VALET_CONF_DIR/policy.json

    cp $VALET_DIR/etc/valet/pipeline.yaml $VALET_CONF_DIR
    cp $VALET_DIR/etc/valet/event_pipeline.yaml $VALET_CONF_DIR
    cp $VALET_DIR/etc/valet/api_paste.ini $VALET_CONF_DIR
    cp $VALET_DIR/etc/valet/event_definitions.yaml $VALET_CONF_DIR
    cp $VALET_DIR/etc/valet/gnocchi_archive_policy_map.yaml $VALET_CONF_DIR
    cp $VALET_DIR/etc/valet/gnocchi_resources.yaml $VALET_CONF_DIR

    if [ "$VALET_PIPELINE_INTERVAL" ]; then
        sed -i "s/interval:.*/interval: ${VALET_PIPELINE_INTERVAL}/" $VALET_CONF_DIR/pipeline.yaml
    fi
    if [ "$VALET_EVENT_ALARM" == "True" ]; then
        if ! grep -q '^ *- notifier://?topic=alarm.all$' $VALET_CONF_DIR/event_pipeline.yaml; then
            sed -i '/^ *publishers:$/,+1s|^\( *\)-.*$|\1- notifier://?topic=alarm.all\n&|' $VALET_CONF_DIR/event_pipeline.yaml
        fi
    fi

    # The compute and central agents need these credentials in order to
    # call out to other services' public APIs.
    # The alarm evaluator needs these options to call valet APIs
    iniset $VALET_CONF service_credentials os_username valet
    iniset $VALET_CONF service_credentials os_password $SERVICE_PASSWORD
    iniset $VALET_CONF service_credentials os_tenant_name $SERVICE_TENANT_NAME
    iniset $VALET_CONF service_credentials os_region_name $REGION_NAME
    iniset $VALET_CONF service_credentials os_auth_url $KEYSTONE_SERVICE_URI/v2.0

    configure_auth_token_middleware $VALET_CONF valet $VALET_AUTH_CACHE_DIR

    iniset $VALET_CONF notification store_events $VALET_EVENTS

    # Configure storage
    _valet_configure_storage_backend

    if [[ "$VIRT_DRIVER" = 'vsphere' ]]; then
        iniset $VALET_CONF DEFAULT hypervisor_inspector vsphere
        iniset $VALET_CONF vmware host_ip "$VMWAREAPI_IP"
        iniset $VALET_CONF vmware host_username "$VMWAREAPI_USER"
        iniset $VALET_CONF vmware host_password "$VMWAREAPI_PASSWORD"
    fi

    # NOTE: This must come after database configurate as those can
    # call cleanup_valet which will wipe the WSGI config.
    if [ "$VALET_USE_MOD_WSGI" == "True" ]; then
        iniset $VALET_CONF api pecan_debug "False"
        _valet_config_apache_wsgi
    fi

    if is_service_enabled valet-aipmi; then
        # Configure rootwrap for the ipmi agent
        configure_rootwrap valet
    fi
}

# init_valet() - Initialize etc.
function init_valet {
    # Get valet keystone settings in place
    _valet_create_accounts
    # Create cache dir
    sudo install -d -o $STACK_USER $VALET_AUTH_CACHE_DIR
    rm -f $VALET_AUTH_CACHE_DIR/*

    if is_service_enabled mysql postgresql; then
        if [ "$VALET_BACKEND" = 'mysql' ] || [ "$VALET_BACKEND" = 'postgresql' ] || [ "$VALET_BACKEND" = 'es' ] ; then
            recreate_database valet
            $VALET_BIN_DIR/valet-dbsync
        fi
    fi
}

# Install Valet.
# The storage and coordination backends are installed here because the
# virtualenv context is active at this point and python drivers need to be
# installed. The context is not active during preinstall (when it would
# otherwise makes sense to do the backend services).
function install_valet {
    _valet_prepare_coordination
    _valet_prepare_storage_backend
    _valet_prepare_virt_drivers
    install_valetclient
    setup_develop $VALET_DIR
    sudo install -d -o $STACK_USER -m 755 $VALET_CONF_DIR $VALET_API_LOG_DIR
}

# install_valetclient() - Collect source and prepare
function install_valetclient {
    if use_library_from_git "python-valetclient"; then
        git_clone_by_name "python-valetclient"
        setup_dev_lib "python-valetclient"
        sudo install -D -m 0644 -o $STACK_USER {${GITDIR["python-valetclient"]}/tools/,/etc/bash_completion.d/}valet.bash_completion
    else
        pip_install_gr python-valetclient
    fi
}

# start_valet() - Start running processes, including screen
function start_valet {
    run_process valet-acentral "$VALET_BIN_DIR/valet-polling --polling-namespaces central --config-file $VALET_CONF"
    run_process valet-anotification "$VALET_BIN_DIR/valet-agent-notification --config-file $VALET_CONF"
    run_process valet-aipmi "$VALET_BIN_DIR/valet-polling --polling-namespaces ipmi --config-file $VALET_CONF"

    if [[ "$VALET_USE_MOD_WSGI" == "False" ]]; then
        run_process valet-api "$VALET_BIN_DIR/valet-api -d -v --log-dir=$VALET_API_LOG_DIR --config-file $VALET_CONF"
    else
        enable_apache_site valet
        restart_apache_server
        tail_log valet /var/log/$APACHE_NAME/valet.log
        tail_log valet-api /var/log/$APACHE_NAME/valet_access.log
    fi

    # run the the collector after restarting apache as it needs
    # operational keystone if using gnocchi
    run_process valet-collector "$VALET_BIN_DIR/valet-collector --config-file $VALET_CONF"

    # Start the compute agent late to allow time for the collector to
    # fully wake up and connect to the message bus. See bug #1355809
    if [[ "$VIRT_DRIVER" = 'libvirt' ]]; then
        run_process valet-acompute "$VALET_BIN_DIR/valet-polling --polling-namespaces compute --config-file $VALET_CONF" $LIBVIRT_GROUP
    fi
    if [[ "$VIRT_DRIVER" = 'vsphere' ]]; then
        run_process valet-acompute "$VALET_BIN_DIR/valet-polling --polling-namespaces compute --config-file $VALET_CONF"
    fi

    # Only die on API if it was actually intended to be turned on
    if is_service_enabled valet-api; then
        echo "Waiting for valet-api to start..."
        if ! wait_for_service $SERVICE_TIMEOUT $(valet_service_url)/v2/; then
            die $LINENO "valet-api did not start"
        fi
    fi

    run_process valet-alarm-notifier "$VALET_BIN_DIR/valet-alarm-notifier --config-file $VALET_CONF"
    run_process valet-alarm-evaluator "$VALET_BIN_DIR/valet-alarm-evaluator --config-file $VALET_CONF"
}

# stop_valet() - Stop running processes
function stop_valet {
    if [ "$VALET_USE_MOD_WSGI" == "True" ]; then
        disable_apache_site valet
        restart_apache_server
    fi
    # Kill the valet screen windows
    for serv in valet-acompute valet-acentral valet-aipmi valet-anotification valet-collector valet-api valet-alarm-notifier valet-alarm-evaluator; do
        stop_process $serv
    done
}

# This is the main for plugin.sh
if is_service_enabled valet; then
    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # Set up other services
        echo_summary "Configuring system services for Valet"
        preinstall_valet
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Valet"
        # Use stack_install_service here to account for vitualenv
        stack_install_service valet
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Valet"
        configure_valet
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Valet"
        # Tidy base for valet
        init_valet
        # Start the services
        start_valet
    fi

    if [[ "$1" == "unstack" ]]; then
        echo_summary "Shutting Down Valet"
        stop_valet
    fi

    if [[ "$1" == "clean" ]]; then
        echo_summary "Cleaning Valet"
        cleanup_valet
    fi
fi

# Restore xtrace
$XTRACE
