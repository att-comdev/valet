=======
Allegro
=======

Allegro (part of the Valet service suite, including Ostro) gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. allegro provides resource plugins to OpenStack Heat for use with QoS services including Bora, Tegu, and IOArbiter.

Prerequisites
-------------

See ``$ALLEGRO_PATH/requirements.txt`` for full prerequisites.

- Ubuntu 12 LTS and OpenStack Kilo are required at a minimum.
- `Ostro`_ is the required and only supported placement engine at this time.
- If VM-to-VM QoS is required, install QoSLite (`Tegu`_ ).
- If VM-to-Volume QoS is required, install `IOArbiter`_ .

Getting Started
---------------

Clone the git repository from AT&T CodeCloud, using a ``$CODECLOUD_USER`` with appropriate access:

::

    $ git clone https://$CODECLOUD_USER@codecloud.web.att.com/scm/st_cloudqos/allegro.git
    $ cd qosorch

Installation
------------

As root, install in production or developer (editable) mode. pip will install any python dependencies required by allegro plugins or the api.

Install the plugins on an OpenStack controller node containing heat-engine, nova-scheduler, and cinder-scheduler.

::

   production: # pip install $ALLEGRO_PATH         # OpenStack plugins

   developer:  # pip install --editable $ALLEGRO_PATH         # OpenStack plugins

It is strongly recommended to create a `virtual environment`_ (venv) for allegro-api. Ubuntu uses pecan 0.3.0, which is out of date. Updating an Ubuntu package via pip can lead to instabilities. Uninstalling the Ubuntu package can lead to instabilities in other packages that require that particular version of pecan. Ostro will also be placed in this venv.

