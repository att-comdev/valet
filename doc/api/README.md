# Placement API v1 (CURRENT)

Determines placement for cloud resources.

## General API information

Authenticated calls that target a known URI but that use an HTTP method the implementation does not support return a 405 Method Not Allowed status. In addition, the HTTP OPTIONS method is supported for each known URI. In the OPTIONS case, the Allow response header indicates the supported HTTP methods.

## API versions

|--------|---------------------------------------------------------|-----------------------------------|
| GET    | `/`                                                     | Lists all Placement API versions. |

Normal response codes: 200

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

Documentation in progress.

|--------|---------------------------------------------------------|-----------------------------------|
| POST   | `/v1/{tenant_id}/groups`                                | Creates a group.                  |

**Normal response codes:** 201
**Error response codes:** unauthorized (401), internalServerError (500)

**Request parameters**

| Parameter   | Style | Type       | Description                                       |
|-------------|-------|------------|---------------------------------------------------|
| description (Optional) | plain | xsd:string | A description for the new group.                  |
| name        | plain | xsd:string | A name for the new group.                         |
| type        | plain | xsd:string | A type for the new group. Presently, the only valid value is `exclusivity`. |

**Response parameters**

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

|--------|---------------------------------------------------------|-----------------------------------|
| GET    | `/v1/{tenant_id}/groups`                                | Lists active groups.              |

|--------|---------------------------------------------------------|-----------------------------------|
| GET    | `/v1/{tenant_id}/groups/{group_id}`                     | Show group details.               |

|--------|---------------------------------------------------------|-----------------------------------|
| PUT    | `/v1/{tenant_id}/groups/{group_id}`                     | Updates a group.                  |

|--------|---------------------------------------------------------|-----------------------------------|
| DELETE | `/v1/{tenant_id}/groups/{group_id}`                     | Deletes a group.                  |

|--------|---------------------------------------------------------|-----------------------------------|
| POST   | `/v1/{tenant_id}/groups/{group_id}/members`             | Sets members of a group.          |

|--------|---------------------------------------------------------|-----------------------------------|
| PUT    | `/v1/{tenant_id}/groups/{group_id}/members`             | Updates members of a group.       |

|--------|---------------------------------------------------------|-----------------------------------|
| GET    | `/v1/{tenant_id}/groups/{group_id}/members`             | Lists members of a group.         |

|--------|---------------------------------------------------------|-----------------------------------|
| GET    | `/v1/{tenant_id}/groups/{group_id}/members/{member_id}` | Verify membership in a group.     |

|--------|---------------------------------------------------------|-----------------------------------|
| DELETE | `/v1/{tenant_id}/groups/{group_id}/members/{member_id}` | Delete member from a group.       |

|--------|---------------------------------------------------------|-----------------------------------|
| DELETE | `/v1/{tenant_id}/groups/{group_id}/members`             | Delete all members from a group.  |

## Optimizers

Documentation forthcoming.

## Placements

Documentation forthcoming.

## Plans

Documentation forthcoming.
