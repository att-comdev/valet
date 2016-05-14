# Valet

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, an optimizer (Ostro), and a set of OpenStack plugins. Valet can also interact with QoS services including Tegu and IOArbiter.

**IMPORTANT**: [AT&T AIC Installation is covered in a separate document](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/valet/atRef/refs/heads/master/renderFile/doc/aic/README.md). These instructions are independent of AIC.

## Prerequisites

Prior to installation:

* Ubuntu 14.04 LTS
* Python 2.7.6 with pip
* Music 6.0
* [Ostro](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README) 2.0
* [Tegu](https://forge.research.att.com/plugins/mediawiki/wiki/qoscloud/index.php/Tegu_Installation_and_Configuration_Guide) (QoSLite) if VM-to-VM QoS is required
* [IOArbiter](https://forge.research.att.com/plugins/mediawiki/wiki/sds/index.php/IOArbiterInstallationGuide) if VM-to-Volume QoS is required

Valet installation consists of two components:
* valet-openstack (formerly qosorch)
* valet-api (formerly valet)

Valet is compatible with OpenStack heat-kilo, cinder-juno, and nova-juno.

Throughout this document, the following installation-specific terms are used:

* ``$VALET_HOST``: valet-api hostname or FQDN
* ``$VALET_PATH``: Valet git repository filesystem path
* ``$VALET_DBPASS``: Valet database password
* ``$APACHE2_CONFIG_PATH``: apache2 httpd server configuration path
* ``$CODECLOUD_USER``: AT&T CodeCloud user id
* ``$CONTROLLER``: OpenStack controller node hostname or FQDN
* ``$DESIRED_ID``: Desired valet Ubuntu user and group id
* ``$IOARBITER_HOST``: IOArbiter API hostname or FQDN
* ``$PATH_TO_VENV``: Valet API virtual environment path
* ``$TEGU_HOST``: Tegu API hostname or FQDN
* ``$VALET_TENANT_NAME``: Valet user default project/tenant (e.g., service)
* ``$VALET_USERNAME``: Valet username (e.g., valet)
* ``$VALET_PASSWORD``: Valet user password
* ``$KEYSTONE_AUTH_API``: Keystone Auth API endpoint
* ``$KEYSTONE_REGION``: Keystone Region (e.g., RegionOne)

Root or sudo privileges are required for some steps.

### A Note About Python Virtual Environments

It is recommended to install valet-api within a python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (venv). This avoids instabilities and conflicts within the default Python environment.

As valet-openstack works in concert with OpenStack services, it must be installed in the same venv used by heat, cinder, and nova, if any. If no venv is used, there is no choice but to install valet-openstack in the default Python environment.

All other prerequisites will be auto-installed.

## Installing Valet

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` account with appropriate credentials:

```bash
$ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/valet.git
$ cd valet
```

Both valet-openstack and valet-api can be installed in production mode or developer mode.

Install valet-openstack on an OpenStack controller node containing heat-engine, nova-scheduler, and cinder-scheduler.

Production:

```bash
$ sudo pip install $VALET_PATH
```

Development:

```bash
$ sudo pip install --editable $VALET_PATH
```

Install valet-api in the venv on the designated valet node (which could be the same as the controller node, but doesn't have to be):

Production:

```bash
$ . $PATH_TO_VENV/bin/activate
(VENV) $ pip install $VALET_PATH/valet
```

Development:

```bash
$ . $PATH_TO_VENV/bin/activate
(VENV) $ pip install --editable $VALET_PATH/valet
```

While the following error might appear when installing valet-api under python 2.7.6, note that SSL is not currently used by valet-api.

[InsecurePlatformWarning](https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning): A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.

## valet-api Configuration

**IMPORTANT**: SQLAlchemy can't be used as an ORM engine at this time. This will be re-enabled in the future. It is ok to ignore the SQLAlchemy directives in this section.

Edit ``$VALET_PATH/valet/config.py`` and ensure the ``server``, ``identity``, ``sqlalchemy``, and ``music`` sections reflect the desired configuration settings:

**server**: ``port`` must be the desired port number (usually 8090, but it doesn't have to be).

**identity**: Within the ``config`` subsection, ``username``, ``password``, and ``project_name`` must match those of the designated OpenStack valet user. (``project_name`` is equivalent to ``tenant_name``.) ``auth_url`` must point to the Keystone API endpoint (usually the publicurl).

**sqlalchemy**: ``url``, ``echo``, ``echo_pool``, ``pool_recycle``, and ``encoding`` must match the settings required for access to SQLAlchemy. In particular, the desired valet username/password for database access must be present in the ``url``.

**music**: ``host``, ``port``, ``keyspace``, and ``replication_factor`` must match the settings required for access to Music. If more than one host is desired, set ``hosts`` (plural) to a python list of hosts instead. If ``host`` and ``hosts`` are both set, ``host`` is used and ``hosts`` is ignored.

## valet-api SQLAlchemy Setup

**IMPORTANT**: SQLAlchemy can't be used as an ORM engine at this time. This will be re-enabled in the future. It is ok to skip this section.

Create an empty ``valet`` database (e.g., in mysql) using a suitable password:

```bash
$ mysql -u root -p
mysql> CREATE DATABASE valet;
mysql> GRANT ALL PRIVILEGES ON valet.* TO 'valet'@'localhost' \
IDENTIFIED BY '$VALET_DBPASS';
mysql> GRANT ALL PRIVILEGES ON valet.* TO 'valet'@'%' \
IDENTIFIED BY '$VALET_DBPASS';
```

Edit ``$VALET_PATH/valet/config.py`` so that it has matching credentials:

```python
sqlalchemy = {
    'url': 'mysql+pymysql://valet:$VALET_DBPASS@$CONTROLLER/valet?charset=utf8',
    'echo': True,
    'echo_pool': True,
    'pool_recycle': 3600,
    'encoding': 'utf-8',
}
```

## valet-api Data Store Initialization

These steps are used for both SQLAlchemy and Music.

Activate a venv if one is being used, then use pecan to initialize data storage on the valet node. 

```bash
$ . $PATH_TO_VENV/bin/activate
(VENV) $ cd $VALET_PATH/valet
(VENV) $ pecan populate config.py
```

## Starting valet-api

### Development Mode

Activate a venv first if necessary, then issue the ``pecan serve`` command:

```bash
$ . $PATH_TO_VENV/bin/activate
(VENV) $ cd $VALET_PATH/valet
(VENV) $ pecan serve config.py
```

### Production Mode

In production, run valet-api in a WSGI-compatible environment. The following instructions illustrate this using apache2 httpd.

Install apache2 and mod-wsgi (3.4 at a minimum, 3.5 recommended by the author):

```bash
$ sudo apt-get install apache2 libapache2-mod-wsgi
```

Create the valet user/group:

```bash
$ sudo adduser --gecos "valet service user" valet
```

If the uid/gid assigned by adduser needs to be adjusted:

```bash
$ sudo usermod -u $DESIRED_ID -U valet; sudo groupmod -g $DESIRED_ID valet
```

Set up valet/apache-related directories and ownership:

```bash
$ sudo mkdir /var/www/valet
$ sudo mkdir /var/log/apache2/valet
$ sudo chown -R valet:valet /var/log/apache2/valet /var/www/valet
$ sudo cp -p $VALET_PATH/valet/app.wsgi $VALET_PATH/valet/config.py /var/www/valet
```

Setup valet-api as an apache service:

```bash
$ sudo cd $APACHE2_CONFIG_PATH/sites-available
$ sudo cp -p $VALET_PATH/valet/app.apache2 valet.conf
$ sudo chown root:root valet.conf
```

Note: ``$APACHE2_CONFIG_PATH`` may be ``/opt/apache2`` or ``/etc/apache2`` depending on the installation.

If valet-api is installed in a venv, append ``python-home=$PATH_TO_VENV`` to ``WSGIDaemonProcess`` within ``valet.conf``. Apache will then use the correct python environment and libraries.

Alternately, the following line can be added outside of the valet ``VirtualHost`` directive. Note that this only makes sense if valet will be the sole focal point of the apache installation as far as venvs are concerned.

```conf
WSGIPythonHome $VENV_PATH
```

Enable valet-api in apache, test apache to make sure the configuration syntax is valid, then restart:

```bash
$ cd $APACHE2_CONFIG_PATH/sites-enabled
$ sudo ln -s ../sites-available/valet.conf .
$ sudo apachectl -t
Syntax OK
$ sudo apachectl graceful
```

## Verify valet-api

Visit ``http://$VALET_HOST:8090/v1/`` to check for a response from valet-api:

```json
{
    "versions": [{
        "status": "CURRENT",
        "id": "v1.0",
        "links": [{
            "href": "http://$VALET_HOST:8090/v1/",
            "rel": "self"
        }]
    }]
}
```

Postman users can import the included Postman collection of sample API calls, located in ``$VALET_PATH/valet/valet/tests/Valet.json.postman_collection``. Change the URL targets to match ``$VALET_HOST``.

## Resource Plugin Directory

Link to the valet-openstack resource plugin directory so that heat can locate the valet plugins:

Production:

```bash
# ln -s /usr/local/etc/heat/resources /usr/lib/heat
```

Development:

```bash
# ln -s $VALET_PATH/heat/resources /usr/lib/heat
```

Alternatively, the heat configuration file can be changed. See the next section.

## OpenStack Configuration

valet-openstack requires edits to the heat, nova, and cinder configuration files, specifically in relation to the heat-engine, nova-scheduler, and cinder-scheduler. It's possible that these services are not all running on the same host. In that case, install valet-openstack all relevant hosts, editing configuration files as needed on each.

### Prerequisites

The following keystone commands must be performed with admin credentials.

Add a user ``valet``, giving it an ``admin`` role in the ``service`` project (tenant):

```bash
$ keystone user-create --name valet --pass $VALET_PASSWORD
$ keystone user-role-add --user valet --tenant service --role admin
```

Create the service entity. This is not used by Valet 1.0 but may be added for future use.

```bash
$ keystone service-create --type placement --name valet --description "OpenStack Placement"
```

Create the service API endpoints. This is not used by Valet 1.0 but may be added for future use.

```bash
$ keystone endpoint-create --region $KEYSTONE_REGION --service valet --publicurl 'http://$VALET_HOST:8090/v1' --adminurl 'http://$VALET_HOST:8090/v1' --internalurl 'http://$VALET_HOST:8090/v1'
```

Note that the administrator may choose to use different hostnames/IPs for public vs. admin vs. internal URLs, depending on local architecture and requirements.

Important: valet-api requires line-of-sight to the Keystone adminurl endpoint. If this endpoint is unavailable, valet-api will not be able to obtain a list of all projects (tenants) for use with group management.

To mitigate, edit ``$VALET_PATH/valet/config.py``. In the ``identity`` section, add an additional config setting of ``interface`` and set it to ``'public'``. Next, add the valet user as a member of every project (tenant) it is expected to be aware of.

### heat.conf

Set the ``plugin_dirs`` option in the ``[DEFAULT]`` section of ``/etc/heat/heat.conf``:

Production:

```ini
[DEFAULT]
plugin_dirs = /usr/local/etc/valet_os/heat
```

Development:

```ini
[DEFAULT]
plugin_dirs = $VALET_PATH/valet_os/etc/valet_os/heat
```

If plugin_dirs is already present, separate entries by commas. Order does not matter. See the OpenStack [heat.conf](http://docs.openstack.org/kilo/config-reference/content/ch_configuring-openstack-orchestration.html) documentation for more information.

Enable stack lifecycle scheduler hints:

```ini
[DEFAULT]
stack_scheduler_hints = True
```

If Tegu and IOArbiter are being used, add the following ``[att_qos_pipe]`` section. This will be used by ``ATT::QoS::Pipe`` plugin:

```ini
[att_qos_pipe]
tegu_uri=http://$TEGU_HOST:29444/tegu/api
ioarbiter_uri=http://$IOARBITER_HOST:7999/v1/ctrl/0/policy
```

Add a ``[valet]`` section. This will be used by Valet's heat stack lifecycle plugin:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
```

Restart heat-engine

```bash
$ sudo service heat-engine restart
```

Examine ``/var/log/heat/heat-engine.log``. The ``ATT::Valet`` plugins should be found and registered:

```log
INFO heat.engine.environment [-]  Registered: [Plugin](User:False) ATT::Valet::Pipe -> <class 'heat.engine.plugins.Pipe.Pipe'>
INFO heat.engine.environment [-]  Registered: [Plugin](User:False) ATT::Valet::GroupAssignment -> <class 'heat.engine.plugins.GroupAssignment.GroupAssignment'>
```

The heat command line interface (python-heatclient) can also be used to verify that the plugins are available:

```bash
$ heat resource-type-list | grep ATT
| ATT::Valet::Pipe                         |
| ATT::Valet::GroupAssignment              |
```

### nova.conf

Edit the ``[DEFAULT]`` section of ``/etc/nova/nova.conf`` so that ``nova-scheduler`` knows how to locate and to use valet-openstack's scheduler filter.

```ini
[DEFAULT]
scheduler_available_filters = nova.scheduler.filters.all_filters
scheduler_available_filters = valet_os.nova.valet_filter.ValetFilter
scheduler_default_filters = RetryFilter, AvailabilityZoneFilter, RamFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter, ValetFilter
```

The two ``scheduler_available_filters`` lines are deliberate. The first is required in order for nova to know where to locate its own default filters. For ``scheduler_default_filters``, ensure that ``ValetFilter`` is placed last so that it has the final say in scheduling.

Next, add a ``[valet]`` section:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
admin_tenant_name = $VALET_TENANT_NAME
admin_username = $VALET_USERNAME
admin_password = $VALET_PASSWORD
admin_auth_url = $KEYSTONE_AUTH_API
```

Restart nova-scheduler:

```bash
$ sudo service nova-scheduler restart
```

### cinder.conf

Edit the ``[DEFAULT]`` section of ``/etc/cinder/cinder.conf`` so that ``cinder-scheduler`` knows to use valet's scheduler filter.

```ini
[DEFAULT]
scheduler_default_filters = AvailabilityZoneFilter, CapacityFilter, CapabilitiesFilter, ValetFilter
```

Unlike nova, cinder automatically knows how to locate the Valet scheduler filter. For ``scheduler_default_filters``, ensure that ``ValetFilter`` is placed last so that it has the final say in scheduling.

Next, add a ``[valet]`` section:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
```

Restart cinder-scheduler: 

```bash
$ sudo service cinder-scheduler restart
```

## Try It Out

Tire-kick things using these example heat templates:

Production:

```bash
/usr/local/etc/heat/examples
```

Development:

```bash
$VALET_PATH/heat/examples
```

The flavor, ssh key, image, net/subnet IDs, mtu adjustment requirement, and security groups are all specific to the OpenStack installation. It will be necessary to edit various parameters to suit the environment in question.

## Uninstallation

Activate a venv first if necessary. Use ``pip uninstall`` to uninstall valet-api and valet-openstack (same command for development or production modes). In this example, valet-api is installed in a venv, while valet-openstack is not. Note that venv activation is only during the uninstallation of valet-api.

```bash
$ . $PATH_TO_VENV/bin/activate
(VENV) $ pip uninstall valet-api
(VENV) $ deactivate
$ pip uninstall valet-openstack
```

Remove previously made configuration file changes, symbolic filesystem links, database configurations, user accounts, and other settings as needed.

## Contact

Joe D'Andrea <jdandrea@research.att.com>
