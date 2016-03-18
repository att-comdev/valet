=======
Allegro
=======

Allegro (part of the Valet service suite, including Ostro) gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. allegro provides resource plugins to OpenStack Heat for use with QoS services including Tegu and IOArbiter.

IMPORTANT:

- The master branch currently REQUIRES Music 6.0 or higher and Ostro 2.0.
- Please ignore any references to Ostro 1.5 and only follow those for Ostro 2.0.
- SQLAlchemy can't be toggled at this time.

Prerequisites
-------------

Prior to installation:

- Ubuntu 14.04 LTS
- Python 2.7.6 with pip
- `Ostro`_ 1.5 or 2.0
- Music 6.0 or higher (if Ostro 2.0 is used)
- `Tegu`_ (QoSLite) if VM-to-VM QoS is required
- `IOArbiter`_ if VM-to-Volume QoS is required

Root or sudo privileges are required for some operations.

allegro-openstack (qosorch) requires OpenStack Kilo or higher versions of:

- cinder
- heat
- nova

allegro-api (allegro) requires ostro 1.5.

It is recommended that allegro-api be installed in a python virtual environment.

allegro-openstack can be installed in a python virtual environment IF heat is in the same venv. This is not typically the case, but it is possible depending on the particular configuration of heat.

ostro 1.5 requires the libcurl4-openssl-dev package, followed by pycurl.

All other prerequisites will be auto-installed.

Installing Ostro
----------------

Ostro 1.5 and 2.0 are supported. Version 2.0 is strongly recommended.

In the "ostro" section of $ALLEGRO_PATH/allegro/config.py, set the version to 1.5 or 2.0::

::

  ostro = {
      'version': "2.0",
  }


Ostro 2.0
---------

Install Ostro 2.0 following the instructions from the CodeCloud repository.
Music 6.0 or higher is required for Ostro 2.0 as a prerequisite.

Ostro 1.5
---------

Ostro 1.5 is to be installed on the same host and in the same environment as allegro-api.

Ostro 1.5 is delivered in a tar/gzip file without a relative path. On Ubuntu, because ostro is a manual installation, unpack it in python's `site-packages`_ (vs. dist-packages),like so:

::

  $ cd /usr/local/lib/python2.7/site-packages
  $ sudo mkdir ostro15
  $ sudo tar -C ostro15 -xzf $ARCHIVE_PATH/ostro15.tgz

If a virtual environment (venv) is used for allegro-api, install ostro in the venv's site-packages directory instead:

::

  $ cd $VENV_PATH/local/lib/python2.7/site-packages
  $ mkdir ostro15
  $ sudo tar -C ostro15 -xzf $ARCHIVE_PATH/ostro15.tgz

Note that the python library location may vary slightly depending on the venv setup.

In both cases, should this not work for any reason, use dist-packages as a fallback location.

Link ``ostro.auth`` from the ostro 1.5 package directory into ``/etc/ostro/ostro.auth`` (not ostro15.auth):

::

  $ sudo mkdir /etc/ostro; cd /etc/ostro
  $ sudo ln -s $OSTRO_PATH/ostro.auth .

Ostro 1.5 requires the ``tegu_req`` command line interface. It does not call the tegu API. If Tegu is installed on another host, perform the following steps:

* Copy ``/usr/bin/tegu_req`` and ``/usr/bin/rjprt`` from the Tegu host onto the Ostro host.
* Install the korn shell using ``sudo apt-get install ksh``
* Edit ``/usr/bin/tegu_req`` and change the line ``host=localhost:$port`` to use the Tegu FQDN instead of localhost.

Looking forward, once ostro comes with a python setup, it will be automatically installed in the appropriate packages directory. At that time, it is recommended to uninstall this version of Ostro before proceeding. venvs may still use site-packages, however Ubuntu will likely install into dist-packages.