Install the API on the designated allegro node (which could be the same as the controller node, but doesn't have to be). Be sure to have the venv activated before doing this.

::

   # . $PATH_TO_VENV/bin/activate

   production: (VENV) # pip install $ALLEGRO_PATH\allegro # API
   developer:  (VENV) # pip install --editable $ALLEGRO_PATH/allegro # API

Python virtual environments can be deactivated with the ``deactivate`` command.

On the controller node, symlink the heat resource plugins so that heat knows how to find them. (In the future, the allegro-specific heat resource path may be added to the heat configuration independently, once supported.)

::

   production: # ln -s /usr/local/etc/heat/resources /usr/lib/heat
   developer:  # ln -s $ALLEGRO_PATH/heat/resources /usr/lib/heat

Database Setup
--------------

Create an empty ``allegro`` database (e.g., in mysql):

::

   $ mysql -u root -p
   mysql> CREATE DATABASE allegro;
   mysql> GRANT ALL PRIVILEGES ON allegro.* TO 'allegro'@'localhost' \
   IDENTIFIED BY '$ALLEGRO_DBPASS';
   mysql> GRANT ALL PRIVILEGES ON allegro.* TO 'allegro'@'%' \
   IDENTIFIED BY '$ALLEGRO_DBPASS';

Edit ``$ALLEGRO_PATH/allegro/config.py`` so that it has appropriate credentials:

::

   sqlalchemy = {
       'url': 'mysql+pymysql://allegro:$ALLEGRO_DBPASS@$CONTROLLER/allegro?charset=utf8',
       'echo':          True,
       'echo_pool':     True,
       'pool_recycle':  3600,
       'encoding':      'utf-8',
   }

Use pecan to setup the database tables on the allegro node. Activate a venv first if one is being used.

::

   $ cd $ALLEGRO_PATH/allegro
   $ pecan populate config.py

Python Virtual Environment and Ostro
------------------------------------

On the allegro node, if a virtual environment (venv) is used, it will be necessary to install ostro in the context of the venv or link to it from the broader default environment, e.g.:

::

   $ cd $VENV_PATH/local/lib/python2.7/site-packages
   $ ln -s /usr/local/lib/python2.7/dist-packages/ostro .

This does not have to be done with the venv activated, as it's just a symlink.

Starting allegro-api
--------------------

allegro-api can be started on the allegro node using pecan via the command line. Please note that This does not run as a daemon and is only recommended for development use. Activate a venv first if one is being used.

::

   $ cd $ALLEGRO_PATH/allegro
   $ pecan serve config.py

Alternatively, allegro-api can be configured to run in apache using WSGI.

Using allegro-api with apache
-----------------------------

Install apache2 and mod-wsgi:

::

   $ sudo apt-get install apache2 libapache2-mod-wsgi


Create the allegro user/group, for instance on Ubuntu:

::

   $ sudo adduser --gecos "allegro service user" allegro

If the uid/gid assigned by adduser needs to be adjusted:

::

   $ sudo usermod -u $DESIRED_ID -U tegu; sudo groupmod -g $DESIRED_ID tegu

Set up allegro directories and ownership:

::

   $ sudo -i
   # mkdir /var/www/allegro
   # mkdir /var/log/apache2/allegro
   # chown -R allegro:allegro /var/log/apache2/allegro /var/www/allegro
   # cp -p $ALLEGRO_PATH/allegro/app.wsgi $ALLEGRO_PATH/allegro/config.py /var/www/allegro

Setup allegro as an apache service:

::

   # cd $APACHE2_CONFIG_PATH/sites-available
   # cp -p $ALLEGRO_PATH/allegro/app.apache2 allegro.conf
   # chown root:root allegro.conf

Note: Depending on the installation, ``$APACHE2_CONFIG_PATH`` may be ``/opt/apache2`` or ``/etc/apache2``.

If a venv is being used, append ``python-path=$PATH_TO_VENV`` to ``WSGIDaemonProcess`` within ``allegro.conf``. This way Apache will use the correct python libraries.

Alternately, the following line can be added outside of the allegro ``VirtualHost`` directive. Note that this only makes sense if allegro will be the sole focal point of the apache install, at least as far as venvs are concerned.

::

   WSGIPythonHome $VENV_PATH

Enable allegro in apache, Test apache to make sure the configuration is valid, then restart:

::

   # cd $APACHE2_CONFIG_PATH/sites-enabled
   # ln -s ../sites-available/allegro.conf .
   # apachectl -t
   Syntax OK
   # apachectl graceful

Check allegro-api
-----------------

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

Heat Configuration
------------------

In ``/etc/heat/heat.conf`` enable stack lifecycle scheduler hints under the ``[DEFAULT]`` section:

::

   [DEFAULT]
   stack_scheduler_hints = True

Add two new sections to the end of ``/etc/heat/heat.conf``: one to let the ``ATT::QoS::Pipe`` plugin know where to look for Tegu and IOArbiter, and one to let the allegro lifecycle plugin know where to find allegro.

::

   [att_qos_pipe]
   tegu_uri=http://$CONTROLLER:29444/tegu/api
   ioarbiter_uri=http://$CONTROLLER:7999/v1/ctrl/0/policy

   [allegro]
   allegro_api_server_url = http://$CONTROLLER:8090/v1

Restart heat-engine:

::

   $ sudo service heat-engine restart

Examine ``/var/log/heat/heat-engine.log``. The ``ATT::QoS`` plugins should load.

::

   INFO heat.engine.environment [-] Registering ATT::QoS::Pipe -> <class 'heat.engine.plugins.resources.ATT.QoS.Reservation.Pipe'>
   INFO heat.engine.environment [-] Registering ATT::QoS::ResourceGroup -> <class 'heat.engine.plugins.resources.ATT.QoS.ResourceGroup.ResourceGroup'>

The heat CLI can also be used to verify that the plugins are available. 

::

   $ heat resource-type-list | grep ATT
   | ATT::QoS::Pipe                           |
   | ATT::QoS::ResourceGroup                  |

Other ATT plugins will be visible as well. Pipe and ResourceGroup are the main plugins of concern.

Nova Configuration
------------------

Adjust the ``[DEFAULT]`` section of ``/etc/nova/nova.conf`` so that ``nova-scheduler`` knows how to locate and to use allegro's scheduler filter. (The two ``scheduler_available_filters`` lines are deliberate. The first is required in order for nova to know where to locate its own default filters.) For ``scheduler_default_filters``, ensure that ``AllegroFilter`` is placed last.

::

   [DEFAULT]
   scheduler_available_filters = nova.scheduler.filters.all_filters
   scheduler_available_filters = allegro.openstack.nova.allegro_filter.AllegroFilter
   scheduler_default_filters = RetryFilter, AvailabilityZoneFilter, RamFilter, ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter, ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter, AllegroFilter

Restart nova-scheduler:

::

   $ sudo service nova-scheduler restart

Cinder Configuration
--------------------

Adjust the ``[DEFAULT]`` section of ``/etc/cinder/cinder.conf`` so that ``cinder-scheduler`` knows to use allegro's scheduler filter. Unlike nova, cinder automatically knows how to locate allegro. For ``scheduler_default_filters``, ensure that ``AllegroFilter`` is placed last.

::

   [DEFAULT]
   scheduler_default_filters = AvailabilityZoneFilter, CapacityFilter, CapabilitiesFilter, AllegroFilter

Restart cinder-scheduler: 

::

   $ sudo service cinder-scheduler restart

Examples
--------

Try it all out using the example templates:

::

   production: /usr/local/etc/heat/examples
   developer:  $ALLEGRO_PATH/heat/examples

Note: The flavor, ssh key, image, net/subnet IDs, mtu adjustment requirement, and security groups are all particular to the OpenStack installation. As such, these templates won't work out-of-the-box. It will be necessary to change various fields to suit the environment in question.

Please see the `QoSOrch Wiki`_ for more information, presentations, and resource plugin documentation.

Contact
-------

Joe D'Andrea <jdandrea@research.att.com>

.. _Ostro: https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README
.. _Tegu: https://forge.research.att.com/plugins/mediawiki/wiki/qoscloud/index.php/Tegu_Installation_and_Configuration_Guide
.. _IOArbiter: https://forge.research.att.com/plugins/mediawiki/wiki/sds/index.php/IOArbiterInstallationGuide
.. _virtual environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/

.. _QoSOrch Wiki: https://forge.research.att.com/plugins/mediawiki/wiki/qosorch/index.php/Main_Page
