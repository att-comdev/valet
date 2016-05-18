For the valet-api Postman collection, create an environment with the following key/value pairs:

* ``valet``: valet-api endpoint (e.g., ``http://controller:8090``)
* ``tenant_name``: tenant name (e.g., ``service``)
* ``username``: username (e.g., ``valet``)
* ``password``: password

Use the **Keystone Generate Token v2** POST request to generate a token. It will be stored in the Postman environment and used for all valet-api requests..
