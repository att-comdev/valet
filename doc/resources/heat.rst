==============
Heat Resources
==============

Valet comes with a set of OpenStack heat resources. This document explains what they are and how they work. As new resources become formally introduced, they will be added here.

ATT::CloudQoS::ResourceGroup
----------------------------

Note: The name of this resource may change to OS::Valet::ResourceGroup in the future.

Use this to declare one or more deployable resources (currently Servers, Volumes, and other Resource Groups) as being related through affinity, diversity, or exclusivity. While Resource Groups can include other groups, no circular references are permitted.

This resource is purely informational in nature and makes no changes to heat, nova, or cinder. The Valet Heat Lifecycle Plugin passes this information to the optimizer.

Properties
----------

Note: Property characteristics are presently under review and may be revised.

* *name* (String)
  * Name of relationship. Required for exclusivity groups.
  * Can be updated without replacement.

* *relationship* (String)
  * Grouping relationship.
  * Allowed values: affinity, diversity, exclusivity
  * Can be updated without replacement.
  * Required property.

* *level* (String)
  * Level of relationship between resources.
  * See list below for allowed values.
  * Can be updated without replacement.

* *resources* (List)
  * List of associated resource IDs.
  * Can be updated without replacement.
  * Required property.

Levels
^^^^^^

- *cluster*: Across a cluster, one resource per cluster.
- *rack*: Across racks, one resource per host.
- *host*: All resources on a single host.
- *any*: Any level.

Attributes
----------

None at this time.

Example
-------

Given a Heat template with a server and volume resource, declare an affinity between them at the rack level:

|  resources:
|    qos_resource_group:
|      type: ATT::QoS::ResourceGroup
|      properties:
|        name: my_awesome_group
|        relationship: affinity
|        level: rack
|        resources:
|        - {get_resource: server}
|        - {get_resource: volume}

Proposed Notation for 'diverse-affinity'
----------------------------------------

Note: This is a proposal and not yet implemented.

Suppose we are given a set of server/volume pairs, and we'd like to treat each pair as an affinity group, and then treat all affinity groups diversely. The following notation makes this diverse affinity pattern easier to describe and with no name repetition.

|  resources:
|    qos_resource_group:
|      type: ATT::QoS::ResourceGroup
|      properties:
|        name: my_even_awesomer_group
|        relationship: diverse-affinity
|        level: host
|        resources:
|        - - {get_resource: server1}
|          - {get_resource: volume1}
|        - - {get_resource: server2}
|          - {get_resource: volume2}
|        - - {get_resource: server3}
|          - {get_resource: volume3}

In a hypothetical example of a Ceph deployment with three monitors, twelve OSDs, and one client, each paired with a volume, that means we only need 3 Heat resources instead of 18.

Plugin Schema
-------------

Use `heat resource-type-show ATT::CloudQoS::ResourceGroup` to view the schema.

|  {
|    "support_status": {
|      "status": "SUPPORTED", 
|      "message": null, 
|      "version": null, 
|      "previous_status": null
|    }, 
|    "attributes": {
|      "show": {
|        "type": "map", 
|        "description": "Detailed information about resource."
|      }
|    }, 
|    "properties": {
|      "resources": {
|        "type": "list", 
|        "required": true, 
|        "update_allowed": true, 
|        "description": "List of one or more resource IDs.", 
|        "immutable": false
|      }, 
|      "name": {
|        "type": "string", 
|        "required": false, 
|        "update_allowed": true, 
|        "description": "Name of relationship. Required for exclusivity groups.", 
|        "immutable": false
|      }, 
|      "relationship": {
|        "description": "Grouping relationship.", 
|        "required": true, 
|        "update_allowed": true, 
|        "type": "string", 
|        "immutable": false, 
|        "constraints": [
|          {
|            "allowed_values": [
|              "affinity", 
|              "diversity", 
|              "exclusivity"
|            ]
|          }
|        ]
|      }, 
|      "level": {
|        "description": "Level of relationship between resources.", 
|        "required": false, 
|        "update_allowed": true, 
|        "type": "string", 
|        "immutable": false, 
|        "constraints": [
|          {
|            "allowed_values": [
|              "host", 
|              "rack", 
|              "cluster", 
|              "any"
|            ]
|          }
|        ]
|      }
|    }, 
|    "resource_type": "ATT::CloudQoS::ResourceGroup"
|  }
