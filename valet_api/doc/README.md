# Placement API v1 - CURRENT

Determines placement for cloud resources.

## General API information

Authenticated calls that target a known URI but that use an HTTP method the implementation does not support return a 405 Method Not Allowed status. In addition, the HTTP OPTIONS method is supported for each known URI. In both cases, the Allow response header indicates the supported HTTP methods. See the [API Errors](#api-errors) section for more information about the error response structure.


## API versions

### List all Placement API versions

**GET** `/`

**Normal response codes:** 200

```json
{
  "versions": [
    {
      "status": "CURRENT",
      "id": "v1.0",
      "links": [
        {
          "href": "http://127.0.0.1:8090/v1/",
          "rel": "self"
        }
      ]
    }
  ]
}
```

This operation does not accept a request body.

## Groups

### Create a group

**POST** `/v1/groups`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), internalServerError (500)

#### Request parameters

| Parameter | Style | Type | Description |
|-----------|-------|------|-------------|
| description | plain | xsd:string | A description for the new group. |
| name | plain | xsd:string | A name for the new group. Must only contain letters, numbers, hypens, full stops, underscores, and tildes (RFC 3986, Section 2.3). This parameter is immutable. |
| type | plain | xsd:string | A type for the new group. Presently, the only valid value is `exclusivity`. This parameter is immutable. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. Initially empty.         |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "name": "group",
  "description": "My Awesome Group",
  "type": "exclusivity"
}
```

```json
{
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
  "members": [],
  "name": "group"
}
```

* * * * * * * * * * *

### List active groups

**GET** `/v1/groups`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| groups      | plain | xsd:list   | A list of active group UUIDs.                     |

This operation does not accept a request body.

```json
{
  "groups": [
    {
      "description": "My Awesome Group",
      "type": "exclusivity",
      "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
      "members": [],
      "name": "group"
    }
  ]
}
```

* * * * * * * * * * *

### Show group details

**GET** `/v1/groups/{group_id}`

**Normal response codes:** 200
**Error response codes:** unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "group": {
    "description": "My Awesome Group",
    "type": "exclusivity",
    "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
    "members": [],
    "name": "group"
  }
}
```

This operation does not accept a request body.

* * * * * * * * * * *

### Update a group

