# API reference

- [Conventions](#conventions)
- [GET /api/v1/resolve](#get-apiv1resolve)
- [POST /api/v1/resolve:batch](#post-apiv1resolvebatch)
- [GET /api/v1/registry-definitions/{name}](#get-apiv1registry-definitionsname)
- [POST /api/v1/registry-definitions](#post-apiv1registry-definitions)
- [PUT /api/v1/registry-definitions/{name}](#put-apiv1registry-definitionsname)
- [POST /api/v1/application-definitions](#post-apiv1application-definitions)
- [PUT /api/v1/application-definitions/{name}](#put-apiv1application-definitionsname)
- [Error model](#error-model)

The App Reg Def service exposes a small HTTP API. The read interfaces turn an `application:version`, or a
registry name, into the coordinates and the blind auth a consumer needs to pull artifacts. The write
interfaces create and update defs in git. This page is the human-readable companion to `openapi.yaml`,
which is the machine-readable contract. The objects in the payloads are in
[data-model-and-layout.md](data-model-and-layout.md).

## Conventions

- base path `/api/v1`, media type `application/json`.
- every request is authorized. Read verbs and write verbs may need different permissions. The authn model
  is in [deployment-and-operations.md](deployment-and-operations.md).
- `zone` is an optional query parameter on the read interfaces. There is one default zone today, and it is
  reserved for multizone.
- errors share one shape and one status-code catalog, in [Error model](#error-model). Each interface notes
  the codes it returns.
- `getAppDef` (open, O2) and `listRegDefs` / `listAppDefs` (open, O3) are not specified here yet. The write
  interfaces are the parked target shape (P1), their semantics are settled but not built.

## GET /api/v1/resolve

Resolves one application and version to its artifact download-info, all registry sections, the blind
`authReady`, and the appdef metadata.

**Parameters**

- `app` (query, required): the application name.
- `version` (query, required): the application version.
- `zone` (query, optional): the registry zone, one default today.

**Request**

```text
GET /api/v1/resolve?app=billing&version=1.2.3&zone=default
```

**Response** `200 OK`

```yaml
artifact:
  kind: DD
  gav: com.example.billing:billing-dd:1.2.3
  downloadUrl: https://nexus.example.com/repository/maven-releases/com/example/billing/billing-dd/1.2.3/billing-dd-1.2.3.zip
# all registry sections from the RegDef, see data-model-and-layout.md
registry:
  maven:
    release:
      url: https://nexus.example.com/repository/maven-releases
      repoName: maven-releases
  # ... docker, helm, and the other sections
# provider, method, non-secret parameters, and credId references, no secret
authReady:
  provider: nexus
  authMethod: userPass
  accessRoles:
    read: nexus-read
# release-name, argocd options, and the appdef metadata
appdef:
  releaseName: billing
```

**Logic**

1. Validate the request. `app` and `version` are required, `zone` defaults to the one zone.
2. Look up the AppDef by `app` in the cache. If it is absent, `404`.
3. Read `registryName`, `groupId`, `artifactId`, and `solutionDescriptor` from the AppDef.
4. Look up the RegDef named `registryName`. If it is absent, `422`, the def points at a registry that does
   not exist.
5. Pick DD or SD from the AppDef `solutionDescriptor` flag.
6. Build the artifact download-info. `groupId`, `artifactId`, and the request `version` are the maven
   coordinates, and the download URL comes from the matching registry section of the RegDef.
7. Assemble `authReady` from the RegDef `authConfig`, the provider, the method, the non-secret parameters,
   and the `credId` references. No secret is read or returned.
8. Return the artifact download-info, all registry sections, `authReady`, and the appdef metadata.

## POST /api/v1/resolve:batch

Resolves a list of entries in one call, each like `GET /api/v1/resolve`.

**Parameters**

- body (required): a list of entries, each with `app` and `version`.
- `zone` (query, optional): applies to the whole batch.

**Request**

```yaml
- app: billing
  version: 1.2.3
- app: payments
  version: 4.5.6
```

**Response** `200 OK`

```yaml
# one result per entry, in request order
- app: billing
  version: 1.2.3
  artifact:
    kind: DD
    gav: com.example.billing:billing-dd:1.2.3
    downloadUrl: https://nexus.example.com/repository/maven-releases/com/example/billing/billing-dd/1.2.3/billing-dd-1.2.3.zip
  # registry, authReady, and appdef as in resolve
- app: payments
  version: 4.5.6
  error:
    code: not_found
    message: application payments is not known
```

**Logic**

1. Validate the body, a non-empty list of `app` and `version` pairs.
2. Run the resolve logic for each entry against the cache.
3. Return a payload or a per-entry error for each, so one bad entry does not fail the batch.

## GET /api/v1/registry-definitions/{name}

Returns a RegDef by name, with no application and no version. The version-independent way to reach a
registry, for publish and promote flows that address a registry directly.

**Parameters**

- `name` (path, required): the RegDef name.
- `zone` (query, optional).

**Request**

```text
GET /api/v1/registry-definitions/shared-platform
```

**Response** `200 OK`

```yaml
# the v2 RegDef object, see data-model-and-layout.md and regdef-v2-extensions.md
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
2. Return the RegDef object as stored, v2.

## POST /api/v1/registry-definitions

Creates a RegDef. Parked (P1), the shape is settled. The write is eventually consistent, the response
carries the written object and the cache catches up on the next resync.

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

**Response** `201 Created`

```yaml
# the written object, echoing the request
name: shared-platform
version: v2
# ... the rest as submitted
```

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

**Request**

```yaml
# PUT /api/v1/registry-definitions/shared-platform
name: shared-platform
version: v2
authConfig:
  nexus-up:
    provider: nexus
    authMethod: userPass
    accessRoles:
      read: nexus-read
      publish: nexus-publish
registries:
  - artifactType: maven
    authConfig: nexus-up
    repositories:
      - type: release
        url: https://nexus.example.com/repository/maven-releases
        repoName: maven-releases
```

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

**Parameters**

- body (required): the AppDef object.

**Request**

```yaml
name: billing
registryName: shared-platform
groupId: com.example.billing
artifactId: billing-dd
supportParallelDeploy: false
deployParameters:
  BILLING_DB_HOST: billing-db.example.local
technicalConfigurationParameters:
  LOG_LEVEL: INFO
```

**Response** `201 Created` with the written object. `409` if an AppDef with that name already exists.

**Logic**

As `POST /api/v1/registry-definitions`, validating the AppDef schema and writing to the
`application-definitions/` folder.

## PUT /api/v1/application-definitions/{name}

Updates an existing AppDef. Parked (P1).

**Parameters**

- `name` (path, required): the AppDef name.
- body (required): the full AppDef object.

**Request**

```yaml
# PUT /api/v1/application-definitions/billing
name: billing
registryName: shared-platform
groupId: com.example.billing
artifactId: billing-dd
supportParallelDeploy: true
deployParameters:
  BILLING_DB_HOST: billing-db.example.local
technicalConfigurationParameters:
  LOG_LEVEL: DEBUG
```

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
| `401` | the request is unauthenticated                                                    |
| `403` | the caller lacks permission for the verb                                          |
| `404` | the app, the def, or the addressed object is not found                           |
| `409` | a create on an existing def, or a write overlap on the same def                  |
| `422` | the def fails schema or name validation, or has a broken reference               |
| `503` | git is unreachable on a write, reads keep serving the cache and do not 503       |
| `500` | an unexpected internal error                                                     |

> [!NOTE]
> Reads stay available when git is unreachable. They serve the last cache and never return `503`. Only
> writes, which must reach git, can.
