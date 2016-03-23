=======
Allegro
=======

Allegro (part of the Valet service suite, along with Ostro) gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Allegro provides an api service, plus OpenStack Heat resource plugins. Allegro can also interact with QoS services including Tegu and IOArbiter.

**IMPORTANT**: `AT&T AIC Installation`_ is covered in a separate document.

Prerequisites
-------------

Prior to installation:

- Ubuntu 14.04 LTS
- Python 2.7.6 with pip
- Music 6.0
- `Ostro`_ 2.0
- `Tegu`_ (QoSLite) if VM-to-VM QoS is required
- `IOArbiter`_ if VM-to-Volume QoS is required

Allegro installation consists of two components:

- allegro-openstack (formerly qosorch)
- allegro-api (formerly allegro)

Allegro is compatible with OpenStack heat-kilo, cinder-juno, and nova-juno.

Throughout this document, the following installation-specific items are used:

- ``$ALLEGRO_HOST``: allegro-api hostname or FQDN
- ``$ALLEGRO_PATH``: Allegro git repository filesystem path
- ``$ALLEGRO_DBPASS``: Allegro database password
- ``$APACHE2_CONFIG_PATH``: apache2 httpd server configuration path
- ``$CODECLOUD_USER``: AT&T CodeCloud user id
- ``$CONTROLLER``: OpenStack controller node hostname or FQDN
- ``$DESIRED_ID``: Desired allegro Ubuntu user and group id
- ``$IOARBITER_HOST``: IOArbiter API hostname or FQDN
- ``$PATH_TO_VENV``: Allegro API virtual environment path
- ``$TEGU_HOST``: Tegu API hostname or FQDN

Root or sudo privileges are required for some steps.

A Note About Python Virtual Environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is recommended to install allegro-api within a python `virtual environment`_ (venv). This avoids instabilities and conflicts within the default Python environment.

As allegro-openstack works in concert with OpenStack services, it must be installed in the same venv used by heat, cinder, and nova, if any. If no venv is used, there is no choice but to install allegro-openstack in the default Python environment.

All other prerequisites will be auto-installed.

