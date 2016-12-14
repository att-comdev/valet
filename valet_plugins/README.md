# Valet

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, a placement optimizer (Ostro), a high availability data storage and persistence layer (Music), and a set of OpenStack plugins.

**IMPORTANT**: [Overall Installation of Valet is covered in a separate document](https://github.com/att-comdev/valet/blob/master/doc/valet_os.md).

Learn more about Valet:

* [OpenStack Newton Summit Presentation](https://www.openstack.org/videos/video/valet-holistic-data-center-optimization-for-openstack) (Austin, TX, 27 April 2016)
* [Presentation Slides](http://www.research.att.com/export/sites/att_labs/techdocs/TD_101806.pdf) (PDF)

Valet consists of the following components:

* [valet-openstack](https://github.com/att-comdev/valet/blob/master/doc/valet_os.md): a set of OpenStack plugins used to interact with Valet
* [valet-api](https://github.com/att-comdev/valet/blob/master/doc/valet_api.md): an API engine used to interact with Valet
* [Ostro](https://github.com/att-comdev/valet/blob/master/doc/ostro.md): a placement optimization engine
* Music: a data storage and persistence service
* [ostro-listener](https://github.com/att-comdev/valet/blob/master/doc/ostro_listener.md): a message bus listener used in conjunction with Ostro and Music
* [havalet](https://github.com/att-comdev/valet/blob/master/doc/ha.md): a service that assists in providing high availability for Valet

Additional documents:

* [OpenStack Heat Resource Plugins](https://github.com/att-comdev/valet/blob/master/valet_plugins/valet_plugins/heat/README.md): Heat resources
* [Placement API](https://github.com/att-comdev/valet/blob/master/doc/valet_api.md): API requests/responses
* [Using Postman with valet-api](https://github.com/att-comdev/valet/blob/master/valet/tests/api/README.md): Postman support

## Thank You

Alicia Abella, Saar Alaluf, Bharath Balasubramanian, Roy Ben Hai, Shimon Benattar, Yael Ben Shalom, Benny Bustan, Rachel Cohen, Joe D'Andrea, Harel Dorfman, Boaz Elitzur, P.K. Esrawan, Inbal Harduf, Matti Hiltunen, Doron Honigsberg, Kaustubh Joshi, Gueyoung Jung, Gerald Karam, David Khanin, Israel Kliger, Erez Korn, Max Osipov, Chris Rice, Amnon Sagiv, Gideon Shafran, Galit Shemesh, Anna Yefimov; AT&T Advanced Technology and Architecture, AT&T Technology Development - AIC, Additional partners in AT&T Domain 2.0. Apologies if we missed anyone (please advise via email!).

## Contact

Joe D'Andrea <jdandrea@research.att.com>