**PUT** `/v1/groups/{group_id}`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | A description for the group. Replaces the original description. |
| group_id | plain | csapi:UUID | The UUID of the group. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "description": "My Extra Awesome Group"
}
```

```json
{
  "description": "My Extra Awesome Group",
  "type": "exclusivity",
  "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
  "members": [],
  "name": "group"
}
```

* * * * * * * * * * *

### Delete a group

**DELETE** `/v1/groups/{group_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Add members to a group

**PUT** `/v1/groups/{group_id}/members`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. This is added to any previous list of members. All members must be valid tenant UUIDs. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

```json
{
  "members": [
    "b7d0e9b175294b649464caa3411adb3f"
  ]
}
```

```json
{
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "bf49803b-48b6-4a13-9191-98dde1dbd5e4",
  "members": [
    "b7d0e9b175294b649464caa3411adb3f",
    "65c3e5ee5ee0428caa5e5275c58ead61"
  ],
  "name": "group"
}
```

* * * * * * * * * * *

### Verify membership in a group

**GET** `/v1/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete member from a group

**DELETE** `/v1/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete all members from a group

**DELETE** `/v1/groups/{group_id}/members`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |

This operation does not accept a request body and does not return a response body.

## Status

### Get status of all subsystems

**HEAD** `/v1/status`

**Normal response codes:** xxx
**Error response codes:** internalServerError (500)

This operation does not accept a request body and does not return a response body.

### List status of all subsystems

**GET** `/v1/status`

**Normal response codes:** xxx
**Error response codes:** internalServerError (500)

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

This operation does not accept a request body.

```json
{
  tbd
}
```

## Placements

Documentation forthcoming.

### List active placements

**GET** `/v1/placements`

**Normal response codes:** xxx
**Error response codes:** xxx

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

This operation does not accept a request body.

```json
[
  {
    "plan_id": "1853a7e7-0075-465b-9019-8908db680f2e",
    "name": "my_instance",
    "orchestration_id": "b71bedad-dd57-4942-a7bd-ab074b72d652",
    "location": "qos103",
    "reserved": null,
    "id": "e8ffb1b4-47d3-4ba4-b10c-7f58c937a0ba"
  }
]
```

### Show placement details - no reservation

**GET** `/v1/placements/{placement_id}`

**Normal response codes:** xxx
**Error response codes:** xxx

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

This operation does not accept a request body.

```json
{
  "plan_id": "1853a7e7-0075-465b-9019-8908db680f2e",
  "name": "my_instance",
  "orchestration_id": "b71bedad-dd57-4942-a7bd-ab074b72d652",
  "location": "qos103",
  "reserved": null,
  "id": "e8ffb1b4-47d3-4ba4-b10c-7f58c937a0ba"
}
```

### Recommend a placement for an existing resource

**POST** `/v1/placements`

**Normal response codes:** xxx
**Error response codes:** xxx

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

```json
{
  "resource_id": "68f61b2-26f3-cbc1-7981-5f52c937c0cd"
  "locations": ["qos101", "qos102", "qos104", "qos106", "qos107"]
}
```

```json
tbd
```

### Reserve a placement - with possible replanning

**POST** `/v1/placements/{placement_id}`

**Normal response codes:** xxx
**Error response codes:** xxx

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

```json
{
  "locations": ["qos101", "qos102", "qos104", "qos106", "qos107"]
}
```

```json
{
  "plan_id": "1853a7e7-0075-465b-9019-8908db680f2e",
  "name": "my_instance",
  "orchestration_id": "b71bedad-dd57-4942-a7bd-ab074b72d652",
  "location": "qos103",
  "reserved": null,
  "id": "e8ffb1b4-47d3-4ba4-b10c-7f58c937a0ba"
}
```

## Plans

Documentation forthcoming.

### Create a plan

**POST** `/v1/plans`

**Normal response codes:** xxx
**Error response codes:** xxx

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_name   | plain | xsd:string | xxx                                               |
| resources   | plain | xsd:string | xxx                                               |
| stack_id    | plain | xsd:string | xxx                                               |
| timeout     | plain | xsd:string | xxx                                               |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| xxx         | plain | xsd:string | xxx                                               |

```json
{
    "plan_name": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "resources": {
        "b71bedad-dd57-4942-a7bd-ab074b72d652": {
            "properties": {
                "flavor": "m1.small",
                "image": "ubuntu12_04",
                "key_name": "demo",
                "networks": [
                    {
                        "network": "demo-net"
                    }
                ]
            },
            "type": "OS::Nova::Server",
            "name": "my_instance"
        }
    },
    "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "timeout": "60 sec"
}
```

```json
{
  "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
  "id": "1853a7e7-0075-465b-9019-8908db680f2e",
  "placements": {
    "b71bedad-dd57-4942-a7bd-ab074b72d652": {
      "location": "qos103",
      "name": "my_instance"
    }
  },
  "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
}
```

### List active plans

**GET** `/v1/plans`

**Normal response codes:** xxx
**Error response codes:** xxx

This operation does not accept a request body.

```json
[
  "e624474b-fc80-4053-ab5f-45cc1030e692"
]
```

### Show plan details

**GET** `/v1/plans/{plan_id}`

**Normal response codes:** xxx
**Error response codes:** xxx

### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_id     | plain | xsd:string | The UUID of the plan.                             |

### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| name        | plain | xsd:string | The name of the plan.                             |
| id          | plain | xsd:string | The UUID of the plan.                             |
| placements  | plain | xsd:string | A dictionary of placements. Each placement is keyed by the Orchestration UUID and contains a ``location`` and ``name`` corresponding to the host placement and Heat resource name, respectively. |
| stack_id    | plain | xsd:string | The UUID of the stack.                            |

This operation does not accept a request body.

```json
{
  "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
  "id": "1853a7e7-0075-465b-9019-8908db680f2e",
  "placements": {
    "b71bedad-dd57-4942-a7bd-ab074b72d652": {
      "location": "qos103",
      "name": "my_instance"
    }
  },
  "name": "e624474b-fc80-4053-ab5f-45cc1030e692"
}
```

### Update a plan

**PUT** `/v1/plans/{plan_id}`

**Normal response codes:** xxx
**Error response codes:** xxx

### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_name   | plain | xsd:string | xxx                                               |
| resources   | plain | xsd:string | xxx                                               |
| resources_update | plain | xsd:string | xxx                                               |
| stack_id    | plain | xsd:string | xxx                                               |
| timeout     | plain | xsd:string | xxx                                               |

### Response parameters

tbd

```json
{
    "plan_name": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "resources": {
        "b71bedad-dd57-4942-a7bd-ab074b72d652": {
            "Properties": {
                "flavor": "m1.small",
                "image": "ubuntu12_04",
                "key_name": "demo",
                "networks": [
                    {
                        "network": "demo-net"
                    }
                ]
            },
            "Type": "OS::Nova::Server",
            "name": "my_instance"
        }
    },
    "resources_update": {
        "a649424b-dd57-1431-befc-45cc4b72d653": {
            "Properties": {
                "flavor": "m1.small",
                "image": "ubuntu12_04",
                "key_name": "demo",
                "networks": [
                    {
                        "network": "demo-net"
                    }
                ]
            },
            "Type": "OS::Nova::Server",
            "name": "my_new_instance"
        }
    },
    "stack_id": "e624474b-fc80-4053-ab5f-45cc1030e692",
    "timeout": "60 sec"
}
```

```json
tbd
```

### Delete a plan

**DELETE** `/v1/plans/{plan_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| plan_id     | plain | xsd:string | The UUID of the plan.                             |

This operation does not accept a request body and does not return a response body.

## API Errors

In the event of an error with a status other than unauthorized (401), a detailed repsonse body is returned.

### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| title       | plain | xsd:string | Human-readable name.                              |
| explanation | plain | xsd:string | Detailed explanation with remediation (if any).   |
| code        | plain | xsd:string | HTTP Status Code.                                 |
| error       | plain | xsd:string | Error dictionary.                                 |
| message     | plain | xsd:string | Internal error message.                           |
| traceback   | plain | xsd:string | Python traceback (if available).                  |
| type        | plain | xsd:string | HTTP Status class name (from python-webob)        |

#### Examples

A group with the name "gro up" is considered a bad request because the name contains a space.

```json
{
  "title": "Bad Request",
  "explanation": "-> name -> gro up did not pass validation against callable: group_name_type (must contain only uppercase and lowercase letters, decimal digits, hyphens, periods, underscores, and tildes [RFC 3986, Section 2.3])",
  "code": 400,
  "error": {
    "message": "The server could not comply with the request since it is either malformed or otherwise incorrect.",
    "traceback": null,
    "type": "HTTPBadRequest"
  }
}
```

The HTTP COPY method was attempted but is not allowed.

```json
{
  "title": "Method Not Allowed",
  "explanation": "The COPY method is not allowed.",
  "code": 405,
  "error": {
    "message": "The server could not comply with the request since it is either malformed or otherwise incorrect.",
    "traceback": null,
    "type": "HTTPMethodNotAllowed"
  }
}
```

The exclusivity group named 'foosball' was not found.

```json
{
  "title": "Conflict",
  "explanation": "Valet error: Exclusivity group 'foosball' not found",
  "code": 409,
  "error": {
    "message": "There was a conflict when trying to complete your request.",
    "traceback": null,
    "type": "HTTPConflict"
  }
}
```
