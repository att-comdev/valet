# valet-openstack

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, an optimizer (Ostro), and a set of OpenStack plugins.

This document covers installation of valet-openstack, a set of OpenStack plugins used to interact with Valet.

**IMPORTANT**: [Overall AT&T AIC Installation of Valet is covered in a separate document](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/valet/atRef/refs/heads/master/renderFile/doc/aic/README.md). These instructions are a component of the overall AIC instructions.

## Prerequisites

Prior to installation:

* Ubuntu 14.04 LTS
* Python 2.7.6 with pip

valet-openstack is compatible with OpenStack heat-kilo and nova-juno.

Throughout this document, the following installation-specific terms are used:

* ``$VALET_HOST``: valet-api hostname or FQDN
* ``$VALET_PATH``: Valet git repository filesystem path
* ``$CODECLOUD_USER``: AT&T CodeCloud user id
* ``$VALET_TENANT_NAME``: Valet user default project/tenant (e.g., service)
* ``$VALET_USERNAME``: Valet username (e.g., valet)
* ``$VALET_PASSWORD``: Valet user password
* ``$KEYSTONE_AUTH_API``: Keystone Auth API endpoint
* ``$KEYSTONE_REGION``: Keystone Region (e.g., RegionOne)
* ``$VENV``: Virtual Environment directory (if heat/nova was installed in a venv)

Root or sudo privileges are required for some steps.

### A Note About Python Virtual Environments

As valet-openstack works in concert with OpenStack services, if heat and nova have been installed in a python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (venv), valet-openstack must be installed in the same environment. (A venv helps avoid instabilities and conflicts within the default python environment.)

## Installing valet-openstack

valet-openstack is maintained in AT&T CodeCloud under the ST_CLOUDQOS project in a repository called 'allegro'.

*Note: The name 'Allegro' is no longer used. Apart from the repository name, use 'Valet' in place of 'Allegro' when referring to components.*

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` account with appropriate credentials:

```bash
$ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/allegro.git
$ cd allegro
```

Install valet-openstack on the OpenStack controller node containing heat-engine and nova-scheduler. If these services are distributed across multiple nodes, install valet-openstack on each node.

valet-openstack can be installed in production mode or development mode.

**Production:**

```bash
$ sudo pip install $VALET_PATH/valet_os
```

**Development:**

```bash
$ sudo pip install --editable $VALET_PATH/valet_os
```

## OpenStack Configuration

valet-openstack requires edits to the heat and nova configuration files, and a restart of the heat-engine and nova-scheduler services.

### Prerequisites

The following keystone commands must be performed by an OpenStack cloud administrator.

Add a user ``$VALET_USERNAME``, giving it an ``admin`` role in the ``service`` tenant:

```bash
$ keystone user-create --name $VALET_USERNAME --pass $VALET_PASSWORD
$ keystone user-role-add --user $VALET_USERNAME --tenant service --role admin
```

Create the service entity and API endpoints. While this is not used by Valet 1.0, it is reserved for future use.

```bash
$ keystone service-create --type placement --name valet --description "OpenStack Placement"
$ keystone endpoint-create --region $KEYSTONE_REGION --service valet --publicurl 'http://$VALET_HOST:8090/v1' --adminurl 'http://$VALET_HOST:8090/v1' --internalurl 'http://$VALET_HOST:8090/v1'
```

The administrator may choose to use differing hostnames/IPs for public vs. admin vs. internal URLs, depending on local architecture and requirements.

### Heat

The following changes are made in ``/etc/heat/heat.conf``.

Set the ``plugin_dirs`` option in the ``[DEFAULT]`` section so that Heat can locate and use the Valet Stack Lifecycle Plugin. The directory used depends on how valet-openstack was installed.

**Production:**

```ini
[DEFAULT]
plugin_dirs = /usr/local/etc/valet_os/heat
```

*Note: In Production mode, if a virtual environment is in use, change the path to be relative to the virtual environment's location, e.g. ``$VENV/etc/valet_os/heat``.*

**Development:**

```ini
[DEFAULT]
plugin_dirs = $VALET_PATH/valet_os/etc/valet_os/heat
```

If ``plugin_dirs`` is already present, separate entries by commas. The order of entries does not matter. See the OpenStack [heat.conf](http://docs.openstack.org/kilo/config-reference/content/ch_configuring-openstack-orchestration.html) documentation for more information.

Enable stack lifecycle scheduler hints in the ``[DEFAULT]`` section:

```ini
[DEFAULT]
stack_scheduler_hints = True
```

Add a ``[valet]`` section. This will be used by the Valet Stack Lifecycle Plugin:

```ini
[valet]
url = http://$VALET_HOST:8090/v1
```

Restart heat-engine:

```bash
$ sudo service heat-engine restart
```

Examine the heat-engine log (usually in ``/var/log/heat/heat-engine.log``). The ``ATT::Valet`` plugin should be found and registered:

```log
INFO heat.engine.environment [-]  Registered: [Plugin](User:False) ATT::Valet::GroupAssignment -> <class 'heat.engine.plugins.GroupAssignment.GroupAssignment'>
```

The heat command line interface (python-heatclient) can also be used to verify plugin registration:

```bash
$ heat resource-type-list | grep ATT
| ATT::Valet::GroupAssignment              |
```

### Nova

The following changes are made in ``/etc/nova/nova.conf``.

The ``nova-scheduler`` service requires manual configuration so that Nova can locate and use Valet's Scheduler Filter.

Edit the ``[DEFAULT]`` section so that ``scheduler_available_filters`` and ``scheduler_default_filters`` reference Valet, for example:

```ini
[DEFAULT]
scheduler_available_filters = nova.scheduler.filters.all_filters
scheduler_available_filters = valet_os.nova.valet_filter.ValetFilter
scheduler_default_filters = RetryFilter, AvailabilityZoneFilter, RamFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter, ValetFilter
```

When referring to additional filter plugins, multiple ``scheduler_available_filters`` lines are required. The first line explicitly makes all of nova's default filters available. The second line makes Valet's filter available. Additional lines may be required for additional plugins.

When setting ``scheduler_default_filters``, ensure that ``ValetFilter`` is placed last so that Valet has the final say in scheduling decisions.

Add a ``[valet]`` section. This will be used by the Valet Scheduler Filter:

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

## Uninstallation

Activate a virtual environment (venv) first if necessary. Uninstallation uses the same command regardless of development or production mode.

```bash
$ pip uninstall valet-openstack
```

Remove previously made configuration file changes, OpenStack user accounts, and other settings as needed.

## Contact

Joe D'Andrea <jdandrea@research.att.com>
