# Install and start **Allegro** service in devstack
#
# To enable Allegro in devstack add an entry to local.conf that
# looks like
#
# [[local|localrc]]
# enable_plugin allegro git://git.openstack.org/openstack/allegro
#
# By default all allegro services are started (see
# devstack/settings). To disable a specific service use the
# disable_service function. For example to turn off alarming:
#
# disable_service allegro-alarm-notifier allegro-alarm-evaluator
#
# NOTE: Currently, there are two ways to get the IPMI based meters in
# OpenStack. One way is to configure Ironic conductor to report those meters
# for the nodes managed by Ironic and to have Allegro notification
# agent to collect them. Ironic by default does NOT enable that reporting
# functionality. So in order to do so, users need to set the option of
# conductor.send_sensor_data to true in the ironic.conf configuration file
# for the Ironic conductor service, and also enable the
# allegro-anotification service. If you do this disable the IPMI
# polling agent:
#
# disable_service allegro-aipmi
#
# The other way is to use Allegro ipmi agent only to get the IPMI based
# meters. To avoid duplicated meters, users need to make sure to set the
# option of conductor.send_sensor_data to false in the ironic.conf
# configuration file if the node on which Allegro ipmi agent is running
# is also managed by Ironic.
#
# Several variables set in the localrc section adjust common behaviors
# of Allegro (see within for additional settings):
#
#   ALLEGRO_PIPELINE_INTERVAL:  Seconds between pipeline processing runs. Default 600.
#   ALLEGRO_BACKEND:            Database backend (e.g. 'mysql', 'mongodb', 'es')
#   ALLEGRO_COORDINATION_URL:   URL for group membership service provided by tooz.
#   ALLEGRO_EVENTS:             Set to True to enable event collection
#   ALLEGRO_EVENT_ALARM:        Set to True to enable publisher for event alarming

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

# Support potential entry-points console scripts in VENV or not
if [[ ${USE_VENV} = True ]]; then
    PROJECT_VENV["allegro"]=${ALLEGRO_DIR}.venv
    ALLEGRO_BIN_DIR=${PROJECT_VENV["allegro"]}/bin
else
    ALLEGRO_BIN_DIR=$(get_python_exec_prefix)
fi

# Test if any Allegro services are enabled
# is_allegro_enabled
function is_allegro_enabled {
    [[ ,${ENABLED_SERVICES} =~ ,"allegro-" ]] && return 0
    return 1
}

function allegro_service_url {
    echo "$ALLEGRO_SERVICE_PROTOCOL://$ALLEGRO_SERVICE_HOST:$ALLEGRO_SERVICE_PORT"
}


