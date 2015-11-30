=======
QoSOrch
=======

QoSOrch adds resource plugins to OpenStack Heat for use with QoS services including Ostro, Tegu, and IOArbiter.

Getting Started
---------------
Clone the git repository from CodeCloud, using your username in the URI.
For example, with the username of jd0616, specify:

::

    git clone https://jd0616@codecloud.web.att.com/scm/st_cloudqos/allegro.git
    cd qosorch

For more information, please see the `QoSOrch Wiki`_.

.. _QoSOrch Wiki: https://forge.research.att.com/plugins/mediawiki/wiki/qosorch/index.php/Main_Page

Installation
------------
See ``requirements.txt`` for prerequisites.

- Ubuntu
- OpenStack
- Ostro
- QoSLite (Tegu)
- IOArbiter

NOTE: Prior documentation advised that each cinder node's ``cinder.conf`` must have a unique storage availability zone using the same nomenclature as nova (e.g., nova:host1). This is no longer required.

As root, install in production or developer mode:

::

   python setup.py install
     or
   python setup.py develop

Symlink the heat resource plugins so that heat can find them:

::

   ln -s /usr/local/etc/heat/resources /usr/lib/heat
     or
   ln -s /git-repository-path/heat/resources /usr/lib/heat

Add a new section to the end of /etc/heat/heat.conf or any other suitable/preferred configuration file (where ``FQDN`` is the target controller):

::

   [att_qos_pipe]
   tegu_uri=http://FQDN:29444/tegu/api
   ioarbiter_uri=http://FQDN:7999/v1/ctrl/0/policy

Restart the ``heat-engine`` service:

::

   service heat-engine restart

If the above config options aren't in ``heat.conf``, use ``--config-dir`` or ``--config-file`` to advise heat of its location.

Examine the log. The ``ATT::QoS`` plugins should load with some deprecation warnings, like so:

::

   INFO heat.engine.environment [-] Registering ATT::QoS::DiversityZone -> <class 'heat.engine.plugins.resources.ATT.QoS.DiversityZone.DiversityZone'>
   UserWarning: ATT::QoS::DiversityZone is unsupported and will be removed in a future release of CloudQoS. Use ATT::QoS::ResourceGroup to specify a diversity relationship.
   INFO heat.engine.environment [-] Registering ATT::QoS::Reservation -> <class 'heat.engine.plugins.resources.ATT.QoS.Reservation.Reservation'>
   INFO heat.engine.environment [-] Registering ATT::QoS::Pipe -> <class 'heat.engine.plugins.resources.ATT.QoS.Reservation.Pipe'>
   UserWarning: Deprecated. Use ATT::QoS::Reservation.
   INFO heat.engine.environment [-] Registering ATT::QoS::ResourceGroup -> <class 'heat.engine.plugins.resources.ATT.QoS.ResourceGroup.ResourceGroup'>
   INFO heat.engine.environment [-] Registering ATT::QoS::Restarter -> <class 'heat.engine.plugins.resources.ATT.QoS.Restarter.Restarter'>

Test the installation using the examples (requires OS credentials and template modification).

::

   /usr/local/etc/heat/examples for production installs
     or
   /git-repository-path/heat/examples for developer installs

Note: The flavor, ssh key, image, net/subnet IDs, mtu adjustment requirement, and security groups are all particular to the agave cluster. As such, these templates won't work out-of-the-box. It will be necessary to change various fields to suit the cluster in question.


Contact
-------

:Author:

   jd <jdandrea@research.att.com>
