# Placement API v1 (CURRENT)

Determines placement for cloud resources.

## General API information

Authenticated calls that target a known URI but that use an HTTP method the implementation does not support return a 405 Method Not Allowed status. In addition, the HTTP OPTIONS method is supported for each known URI. In the OPTIONS case, the Allow response header indicates the supported HTTP methods.

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

**POST** `/v1/{tenant_id}/groups`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), internalServerError (500)

#### Request parameters

| Parameter | Style | Type | Description |
|-----------|-------|------|-------------|
| description (Optional) | plain | xsd:string | A description for the new group. |
| name | plain | xsd:string | A name for the new group. |
| tenant_id | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |
| type | plain | xsd:string | A type for the new group. Presently, the only valid value is `exclusivity`. |

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

**GET** `/v1/{tenant_id}/groups`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Request parameters

| Parameter | Style | Type | Description |
|-----------|-------|------|-------------|
| tenant_id | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| groups      | plain | xsd:list   | A list of active group UUIDs.                     |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body.

* * * * * * * * * * *

### Show group details

**GET** `/v1/{tenant_id}/groups/{group_id}`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

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
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "7de4790e-08f2-44b7-8332-7a41fab36a41",
  "members": [],
  "name": "group"
}
```
This operation does not accept a request body.

* * * * * * * * * * *

### Update a group

**PUT** `/v1/{tenant_id}/groups/{group_id}`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description (Optional) | plain | xsd:string | A description for the group. Replaces the original description. |
| group_id | plain | csapi:UUID | The UUID of the group. |
| name | plain | xsd:string | A name for the group. Replaces the original name. |
| tenant_id | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |
| type | plain | xsd:string | A type for the group. Presently, the only valid value is `exclusivity`. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description | plain | xsd:string | The group description.                            |
| id          | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members.                          |
| name        | plain | xsd:string | The group name.                                   |
| type        | plain | xsd:string | The group type.                                   |

* * * * * * * * * * *

### Delete a group

**DELETE** `/v1/{tenant_id}/groups/{group_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Set members of a group

**POST** `/v1/{tenant_id}/groups/{group_id}/members`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. This replaces any previous list of members. All members must be valid tenant UUIDs. |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

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
        "65c3e5ee5ee0428caa5e5275c58ead61"
    ]
}
```

```json
{
  "description": "My Awesome Group",
  "type": "exclusivity",
  "id": "bf49803b-48b6-4a13-9191-98dde1dbd5e4",
  "members": [
    "65c3e5ee5ee0428caa5e5275c58ead61"
  ],
  "name": "group"
}
```

* * * * * * * * * * *

### Update members of a group

**PUT** `/v1/{tenant_id}/groups/{group_id}/members`

**Normal response codes:** 201
**Error response codes:** badRequest (400), unauthorized (401), conflict (409)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| members     | plain | xsd:list   | A list of group members. This is added to any previous list of members. All members must be valid tenant UUIDs. |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

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

### List members of a group

**GET** `/v1/{tenant_id}/groups/{group_id}/members`

**Normal response codes:** 200
**Error response codes:** unauthorized (401)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

#### Response parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| members     | plain | xsd:list   | A list of member UUIDs for the group. Members are tenant UUIDs that were valid at the time they were added. |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body.

* * * * * * * * * * *

### Verify membership in a group

**GET** `/v1/{tenant_id}/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete member from a group

**DELETE** `/v1/{tenant_id}/groups/{group_id}/members/{member_id}`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| member_id   | plain | csapi:UUID | The UUID of one potential group member. Members are tenant UUIDs. |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body and does not return a response body.

* * * * * * * * * * *

### Delete all members from a group

**DELETE** `/v1/{tenant_id}/groups/{group_id}/members`

**Normal response codes:** 204
**Error response codes:** badRequest (400), unauthorized (401), itemNotFound (404)

#### Request parameters

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| group_id    | plain | csapi:UUID | The UUID of the group.                            |
| tenant_id   | plain | csapi:UUID | The UUID of the tenant. A tenant is also known as an account or project. |

This operation does not accept a request body and does not return a response body.

## Optimizers

Documentation forthcoming.

## Placements

Documentation forthcoming.

## Plans

Documentation forthcoming.