Installing Allegro
------------------

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` account with appropriate credentials:

::

  $ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/allegro.git <br>
  $ cd allegro # this is $ALLEGRO_PATH

Both allegro-openstack and allegro-api can be installed in production mode or developer mode.

Install allegro-openstack on an OpenStack controller node containing heat-engine, nova-scheduler, and cinder-scheduler.

::

  production: $ sudo pip install $ALLEGRO_PATH
  developer:  $ sudo pip install --editable $ALLEGRO_PATH

Install allegro-api in the venv on the designated allegro node (which could be the same as the controller node, but doesn't have to be):

::

  $ . $PATH_TO_VENV/bin/activate

  production: (VENV) $ pip install $ALLEGRO_PATH/allegro
  developer:  (VENV) $ pip install --editable $ALLEGRO_PATH/allegro

While the following error might appear when installing allegro-api under python 2.7.6, note that SSL is not currently used by allegro-api.

`InsecurePlatformWarning`_ : A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.

allegro-api SQLAlchemy Setup
----------------------------

**IMPORTANT**: SQLAlchemy can't be used as an ORM engine at this time. This will be re-enabled in the future. It is ok to skip this section.

Create an empty ``allegro`` database (e.g., in mysql) using a suitable password:

::

  $ mysql -u root -p
  mysql> CREATE DATABASE allegro;
  mysql> GRANT ALL PRIVILEGES ON allegro.* TO 'allegro'@'localhost' \
  IDENTIFIED BY '$ALLEGRO_DBPASS';
  mysql> GRANT ALL PRIVILEGES ON allegro.* TO 'allegro'@'%' \
  IDENTIFIED BY '$ALLEGRO_DBPASS';

Edit ``$ALLEGRO_PATH/allegro/config.py`` so that it has matching credentials:

::

  sqlalchemy = {
      'url': 'mysql+pymysql://allegro:$ALLEGRO_DBPASS@$CONTROLLER/allegro?charset=utf8',
      'echo':          True,
      'echo_pool':     True,
      'pool_recycle':  3600,
      'encoding':      'utf-8',
  }

allegro-api Data Store Initialization
-------------------------------------

These steps are used for both SQLAlchemy and Music.

Activate a venv if one is being used, then use pecan to initialize data storage on the allegro node. 

::

  $ . $PATH_TO_VENV/bin/activate

  (VENV) $ cd $ALLEGRO_PATH/allegro
  (VENV) $ pecan populate config.py

Starting allegro-api
--------------------

Development Mode
^^^^^^^^^^^^^^^^

Activate a venv first if necessary, then issue the ``pecan serve`` command:

::

  $ . $PATH_TO_VENV/bin/activate

  (VENV) $ cd $ALLEGRO_PATH/allegro
  (VENV) $ pecan serve config.py

Production Mode
^^^^^^^^^^^^^^^

In production, run allegro-api in a WSGI-compatible environment. The following instructions illustrate this using apache2 httpd.

Install apache2 and mod-wsgi (3.4 at a minimum, 3.5 recommended by the author):

::

  $ sudo apt-get install apache2 libapache2-mod-wsgi

Create the allegro user/group:

::

  $ sudo adduser --gecos "allegro service user" allegro

If the uid/gid assigned by adduser needs to be adjusted:

::

  $ sudo usermod -u $DESIRED_ID -U allegro; sudo groupmod -g $DESIRED_ID allegro

Set up allegro/apache-related directories and ownership:

::

  $ sudo mkdir /var/www/allegro
  $ sudo mkdir /var/log/apache2/allegro
  $ sudo chown -R allegro:allegro /var/log/apache2/allegro /var/www/allegro
  $ sudo cp -p $ALLEGRO_PATH/allegro/app.wsgi $ALLEGRO_PATH/allegro/config.py /var/www/allegro

Setup allegro-api as an apache service:

::

   $ sudo cd $APACHE2_CONFIG_PATH/sites-available
   $ sudo cp -p $ALLEGRO_PATH/allegro/app.apache2 allegro.conf
   $ sudo chown root:root allegro.conf

Note: ``$APACHE2_CONFIG_PATH`` may be ``/opt/apache2`` or ``/etc/apache2`` depending on the installation.

If allegro-api is installed in a venv, append ``python-home=$PATH_TO_VENV`` to ``WSGIDaemonProcess`` within ``allegro.conf``. Apache will then use the correct python environment and libraries.

Alternately, the following line can be added outside of the allegro ``VirtualHost`` directive. Note that this only makes sense if allegro will be the sole focal point of the apache installation as far as venvs are concerned.

::

   WSGIPythonHome $VENV_PATH

Enable allegro-api in apache, test apache to make sure the configuration syntax is valid, then restart:

::

   $ cd $APACHE2_CONFIG_PATH/sites-enabled
   $ sudo ln -s ../sites-available/allegro.conf .
   $ sudo apachectl -t
   Syntax OK
   $ sudo apachectl graceful

Verify allegro-api
------------------

Visit ``http://$ALLEGRO_HOST:8090/v1/`` to check for a response from allegro-api:

::

   {
       "versions": [{
           "status": "CURRENT",
           "id": "v1.0",
           "links": [{
               "href": "http://$ALLEGRO_HOST:8090/v1/",
               "rel": "self"
           }]
       }]
   }

Postman users can import the included Postman collection of sample API calls, located in ``$ALLEGRO_PATH/allegro/allegro/tests/Allegro.json.postman_collection``. Change the URL targets to match ``$ALLEGRO_HOST``.

Resource Plugin Directory
-------------------------

Link to the allegro-openstack resource plugin directory so that heat can locate the allegro plugins:

::

  production: # ln -s /usr/local/etc/heat/resources /usr/lib/heat
  developer:  # ln -s $ALLEGRO_PATH/heat/resources /usr/lib/heat

Alternatively, the heat configuration file can be changed. See the next section.

OpenStack Configuration
-----------------------

allegro-openstack requires edits to the heat, nova, and cinder configuration files, specifically in relation to the heat-engine, nova-scheduler, and cinder-scheduler. It's possible that these services are not all running on the same host. In that case, install allegro-openstack all relevant hosts, editing configuration files as needed on each.

heat.conf
^^^^^^^^^

If the allegro-openstack resource plugin directory is not linked through the filesystem, set the ``plugin_dirs`` option in the ``[DEFAULT]`` section of ``/etc/heat/heat.conf``:

In production mode:

::

  [DEFAULT]
  plugin_dirs = /usr/local/etc/heat/resources

In development mode:

::

  [DEFAULT]
  plugin_dirs = $ALLEGRO_PATH/heat/resources

When using plugin_dirs, take care to include *all* directories being used for plugins, separated by commas. See the OpenStack `heat.conf`_ documentation for more information.

Enable stack lifecycle scheduler hints:

::

   [DEFAULT]
   stack_scheduler_hints = True

If Tegu and IOArbiter are being used, add the following ``[att_qos_pipe]`` section. This will be used by ``ATT::QoS::Pipe`` plugin:

::

   [att_qos_pipe]
   tegu_uri=http://$TEGU_HOST:29444/tegu/api
   ioarbiter_uri=http://$IOARBITER_HOST:7999/v1/ctrl/0/policy

Add an ``[allegro]`` section. This will be used by the allegro-openstack lifecycle plugin:

::

   [allegro]
   allegro_api_server_url = http://$ALLEGRO_HOST:8090/v1

Restart heat-engine

::

   $ sudo service heat-engine restart

Examine ``/var/log/heat/heat-engine.log``. The ``ATT::CloudQoS`` plugins should be found and registered:

::

   INFO heat.engine.environment [-] Registering ATT::CloudQoS::Pipe -> <class 'heat.engine.plugins.resources.ATT.CloudQoS.Reservation.Pipe'>
   INFO heat.engine.environment [-] Registering ATT::CloudQoS::ResourceGroup -> <class 'heat.engine.plugins.resources.ATT.CloudQoS.ResourceGroup.ResourceGroup'>

The heat command line interface (python-heatclient) can also be used to verify that the plugins are available:

::

   $ heat resource-type-list | grep ATT
   | ATT::CloudQoS::Pipe                      |
   | ATT::CloudQoS::ResourceGroup             |

Other ATT plugins will be visible as well. ``ATT::QoS::Pipe`` and ``ATT::QoS::ResourceGroup`` are the plugins most often used.

Note: In future revisions of OpenStack, the heat cli will be superceded by the OpenStack cli (python-openstackclient).

nova.conf
^^^^^^^^^

Edit the ``[DEFAULT]`` section of ``/etc/nova/nova.conf`` so that ``nova-scheduler`` knows how to locate and to use allegro-openstack's scheduler filter.

::

   [DEFAULT]
   scheduler_available_filters = nova.scheduler.filters.all_filters
   scheduler_available_filters = qosorch.openstack.nova.allegro_filter.AllegroFilter
   scheduler_default_filters = RetryFilter, AvailabilityZoneFilter, RamFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter, AllegroFilter

The two ``scheduler_available_filters`` lines are deliberate. The first is required in order for nova to know where to locate its own default filters. For ``scheduler_default_filters``, ensure that ``AllegroFilter`` is placed last so that it has the final say in scheduling.

Next, add an ``[allegro]`` section:

::

   [allegro]
   allegro_api_server_url = http://$ALLEGRO_HOST:8090/v1

Restart nova-scheduler:

::

   $ sudo service nova-scheduler restart

cinder.conf
^^^^^^^^^^^

Edit the ``[DEFAULT]`` section of ``/etc/cinder/cinder.conf`` so that ``cinder-scheduler`` knows to use allegro's scheduler filter.

::

   [DEFAULT]
   scheduler_default_filters = AvailabilityZoneFilter, CapacityFilter, CapabilitiesFilter, AllegroFilter

Unlike nova, cinder automatically knows how to locate allegro-openstack's scheduler filter. For ``scheduler_default_filters``, ensure that ``AllegroFilter`` is placed last so that it has the final say in scheduling.

Next, add an ``[allegro]`` section:

::

   [allegro]
   allegro_api_server_url = http://$ALLEGRO_HOST:8090/v1

Restart cinder-scheduler: 

::

   $ sudo service cinder-scheduler restart

Try It Out
----------

Tire-kick things using these example heat templates:

::

   production: /usr/local/etc/heat/examples
   developer:  $ALLEGRO_PATH/heat/examples

The flavor, ssh key, image, net/subnet IDs, mtu adjustment requirement, and security groups are all specific to the OpenStack installation. It will be necessary to edit various parameters to suit the environment in question.

Contact
-------

Joe D'Andrea <jdandrea@research.att.com>

.. _AT&T AIC Installation: https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/doc/aic/README.rst
.. _Ostro: https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README
.. _Tegu: https://forge.research.att.com/plugins/mediawiki/wiki/qoscloud/index.php/Tegu_Installation_and_Configuration_Guide
.. _IOArbiter: https://forge.research.att.com/plugins/mediawiki/wiki/sds/index.php/IOArbiterInstallationGuide
.. _virtual environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _InsecurePlatformWarning: https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.
.. _heat.conf: http://docs.openstack.org/kilo/config-reference/content/ch_configuring-openstack-orchestration.html
