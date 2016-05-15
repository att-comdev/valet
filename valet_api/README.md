# Valet

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, an optimizer (Ostro), and a set of OpenStack plugins.

This document covers installation of valet-api, the API engine used to interact with Valet.

**IMPORTANT**: [Overall AT&T AIC Installation of Valet is covered in a separate document](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/valet/atRef/refs/heads/master/renderFile/doc/aic/README.md). These instructions are to be used by the Bedminster and Tel Aviv development teams.

## Prerequisites

Prior to installation:

* Ubuntu 14.04 LTS
* Python 2.7.6 with pip
* An OpenStack Kilo cloud
* Music 6.0
* [Ostro](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README) 2.0

Throughout this document, the following installation-specific terms are used:

* ``$CODECLOUD_USER``: AT&T CodeCloud user id
* ``$VENV``: Python virtual environment path (if any)
* ``$VALET_PATH``: Local git repository path
* ``$VALET_HOST``: valet-api hostname or FQDN
* ``$VALET_USERNAME``: OpenStack placement service username (e.g., valet)
* ``$VALET_PASSWORD``: OpenStack placement service password
* ``$VALET_TENANT_NAME``: OpenStack placement service default tenant (e.g., service)
* ``$KEYSTONE_AUTH_API``: Keystone Auth API publicurl endpoint
* ``$VALET_CONFIG_PATH``: Valet configuration directory (e.g., /etc/valet)
* ``$APACHE2_CONFIG_PATH``: apache2 httpd server configuration path

Root or sufficient sudo privileges are required for some steps.

### A Note About Python Virtual Environments

It is recommended to install and configure valet-api witin a python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (venv), This helps avoid instabilities and conflicts within the default python environment.

## Installation

valet-api is maintained in AT&T CodeCloud under the CloudQoS project, in a repository called 'allegro'.