Installing Allegro
------------------

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` with appropriate credentials:

::

  $ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/allegro.git
  $ cd allegro # this is $ALLEGRO_PATH

Both allegro-openstack (qosorch) and allegro-api (allegro) can be installed in production or developer (editable) mode. pip will install any python dependencies required by each.

Install allegro-openstack on an OpenStack controller node containing heat-engine, nova-scheduler, and cinder-scheduler.

::

  production: $ sudo pip install $ALLEGRO_PATH
  developer:  $ sudo pip install --editable $ALLEGRO_PATH

Install allegro-api in the venv on the designated allegro node (which could be the same as the controller node, but doesn't have to be):

::

  $ . $PATH_TO_VENV/bin/activate

  production: (VENV) $ pip install $ALLEGRO_PATH/allegro
  developer:  (VENV) $ pip install --editable $ALLEGRO_PATH/allegro

It is very strongly recommended to create a python `virtual environment`_ (venv) for allegro-api.

For instance, Ubuntu 14.04 uses pecan 0.3.0, which is out of date. Updating an Ubuntu package via pip can lead to instabilities. Uninstalling an Ubuntu package can lead to instabilities in other packages that expect it. Using a venv avoids such conflicts.

(Note: By way of contrast, allegro-openstack works in concert with OpenStack services, and OpenStack is not usually installed using a venv.)

The following error might appear when installing allegro-api under python 2.7.6, however SSL is not currently used by allegro-api.

`InsecurePlatformWarning`_ : A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.

allegro-api SQLAlchemy Setup
----------------------------

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

allegro-api can be started on the allegro node using pecan via the command line. This method is only recommended for development use. Activate a venv first if necessary.

::

  $ . $PATH_TO_VENV/bin/activate

  (VENV) $ cd $ALLEGRO_PATH/allegro
  (VENV) $ pecan serve config.py

Using allegro-api with apache
-----------------------------

Alternatively, allegro-api can be configured to run in apache using the Python WSGI standard. Here's how.

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

Note: Depending on the installation, ``$APACHE2_CONFIG_PATH`` may be ``/opt/apache2`` or ``/etc/apache2``.

If a venv is being used, append ``python-home$PATH_TO_VENV`` to ``WSGIDaemonProcess`` within ``allegro.conf``. This way Apache will use the correct python environment and libraries.

Alternately, the following line can be added outside of the allegro ``VirtualHost`` directive. Note that this only makes sense if allegro will be the sole focal point of the apache installation as far as venvs are concerned.

::

   WSGIPythonHome $VENV_PATH

Enable allegro-api in apache, Test apache to make sure the configuration is valid, then restart:

::

   $ cd $APACHE2_CONFIG_PATH/sites-enabled
   $ sudo ln -s ../sites-available/allegro.conf .
   $ sudo apachectl -t
   Syntax OK
   $ sudo apachectl graceful

Verify allegro-api
------------------

Visit ``http://$CONTROLLER:8090/`` to check for a response.

::

   {
       "versions": [{
           "status": "CURRENT",
           "id": "v1.0",
           "links": [{
               "href": "http://$CONTROLLER:8090/v1/",
               "rel": "self"
           }]
       }]
   }

OpenStack Configuration
-----------------------

allegro-openstack requires adjustments in the heat, nova, and cinder configuration files. This is in relation to the heat-engine, nova-scheduler, and cinder-scheduler services, specifically. It's possible that these services are not all running on the same host. In that case, allegro-openstack should be installed on all relevant hosts. The OpenStack services can then be configured as needed on each.

Heat Configuration
------------------

Link to the allegro-openstack resource plugin directory so that heat can locate the allegro plugins:

::

  production: # ln -s /usr/local/etc/heat/resources /usr/lib/heat
  developer:  # ln -s $ALLEGRO_PATH/heat/resources /usr/lib/heat

Alternatively, set the ``plugin_dirs`` option in the ``[DEFAULT]`` section of ``/etc/heat/heat.conf``:

::

  production: plugin_dirs = /usr/local/etc/heat/resources
  developer:  plugin_dirs = $ALLEGRO_PATH/heat/resources

When using plugin_dirs, take care to include all directories being used for plugins, separated by commas. See the OpenStack `heat.conf`_ documentation for more information.

Enable stack (lifecycle) scheduler hints under the ``[DEFAULT]`` section of ``/etc/heat/heat.conf``:

::

   [DEFAULT]
   stack_scheduler_hints = True

Add two new sections to the end of ``/etc/heat/heat.conf``: one to let the ``ATT::QoS::Pipe`` plugin know where to look for Tegu and IOArbiter, and one to let the allegro-openstack lifecycle plugin know where to find allegro-api.

::

   [att_qos_pipe]
   tegu_uri=http://$TEGU_HOST:29444/tegu/api
   ioarbiter_uri=http://$IOARBITER_HOST:7999/v1/ctrl/0/policy

   [allegro]
   allegro_api_server_url = http://$ALLEGRO_HOST:8090/v1

Restart heat-engine:

::

   $ sudo service heat-engine restart

Examine ``/var/log/heat/heat-engine.log``. The ``ATT::QoS`` plugins should be found and registered:

::

   INFO heat.engine.environment [-] Registering ATT::QoS::Pipe -> <class 'heat.engine.plugins.resources.ATT.QoS.Reservation.Pipe'>
   INFO heat.engine.environment [-] Registering ATT::QoS::ResourceGroup -> <class 'heat.engine.plugins.resources.ATT.QoS.ResourceGroup.ResourceGroup'>

The heat command line interface (python-heatclient) can also be used to verify that the plugins are available.

::

   $ heat resource-type-list | grep ATT
   | ATT::QoS::Pipe                           |
   | ATT::QoS::ResourceGroup                  |

Other ATT plugins will be visible as well. ``ATT::QoS::Pipe`` and ``ATT::QoS::ResourceGroup`` are the plugins most often used.

Note: In future revisions of OpenStack, the heat cli will be superceded by the OpenStack cli (python-openstackclient).

Nova Configuration
------------------

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

Cinder Configuration
--------------------

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

Tire-kick things using these example templates:

::

   production: /usr/local/etc/heat/examples
   developer:  $ALLEGRO_PATH/heat/examples

The flavor, ssh key, image, net/subnet IDs, mtu adjustment requirement, and security groups are all specific to the OpenStack installation. It will be necessary to edit various parameters to suit the environment in question.

Please see the `QoSOrch Wiki`_ for more information, presentations, and resource plugin documentation.

Contact
-------

Joe D'Andrea <jdandrea@research.att.com>

.. _Ostro: https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README
.. _Tegu: https://forge.research.att.com/plugins/mediawiki/wiki/qoscloud/index.php/Tegu_Installation_and_Configuration_Guide
.. _IOArbiter: https://forge.research.att.com/plugins/mediawiki/wiki/sds/index.php/IOArbiterInstallationGuide
.. _virtual environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _InsecurePlatformWarning: https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.
.. _site-packages: https://wiki.debian.org/Python#Deviations_from_upstream
.. _heat.conf: http://docs.openstack.org/kilo/config-reference/content/ch_configuring-openstack-orchestration.html
.. _QoSOrch Wiki: https://forge.research.att.com/plugins/mediawiki/wiki/qosorch/index.php/Main_Page
