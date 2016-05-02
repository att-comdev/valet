==========================
Placement API v1 (CURRENT)
==========================

.. _NOTE: The use of superfluous :: characters is necessary as a workaround for a CodeCloud reStructuredText markup parsing bug.

Determines placement for cloud resources.

General API information
-----------------------

Authenticated calls that target a known URI but that use an HTTP method the implementation does not support return a 405 Method Not Allowed status. In addition, the HTTP OPTIONS method is supported for each known URI. In the OPTIONS case, the Allow response header indicates the supported HTTP methods.

API versions
------------

===  =  =================================
GET  /  Lists all Placement API versions.
===  =  =================================

=====================  ===
Normal response codes  200
=====================  ===

::

  {

::

    "versions": [
::

      {
::

        "status": "CURRENT",
::

        "id": "v1.0",
::

        "links": [
::

          {
::

            "href": "http://127.0.0.1:8090/v1/",
::

            "rel": "self"
::

          }
::

        ]
::

      }
::

    ]
::

  }

This operation does not accept a request body.

Groups
------

Documentation forthcoming.

====  ====================  ================
POST  /v1/TENANT_ID/groups  Creates a group.
====  ====================  ================

===  ====================  ====================
GET  /v1/TENANT_ID/groups  Lists active groups.
===  ====================  ====================

===  =============================  ====================
GET  /v1/TENANT_ID/groups/GROUP_ID  Lists active groups.
===  =============================  ====================

===  =============================  ================
PUT  /v1/TENANT_ID/groups/GROUP_ID  Updates a group.
===  =============================  ================

======  =============================  ================
DELETE  /v1/TENANT_ID/groups/GROUP_ID  Deletes a group.
======  =============================  ================

====  =====================================  ========================
POST  /v1/TENANT_ID/groups/GROUP_ID/members  Sets members of a group.
====  =====================================  ========================

===  =====================================  ===========================
PUT  /v1/TENANT_ID/groups/GROUP_ID/members  Updates members of a group.
===  =====================================  ===========================

===  =====================================  =========================
GET  /v1/TENANT_ID/groups/GROUP_ID/members  Lists members of a group.
===  =====================================  =========================

===  ===============================================  =============================
GET  /v1/TENANT_ID/groups/GROUP_ID/members/MEMBER_ID  Verify membership in a group.
===  ===============================================  =============================

======  ===============================================  ===========================
DELETE  /v1/TENANT_ID/groups/GROUP_ID/members/MEMBER_ID  Delete member from a group.
======  ===============================================  ===========================

======  =====================================  ================================
DELETE  /v1/TENANT_ID/groups/GROUP_ID/members  Delete all members from a group.
======  =====================================  ================================

Optimizers
----------

Documentation forthcoming.

Placements
----------

Documentation forthcoming.

Plans
-----

Documentation forthcoming.