*Note: Apart from the repository name, the word 'Allegro' is no longer used. Use the word 'Valet' in place of 'Allegro' when referring to components.*

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` account with appropriate credentials:

```bash
$ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/allegro.git
$ cd allegro
```

Install valet-api on a host that can reach all OpenStack Keystone endpoints (public, internal, and admin). This can be a controller node or a separate host. Likewise, valet-api, Ostro, and Music may be installed on the same host or separate hosts.

valet-api can be installed in production mode or development mode.

**Production:**

```bash
$ sudo pip install $VALET_PATH/valet_api
```

**Development:**

```bash
$ sudo pip install --editable $VALET_PATH/valet_api
```

If the following error appears when installing valet-api, and SSL access is required (e.g., if Keystone can only be reached via SSL), use a newer Python 2.7 Ubuntu package.

[InsecurePlatformWarning](https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning): A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.

## User account

Create an ubuntu user/group for the valet service user (usually ``valet``):

```bash
$ sudo adduser --gecos "valet service user" valet
```

If the Ubuntu-assigned uid/gid requires adjustment:

```bash
$ sudo usermod -u $DESIRED_ID -U valet
$ sudo groupmod -g $DESIRED_ID valet
```

## Configuration

Copy ``$VALET_PATH/etc/valet_api/config.py`` to a suitable ``$VALET_CONFIG_PATH`` (e.g., ``/var/www/valet/config.py``). As the config file will contain sensitive passwords, ``$VALET_CONFIG_PATH`` must have limited visibility and be accessible only to the user running valet-api.

Edit the following sections in the ``config.py`` copy. See the [valet-openstack README](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_os/README.md) for additional context around the ``server`` and ``identity`` sections.

*Note: In OpenStack parlance, Valet is canonically referred to as a **placement service**.*

### Server

* Set ``port`` to match the OpenStack Keystone placement service port number (e.g., 8090).

```python
server = {
    'port': '8090',
    'host': '0.0.0.0'
}
```

### Identity

* Set ``username`` and ``password`` to the OpenStack placement service user (e.g., ``valet``).
* Set ``project_name`` to the OpenStack placement service user's tenant name (e.g., ``service``).
* Set ``auth_url`` to the Keystone API publicurl endpoint.

```python
identity = {
    'config': {
        'username': '$VALET_USERNAME',
        'password': '$VALET_PASSWORD',
        'project_name': '$VALET_TENANT_NAME',
        'auth_url': '$KEYSTONE_AUTH_API',
    }
}
```

After authenticating via Keystone's publicurl endpoint, valet-api uses Keystone's adminurl endpoint for further API calls. Access to the adminurl endpoint is required for:

* AuthN of OpenStack users for valet-api access, presently limited to users with an ``admin`` role. Formal RBAC support is expected in a future release through oslo-policy.
* Obtaining a list of all OpenStack cloud tenants (used by Valet Groups).

If the Keystone adminurl endpoint is not reachable, Valet will not be able to obtain a complete tenant list. To mitigate:

* Add an additional identity config setting named ``'interface'``, set to ``'public'``.
* In the OpenStack cloud, ensure ``$VALET_USERNAME`` is a member of every tenant. Keep current as needed.

### Music

* Set ``host``, ``port``, ``keyspace``, and ``replication_factor`` as needed for access to Music.
* Alternately, set ``hosts`` (plural) to a python list of hosts if more than one host is used.

```python
music = {
    'host': '127.0.0.1',
    'port': '8080',
    'keyspace': 'valet',
    'replication_factor': 3,
}
```

*Notes: If ``host`` and ``hosts`` are both set, ``host`` is used and ``hosts`` is ignored. Music does not use AuthN or AuthZ at this time.*

## Data Storage Initialization

Use the ``pecan populate`` command to initialize data storage:

```bash
$ pecan populate $VALET_CONFIG_PATH/config.py
```

Any previously created tables will be left as-is and not deleted/re-created.

*Note: Music does not support migrations. If necessary, schema changes in future versions will be noted here with specific upgrade instructions.*

## Running

Use the ``pecan serve`` command to run valet-api and verify installation.

```bash
$ pecan serve $VALET_CONFIG_PATH/config.py
```

Do not use this command to run valet-api in a production environment. A number of production-quality WSGI-compatible environments are available (e.g., apache2 httpd)..

## Configuring apache2 httpd for valet-api

### Prerequisites

* apache2 httpd
* libapache2-mod-wsgi (3.4 at a minimum, 3.5 recommended by the author)
* A ``valet`` service user account/group on the host where valet-api is installed (usually ``valet``).

### Configuration

Set up directories and ownership. ``$VALET_CONFIG_PATH`` is usually set to ``/var/www/valet``.

```bash
$ sudo mkdir $VALET_CONFIG_PATH
$ sudo mkdir /var/log/apache2/valet
$ sudo cp -p $VALET_PATH/etc/valet_api/app.wsgi $VALET_PATH/etc/valet_api/config.py $VALET_CONFIG_PATH
$ sudo chown -R valet:valet /var/log/apache2/valet $VALET_CONFIG_PATH
```

Set up valet-api as a site. ``$APACHE2_CONFIG_PATH`` may be ``/opt/apache2`` or ``/etc/apache2`` depending on the installation.

```bash
$ sudo cd $APACHE2_CONFIG_PATH/sites-available
$ sudo cp -p $VALET_PATH/etc/valet_api/app.apache2 valet.conf
$ sudo chown root:root valet.conf
```

If valet-api was installed in a python virtual environment, append ``python-home=$VENV`` to ``WSGIDaemonProcess`` within ``valet.conf``. Apache will then use the correct python environment and libraries.

Enable valet-api, ensure the configuration syntax is valid, then restart:

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

[Postman](http://www.getpostman.com/) users can import the included collection of sample API calls, located in ``$VALET_PATH/valet_api/valet_api/tests/Valet.json.postman_collection``. Change the URL targets to match ``$VALET_HOST``.

## Usage

See the ``doc`` directory for [API documentation](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_api/doc/README.md).

## Uninstallation

Activate a virtual environment (venv) first if necessary. Uninstallation uses the same command regardless of development or production mode.

```bash
$ sudo pip uninstall valet-api
```

Remove previously made configuration file changes, OpenStack user accounts, and other settings as needed.

## Contact

Joe D'Andrea <jdandrea@research.att.com>
