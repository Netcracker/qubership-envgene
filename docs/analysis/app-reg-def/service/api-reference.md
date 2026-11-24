# API reference

- [Conventions](#conventions)
- [GET /api/v1/resolve](#get-apiv1resolve)
- [POST /api/v1/resolve:batch](#post-apiv1resolvebatch)
- [GET /api/v1/registry-definitions/{name}](#get-apiv1registry-definitionsname)
- [GET /api/v1/application-definitions/{name}](#get-apiv1application-definitionsname)
- [POST /api/v1/registry-definitions](#post-apiv1registry-definitions)
- [PUT /api/v1/registry-definitions/{name}](#put-apiv1registry-definitionsname)
- [POST /api/v1/application-definitions](#post-apiv1application-definitions)
- [PUT /api/v1/application-definitions/{name}](#put-apiv1application-definitionsname)
- [Error model](#error-model)

The appregdef service exposes a small HTTP API. `resolve` returns the joined defs as an `Application`, and
the consumer adds the version and the credentials to build the artifact and the provider and download
through artifacts_finder. The write interfaces create and update defs in git. This page is the
human-readable companion to `openapi.yaml`. The objects in the payloads are in [model.md](../model.md).

## Conventions

- base path `/api/v1`, media type `application/json`.
- every request is authorized. Read verbs and write verbs may need different permissions. The authn model
  is in [deployment-and-operations.md](deployment-and-operations.md).
- `zone` is an optional query parameter on the read interfaces. There is one default zone today, and it is
  reserved for multizone.
- the service returns defs with their `credId` references, not the secret values, and it never contacts a
  registry. Building the artifact and the provider and downloading are the consumer's, through the client
  and artifacts_finder.
- errors share one shape and one status-code catalog, in [Error model](#error-model). Each interface notes
  the codes it returns.
- `listRegDefs` and `listAppDefs` (open, O3) are not specified here yet. The write interfaces are the
  parked target shape (P1), their semantics are settled but not built.

## GET /api/v1/resolve

Resolves an application to its `Application`, the AppDef attributes with the RegDef joined in.
Version-independent.

**Parameters**

- `app` (query, required): the application name.
- `zone` (query, optional): the registry zone, one default today.

**Request**

```text
GET /api/v1/resolve?app=billing
```

**Response** `200 OK`

```yaml
# the Application: the AppDef attributes with the RegDef joined in as registry
name: billing
registryName: shared-platform
groupId: com.example.billing
artifactId: billing-dd
solutionDescriptor: false
supportParallelDeploy: false
deployParameters:
  BILLING_DB_HOST: billing-db.example.local
technicalConfigurationParameters:
  LOG_LEVEL: INFO
metadata:
  releaseName: billing
# the resolved RegDef, v1 or v2, see ../model.md
registry:
  name: shared-platform
  version: v2
  # authConfig and the registry sections
```

**Logic**

1. Look up the AppDef by `app` in the cache. If it is absent, `404`.
2. Look up the RegDef named by the AppDef `registryName`. If it is absent, `422`, the def points at a
   registry that does not exist.
3. Return the Application, the AppDef attributes with the RegDef joined in as `registry`, as stored, v1 or
   v2.

The service does not select DD or SD, build an artifact, mint auth, or touch a registry. The consumer does
that with the version and the credentials, through the client and artifacts_finder.

## POST /api/v1/resolve:batch

Resolves a list of applications in one call, each like `GET /api/v1/resolve`.

**Parameters**

- body (required): a list of application names.
- `zone` (query, optional): applies to the whole batch.

**Request**

```yaml
- app: billing
- app: payments
```

**Response** `200 OK`

```yaml
# one result per entry, in request order
- app: billing
  # the Application, as in resolve
- app: payments
  error:
    code: not_found
    message: application payments is not known
```

**Logic**

1. Validate the body, a non-empty list of application names.
2. Run the resolve logic for each against the cache.
3. Return an Application or a per-entry error for each, so one bad entry does not fail the batch.

## GET /api/v1/registry-definitions/{name}

Returns a RegDef by name, with no application. The way to reach a registry directly, for publish and
promote flows.

**Parameters**

- `name` (path, required): the RegDef name.
- `zone` (query, optional).

**Request**

```text
GET /api/v1/registry-definitions/shared-platform
```

**Response** `200 OK`

```yaml
# the RegDef as stored, v1 or v2, see ../model.md
name: shared-platform
version: v2
authConfig:
  nexus-up:
    provider: nexus
    authMethod: userPass
    accessRoles:
      read: nexus-read
registries:
  - artifactType: maven
    authConfig: nexus-up
    repositories:
      - type: release
        url: https://nexus.example.com/repository/maven-releases
        repoName: maven-releases
  # ... other artifact types
```

**Logic**

1. Look up the RegDef by `name` in the cache. If it is absent, `404`.
2. Return the RegDef as stored.

## GET /api/v1/application-definitions/{name}

Returns an AppDef by name, without resolving its registry. The raw stored definition.

**Parameters**

- `name` (path, required): the AppDef name.

**Request**

```text
GET /api/v1/application-definitions/billing
```

**Response** `200 OK`

```yaml
# the AppDef as stored, see ../model.md
name: billing
registryName: shared-platform
groupId: com.example.billing
artifactId: billing-dd
solutionDescriptor: false
supportParallelDeploy: false
deployParameters:
  BILLING_DB_HOST: billing-db.example.local
technicalConfigurationParameters:
  LOG_LEVEL: INFO
```

**Logic**

1. Look up the AppDef by `name` in the cache. If it is absent, `404`.
2. Return the AppDef as stored.

## POST /api/v1/registry-definitions

Creates a RegDef. Parked (P1), the shape is settled. The write is eventually consistent. The response
carries the written object, and the cache catches up on the next resync.

**Parameters**

- body (required): the RegDef object.

**Request**

```yaml
name: shared-platform
version: v2
authConfig:
  nexus-up:
    provider: nexus
    authMethod: userPass
    accessRoles:
      read: nexus-read
registries:
  - artifactType: maven
    authConfig: nexus-up
    repositories:
      - type: release
        url: https://nexus.example.com/repository/maven-releases
        repoName: maven-releases
```

**Response** `201 Created` with the written object. `409` if a def with that name already exists.

**Logic**

1. Validate the body against the schema, and validate or normalize the name to the kebab DNS-safe
   convention.
2. If a def with that name already exists, `409`.
3. Commit and push the new file to the defs repo, with a fetch-rebase retry on a non-fast-forward.
4. Return the written object. A following resolve sees it once the push-triggered resync lands.

## PUT /api/v1/registry-definitions/{name}

Updates an existing RegDef. Parked (P1), the shape is settled.

**Parameters**

- `name` (path, required): the RegDef name.
- body (required): the full RegDef object.

**Response** `200 OK` with the written object. `404` if the def is absent.

**Logic**

1. Validate the body against the schema and the name.
2. If no def with that name exists, `404`.
3. Commit and push the change, with a fetch-rebase retry on a non-fast-forward. A real overlap, two commits
   changing the same def, surfaces as `409`.
4. Return the written object. The cache catches up on the next resync.

## POST /api/v1/application-definitions

Creates an AppDef. The application-definitions write interfaces mirror the registry-definitions ones, over
the AppDef object. Parked (P1).

**Response** `201 Created` with the written object. `409` if an AppDef with that name already exists.

**Logic**

As `POST /api/v1/registry-definitions`, validating the AppDef schema and writing to the
`application-definitions/` folder.

## PUT /api/v1/application-definitions/{name}

Updates an existing AppDef. Parked (P1).

**Response** `200 OK` with the written object. `404` if the AppDef is absent.

**Logic**

As `PUT /api/v1/registry-definitions/{name}`, over the AppDef object.

## Error model

Every error shares one body:

```yaml
# a stable machine-readable code
code: not_found
# a human-readable summary
message: application payments is not known
# optional, the offending field or name and other context
details:
  app: payments
```

The status codes across the interfaces:

| Code  | Meaning                                                                          |
|-------|----------------------------------------------------------------------------------|
| `400` | the request is malformed, a required parameter or body field is missing or wrong |
| `401` | the request is unauthenticated                                                   |
| `403` | the caller lacks permission for the verb                                         |
| `404` | the app, the def, or the addressed object is not found                           |
| `409` | a create on an existing def, or a write overlap on the same def                  |
| `422` | the def fails schema or name validation, or has a broken reference               |
| `503` | git is unreachable on a write, reads keep serving the cache and do not 503       |
| `500` | an unexpected internal error                                                     |

> [!NOTE]
> Reads stay available when git is unreachable. They serve the last cache and never return `503`. Only
> writes, which must reach git, can.
