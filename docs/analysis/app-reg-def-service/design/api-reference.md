# API reference

The human-readable companion to `openapi.yaml`. `openapi.yaml` is the machine-readable contract, this page
explains each interface and the logic behind it. The objects in the payloads are in
[data-model-and-layout.md](data-model-and-layout.md).

## Conventions

- base path `/api/v1`, media type `application/json`.
- every request is authorized. Read verbs and write verbs may need different permissions. The authn model
  is in [deployment-and-operations.md](deployment-and-operations.md).
- `zone` is an optional query parameter on the read interfaces. There is one default zone today, and it is
  reserved for multizone.
- errors share one shape and one status-code catalog, in [Error model](#error-model). Each interface lists
  the codes it returns.
- `getAppDef` (open, O2) and `listRegDefs` / `listAppDefs` (open, O3) are not specified here yet. The write
  interfaces are the parked target shape (P1), their semantics are settled but not built.

## resolve

`GET /api/v1/resolve`

Turns one `application:version` into everything a consumer needs to pull the artifact, blind on
credentials.

### Parameters

- `app` (query, required): the application name.
- `version` (query, required): the application version.
- `zone` (query, optional): the registry zone, one default today.

### Response

`200 OK` with the resolved payload:

```yaml
# the DD or SD at the resolved coordinates
artifact:
  kind:        # DD or SD
  gav:         # group, artifact, version
  downloadUrl: # where the consumer downloads it
# all registry sections from the RegDef, see data-model-and-layout.md
registry:
# provider, method, non-secret parameters, and credId references, no secret
authReady:
# release-name, argocd options, and the appdef metadata
appdef:
```

### Processing logic

1. Validate the request. `app` and `version` are required, `zone` defaults to the one zone.
2. Look up the AppDef by `app` in the cache. If it is absent, `404`.
3. Read `registryName`, `groupId`, `artifactId`, and `solutionDescriptor` from the AppDef.
4. Look up the RegDef named `registryName` in the cache. If it is absent, `422`, the def points at a
   registry that does not exist.
5. Pick DD or SD from the AppDef `solutionDescriptor` flag.
6. Build the artifact download-info. The `groupId`, `artifactId`, and the request `version` are the maven
   coordinates, and the download URL comes from the matching registry section of the RegDef.
7. Assemble `authReady` from the RegDef `authConfig`, the provider, the method, the non-secret parameters,
   and the `credId` references. No secret is read or returned.
8. Return the artifact download-info, all registry sections, `authReady`, and the appdef metadata.

The consumer downloads the artifact and builds any sub-artifact URLs itself from the registry sections.

## resolveBatch

`POST /api/v1/resolve:batch`

The `resolve` result for a list of entries in one call.

### Parameters

- body (required): a list of entries, each with `app` and `version`.
- `zone` (query, optional): applies to the whole batch.

### Response

`200 OK` with one result per entry, in request order. An entry that fails to resolve carries its own error
in place of a payload, so one bad entry does not fail the batch.

### Processing logic

1. Validate the body. It is a non-empty list of `app` and `version` pairs.
2. Run the `resolve` logic for each entry against the cache.
3. Collect a payload or a per-entry error for each, and return the list.

## getRegDef

`GET /api/v1/registry-definitions/{name}`

Returns a RegDef by name, with no application and no version. It is the version-independent way to reach a
registry, for publish and promote flows that address a registry directly.

### Parameters

- `name` (path, required): the RegDef name.
- `zone` (query, optional).

### Response

`200 OK` with the v2 RegDef object. If the RegDef is absent, `404`.

### Processing logic

1. Look up the RegDef by `name` in the cache. If it is absent, `404`.
2. Return the RegDef object as stored, v2.

## create

`POST /api/v1/registry-definitions` and `POST /api/v1/application-definitions`

Creates a new RegDef or AppDef. Parked (P1), the shape is settled. The write is eventually consistent, the
response carries the written object and the cache catches up on the next resync.

### Parameters

- body (required): the def object.

### Response

`201 Created` with the written object. `409` if a def with that name already exists.

### Processing logic

1. Validate the body against the schema, and validate or normalize the name to the kebab DNS-safe
   convention.
2. If a def with that name already exists in git, `409`.
3. Commit and push the new file to the defs repo, with a fetch-rebase retry on a non-fast-forward.
4. Return the written object. A following `resolve` sees it once the push-triggered resync lands.

## update

`PUT /api/v1/registry-definitions/{name}` and `PUT /api/v1/application-definitions/{name}`

Updates an existing RegDef or AppDef. Parked (P1), the shape is settled.

### Parameters

- `name` (path, required): the def name.
- body (required): the full def object.

### Response

`200 OK` with the written object. `404` if the def is absent.

### Processing logic

1. Validate the body against the schema and the name.
2. If no def with that name exists in git, `404`.
3. Commit and push the change, with a fetch-rebase retry on a non-fast-forward. A real overlap, two commits
   changing the same def, surfaces as `409`.
4. Return the written object. The cache catches up on the next resync.

## Error model

Every error shares one body:

```yaml
# a stable machine-readable code
code:
# a human-readable summary
message:
# optional, the offending field or name and other context
details:
```

The status codes across the interfaces:

| Code  | Meaning                                                                           |
|-------|-----------------------------------------------------------------------------------|
| `400` | the request is malformed, a required parameter or body field is missing or wrong  |
| `401` | the request is unauthenticated                                                    |
| `403` | the caller lacks permission for the verb                                          |
| `404` | the app, the def, or the addressed object is not found                            |
| `409` | a create on an existing def, or a write overlap on the same def                   |
| `422` | the def is unprocessable, it fails schema or name validation or has a broken reference |
| `503` | git is unreachable on a write. Reads keep serving the cache and do not 503        |
| `500` | an unexpected internal error                                                      |

Reads stay available when git is unreachable, they serve the last cache and never return `503`. Only writes,
which must reach git, can.
