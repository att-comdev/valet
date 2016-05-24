# Valet

Valet gives OpenStack the ability to optimize cloud resources while simultaneously meeting a cloud application's QoS requirements. Valet provides an api service, a placement optimizer (Ostro), a high availability data storage and persistence layer (Music), and a set of OpenStack plugins.

**IMPORTANT**: [Overall AT&T AIC Installation of Valet is covered in a separate document](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/valet/atRef/refs/heads/master/renderFile/doc/aic/README.md).

Valet consists of the following components:

* [valet-openstack](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_os/README.md): a set of OpenStack plugins used to interact with Valet
* [valet-api](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_api/README.md): an API engine used to interact with Valet
* [Ostro](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/ostro/atRef/refs/heads/master/renderFile/README): a placement optimization engine
* [Music](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/music/atRef/refs/heads/master/renderFile/README.md): a data storage and persistence service
* [ostro-listener](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/ostro_listener/README.md): a message bus listener used in conjunction with Ostro and Music
* [havalet](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/havalet/README.rst): a service that assists in providing high availability for Valet

Additional documents:

* [OpenStack Heat Resource Plugins](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/havalet/README.rst): Heat resources
* [Placement API](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_api/doc/README.md): API requests/responses
* [Using Postman with valet-api](https://codecloud.web.att.com/plugins/servlet/readmeparser/display/ST_CLOUDQOS/allegro/atRef/refs/heads/master/renderFile/valet_api/valet_api/README.md): Postman support

## Contact

Joe D'Andrea <jdandrea@research.att.com>