# _allegro_install_mongdb - Install mongodb and python lib.
function _allegro_install_mongodb {
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

# _allegro_install_redis() - Install the redis server and python lib.
function _allegro_install_redis {
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
function _allegro_config_apache_wsgi {
    sudo mkdir -p $ALLEGRO_WSGI_DIR

    local allegro_apache_conf=$(apache_site_config_for allegro)
    local apache_version=$(get_apache_version)
    local venv_path=""

    # Copy proxy vhost and wsgi file
    sudo cp $ALLEGRO_DIR/allegro/api/app.wsgi $ALLEGRO_WSGI_DIR/app

    if [[ ${USE_VENV} = True ]]; then
        venv_path="python-path=${PROJECT_VENV["allegro"]}/lib/$(python_version)/site-packages"
    fi

    sudo cp $ALLEGRO_DIR/devstack/apache-allegro.template $allegro_apache_conf
    sudo sed -e "
        s|%PORT%|$ALLEGRO_SERVICE_PORT|g;
        s|%APACHE_NAME%|$APACHE_NAME|g;
        s|%WSGIAPP%|$ALLEGRO_WSGI_DIR/app|g;
        s|%USER%|$STACK_USER|g;
        s|%VIRTUALENV%|$venv_path|g
    " -i $allegro_apache_conf
}

# Install required services for coordination
function _allegro_prepare_coordination {
    if echo $ALLEGRO_COORDINATION_URL | grep -q '^memcached:'; then
        install_package memcached
    elif echo $ALLEGRO_COORDINATION_URL | grep -q '^redis:'; then
        _allegro_install_redis
    fi
}

# Install required services for storage backends
function _allegro_prepare_storage_backend {
    if [ "$ALLEGRO_BACKEND" = 'mongodb' ] ; then
        pip_install_gr pymongo
        _allegro_install_mongodb
    fi

    if [ "$ALLEGRO_BACKEND" = 'es' ] ; then
        ${TOP_DIR}/pkg/elasticsearch.sh download
        ${TOP_DIR}/pkg/elasticsearch.sh install
    fi
}


# Install the python modules for inspecting nova virt instances
function _allegro_prepare_virt_drivers {
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


# Create allegro related accounts in Keystone
function _allegro_create_accounts {
    if is_service_enabled allegro-api; then

        create_service_user "allegro" "admin"

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
            get_or_create_service "allegro" "metering" "OpenStack Telemetry Service"
            get_or_create_endpoint "metering" \
                "$REGION_NAME" \
                "$(allegro_service_url)/" \
                "$(allegro_service_url)/" \
                "$(allegro_service_url)/"
        fi
        if is_service_enabled swift; then
            # Allegro needs ResellerAdmin role to access Swift account stats.
            get_or_add_user_project_role "ResellerAdmin" "allegro" $SERVICE_TENANT_NAME
        fi
    fi
}

# Activities to do before allegro has been installed.
function preinstall_allegro {
    echo_summary "Preinstall not in virtualenv context. Skipping."
}

# Remove WSGI files, disable and remove Apache vhost file
function _allegro_cleanup_apache_wsgi {
    sudo rm -f $ALLEGRO_WSGI_DIR/*
    sudo rm -f $(apache_site_config_for allegro)
}

# cleanup_allegro() - Remove residual data files, anything left over
# from previous runs that a clean run would need to clean up
function cleanup_allegro {
    if [ "$ALLEGRO_BACKEND" = 'mongodb' ] ; then
        mongo allegro --eval "db.dropDatabase();"
    elif [ "$ALLEGRO_BACKEND" = 'es' ] ; then
        curl -XDELETE "localhost:9200/events_*"
    fi
    if [ "$ALLEGRO_USE_MOD_WSGI" == "True" ]; then
        _allegro_cleanup_apache_wsgi
    fi
}

# Set configuration for storage backend.
function _allegro_configure_storage_backend {
    if [ "$ALLEGRO_BACKEND" = 'mysql' ] || [ "$ALLEGRO_BACKEND" = 'postgresql' ] ; then
        iniset $ALLEGRO_CONF database alarm_connection $(database_connection_url allegro)
        iniset $ALLEGRO_CONF database event_connection $(database_connection_url allegro)
        iniset $ALLEGRO_CONF database metering_connection $(database_connection_url allegro)
        iniset $ALLEGRO_CONF DEFAULT collector_workers $API_WORKERS
    elif [ "$ALLEGRO_BACKEND" = 'es' ] ; then
        # es is only supported for events. we will use sql for alarming/metering.
        iniset $ALLEGRO_CONF database alarm_connection $(database_connection_url allegro)
        iniset $ALLEGRO_CONF database event_connection es://localhost:9200
        iniset $ALLEGRO_CONF database metering_connection $(database_connection_url allegro)
        iniset $ALLEGRO_CONF DEFAULT collector_workers $API_WORKERS
        ${TOP_DIR}/pkg/elasticsearch.sh start
        cleanup_allegro
    elif [ "$ALLEGRO_BACKEND" = 'mongodb' ] ; then
        iniset $ALLEGRO_CONF database alarm_connection mongodb://localhost:27017/allegro
        iniset $ALLEGRO_CONF database event_connection mongodb://localhost:27017/allegro
        iniset $ALLEGRO_CONF database metering_connection mongodb://localhost:27017/allegro
        cleanup_allegro
    else
        die $LINENO "Unable to configure unknown ALLEGRO_BACKEND $ALLEGRO_BACKEND"
    fi
}

# Configure Allegro
function configure_allegro {

    iniset_rpc_backend allegro $ALLEGRO_CONF

    iniset $ALLEGRO_CONF DEFAULT notification_topics "$ALLEGRO_NOTIFICATION_TOPICS"
    iniset $ALLEGRO_CONF DEFAULT verbose True
    iniset $ALLEGRO_CONF DEFAULT debug "$ENABLE_DEBUG_LOG_LEVEL"

    if [[ -n "$ALLEGRO_COORDINATION_URL" ]]; then
        iniset $ALLEGRO_CONF coordination backend_url $ALLEGRO_COORDINATION_URL
        iniset $ALLEGRO_CONF compute workload_partitioning True
    fi

    # Install the policy file for the API server
    cp $ALLEGRO_DIR/etc/allegro/policy.json $ALLEGRO_CONF_DIR
    iniset $ALLEGRO_CONF oslo_policy policy_file $ALLEGRO_CONF_DIR/policy.json

    cp $ALLEGRO_DIR/etc/allegro/pipeline.yaml $ALLEGRO_CONF_DIR
    cp $ALLEGRO_DIR/etc/allegro/event_pipeline.yaml $ALLEGRO_CONF_DIR
    cp $ALLEGRO_DIR/etc/allegro/api_paste.ini $ALLEGRO_CONF_DIR
    cp $ALLEGRO_DIR/etc/allegro/event_definitions.yaml $ALLEGRO_CONF_DIR
    cp $ALLEGRO_DIR/etc/allegro/gnocchi_archive_policy_map.yaml $ALLEGRO_CONF_DIR
    cp $ALLEGRO_DIR/etc/allegro/gnocchi_resources.yaml $ALLEGRO_CONF_DIR

    if [ "$ALLEGRO_PIPELINE_INTERVAL" ]; then
        sed -i "s/interval:.*/interval: ${ALLEGRO_PIPELINE_INTERVAL}/" $ALLEGRO_CONF_DIR/pipeline.yaml
    fi
    if [ "$ALLEGRO_EVENT_ALARM" == "True" ]; then
        if ! grep -q '^ *- notifier://?topic=alarm.all$' $ALLEGRO_CONF_DIR/event_pipeline.yaml; then
            sed -i '/^ *publishers:$/,+1s|^\( *\)-.*$|\1- notifier://?topic=alarm.all\n&|' $ALLEGRO_CONF_DIR/event_pipeline.yaml
        fi
    fi

    # The compute and central agents need these credentials in order to
    # call out to other services' public APIs.
    # The alarm evaluator needs these options to call allegro APIs
    iniset $ALLEGRO_CONF service_credentials os_username allegro
    iniset $ALLEGRO_CONF service_credentials os_password $SERVICE_PASSWORD
    iniset $ALLEGRO_CONF service_credentials os_tenant_name $SERVICE_TENANT_NAME
    iniset $ALLEGRO_CONF service_credentials os_region_name $REGION_NAME
    iniset $ALLEGRO_CONF service_credentials os_auth_url $KEYSTONE_SERVICE_URI/v2.0

    configure_auth_token_middleware $ALLEGRO_CONF allegro $ALLEGRO_AUTH_CACHE_DIR

    iniset $ALLEGRO_CONF notification store_events $ALLEGRO_EVENTS

    # Configure storage
    _allegro_configure_storage_backend

    if [[ "$VIRT_DRIVER" = 'vsphere' ]]; then
        iniset $ALLEGRO_CONF DEFAULT hypervisor_inspector vsphere
        iniset $ALLEGRO_CONF vmware host_ip "$VMWAREAPI_IP"
        iniset $ALLEGRO_CONF vmware host_username "$VMWAREAPI_USER"
        iniset $ALLEGRO_CONF vmware host_password "$VMWAREAPI_PASSWORD"
    fi

    # NOTE: This must come after database configurate as those can
    # call cleanup_allegro which will wipe the WSGI config.
    if [ "$ALLEGRO_USE_MOD_WSGI" == "True" ]; then
        iniset $ALLEGRO_CONF api pecan_debug "False"
        _allegro_config_apache_wsgi
    fi

    if is_service_enabled allegro-aipmi; then
        # Configure rootwrap for the ipmi agent
        configure_rootwrap allegro
    fi
}

# init_allegro() - Initialize etc.
function init_allegro {
    # Get allegro keystone settings in place
    _allegro_create_accounts
    # Create cache dir
    sudo install -d -o $STACK_USER $ALLEGRO_AUTH_CACHE_DIR
    rm -f $ALLEGRO_AUTH_CACHE_DIR/*

    if is_service_enabled mysql postgresql; then
        if [ "$ALLEGRO_BACKEND" = 'mysql' ] || [ "$ALLEGRO_BACKEND" = 'postgresql' ] || [ "$ALLEGRO_BACKEND" = 'es' ] ; then
            recreate_database allegro
            $ALLEGRO_BIN_DIR/allegro-dbsync
        fi
    fi
}

# Install Allegro.
# The storage and coordination backends are installed here because the
# virtualenv context is active at this point and python drivers need to be
# installed. The context is not active during preinstall (when it would
# otherwise makes sense to do the backend services).
function install_allegro {
    _allegro_prepare_coordination
    _allegro_prepare_storage_backend
    _allegro_prepare_virt_drivers
    install_allegroclient
    setup_develop $ALLEGRO_DIR
    sudo install -d -o $STACK_USER -m 755 $ALLEGRO_CONF_DIR $ALLEGRO_API_LOG_DIR
}

# install_allegroclient() - Collect source and prepare
function install_allegroclient {
    if use_library_from_git "python-allegroclient"; then
        git_clone_by_name "python-allegroclient"
        setup_dev_lib "python-allegroclient"
        sudo install -D -m 0644 -o $STACK_USER {${GITDIR["python-allegroclient"]}/tools/,/etc/bash_completion.d/}allegro.bash_completion
    else
        pip_install_gr python-allegroclient
    fi
}

# start_allegro() - Start running processes, including screen
function start_allegro {
    run_process allegro-acentral "$ALLEGRO_BIN_DIR/allegro-polling --polling-namespaces central --config-file $ALLEGRO_CONF"
    run_process allegro-anotification "$ALLEGRO_BIN_DIR/allegro-agent-notification --config-file $ALLEGRO_CONF"
    run_process allegro-aipmi "$ALLEGRO_BIN_DIR/allegro-polling --polling-namespaces ipmi --config-file $ALLEGRO_CONF"

    if [[ "$ALLEGRO_USE_MOD_WSGI" == "False" ]]; then
        run_process allegro-api "$ALLEGRO_BIN_DIR/allegro-api -d -v --log-dir=$ALLEGRO_API_LOG_DIR --config-file $ALLEGRO_CONF"
    else
        enable_apache_site allegro
        restart_apache_server
        tail_log allegro /var/log/$APACHE_NAME/allegro.log
        tail_log allegro-api /var/log/$APACHE_NAME/allegro_access.log
    fi

    # run the the collector after restarting apache as it needs
    # operational keystone if using gnocchi
    run_process allegro-collector "$ALLEGRO_BIN_DIR/allegro-collector --config-file $ALLEGRO_CONF"

    # Start the compute agent late to allow time for the collector to
    # fully wake up and connect to the message bus. See bug #1355809
    if [[ "$VIRT_DRIVER" = 'libvirt' ]]; then
        run_process allegro-acompute "$ALLEGRO_BIN_DIR/allegro-polling --polling-namespaces compute --config-file $ALLEGRO_CONF" $LIBVIRT_GROUP
    fi
    if [[ "$VIRT_DRIVER" = 'vsphere' ]]; then
        run_process allegro-acompute "$ALLEGRO_BIN_DIR/allegro-polling --polling-namespaces compute --config-file $ALLEGRO_CONF"
    fi

    # Only die on API if it was actually intended to be turned on
    if is_service_enabled allegro-api; then
        echo "Waiting for allegro-api to start..."
        if ! wait_for_service $SERVICE_TIMEOUT $(allegro_service_url)/v2/; then
            die $LINENO "allegro-api did not start"
        fi
    fi

    run_process allegro-alarm-notifier "$ALLEGRO_BIN_DIR/allegro-alarm-notifier --config-file $ALLEGRO_CONF"
    run_process allegro-alarm-evaluator "$ALLEGRO_BIN_DIR/allegro-alarm-evaluator --config-file $ALLEGRO_CONF"
}

# stop_allegro() - Stop running processes
function stop_allegro {
    if [ "$ALLEGRO_USE_MOD_WSGI" == "True" ]; then
        disable_apache_site allegro
        restart_apache_server
    fi
    # Kill the allegro screen windows
    for serv in allegro-acompute allegro-acentral allegro-aipmi allegro-anotification allegro-collector allegro-api allegro-alarm-notifier allegro-alarm-evaluator; do
        stop_process $serv
    done
}

# This is the main for plugin.sh
if is_service_enabled allegro; then
    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # Set up other services
        echo_summary "Configuring system services for Allegro"
        preinstall_allegro
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Allegro"
        # Use stack_install_service here to account for vitualenv
        stack_install_service allegro
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Allegro"
        configure_allegro
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Allegro"
        # Tidy base for allegro
        init_allegro
        # Start the services
        start_allegro
    fi

    if [[ "$1" == "unstack" ]]; then
        echo_summary "Shutting Down Allegro"
        stop_allegro
    fi

    if [[ "$1" == "clean" ]]; then
        echo_summary "Cleaning Allegro"
        cleanup_allegro
    fi
fi

# Restore xtrace
$XTRACE
