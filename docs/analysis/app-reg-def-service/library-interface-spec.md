# App Reg Def library - interface specification

- [App Reg Def library - interface specification](#app-reg-def-library---interface-specification)
  - [Overview and scope](#overview-and-scope)
  - [Concepts and data contracts](#concepts-and-data-contracts)
  - [Operations](#operations)
    - [open\_defs](#open_defs)
    - [resolve](#resolve)
    - [download](#download)
    - [get\_regdef](#get_regdef)
    - [get\_appdef](#get_appdef)
    - [create](#create)
    - [update](#update)
    - [refresh](#refresh)
  - [Behaviors](#behaviors)
  - [Error model](#error-model)

This specifies the App Reg Def library at the contract level, enough for a developer to implement without
prescribing the internals. The key words MUST, SHOULD, and MAY follow RFC 2119. The object shapes are in
[data-model-and-layout.md](design/data-model-and-layout.md) and the schemas under `/schemas`.

## Overview and scope

The library is embedded in a consumer process and resolves an `application:version` to its artifact
download-info, from a dedicated defs git repo, using the consumer's own credentials. It is the variant of
the App Reg Def capability that is a library, not a service. Consumers today are Python, so the library is
a Python package.

It does:

- fetch the defs repo by git, a shallow and sparse checkout of the def folders.
- parse the AppDef and RegDef v2 objects.
- resolve an application and version to download-info, including the registry tier probing, the snapshot
  resolution, and minting the registry auth from the consumer's credentials.
- return a RegDef or an AppDef by name.
- create and update defs, validating them and committing to git.

It does not:

- hold or persist secrets. It reads the consumer's credentials transiently to build auth, nothing is
  stored.
- migrate v1 defs to v2. That stays a separate one-time CLI.

The consumer supplies git access to the defs repo and the registry credentials for the artifact registries.

## Concepts and data contracts

- **DefsSource** - a handle bound to a local checkout of the defs repo at a ref. All operations run against
  it.
- **DownloadInfo** - the resolve result: `downloadUrl`, `kind` (`dd.json` or `sd.yaml`), `authHeaders`
  (the minted registry auth), `registry` (the RegDef sections), and `appdef` (the appdef coordinates and
  metadata).
- **AppDef** and **RegDef** - the def objects, defined in
  [data-model-and-layout.md](design/data-model-and-layout.md) and the schemas. RegDef is the extended v2
  shape.
- **RegistryCredentials** - a lookup from a `credId` to its secret material, supplied by the consumer, for
  example from its secret store or environment. The library uses it to mint registry auth.
- **GitAuth** - a token or an ssh key for a private defs repo. Omitted for an anonymous public repo.
- **Strategy** - the tier-probing order for resolve, an enum with a default.

## Operations

### open_defs

**Purpose** open a defs repo for reading and writing, fetching it by git.

**Signature** `open_defs(git_url, ref = "main", git_auth = None) -> DefsSource`

**Parameters**

- `git_url` (string, required): the defs repo git URL.
- `ref` (string, optional, default `main`): the branch or commit to open.
- `git_auth` (GitAuth, optional): credentials for a private repo. Omit for an anonymous public repo.

**Returns** a `DefsSource` bound to a local checkout at `ref`.

**Errors** `GitUnreachable`, `GitUnauthorized`.

**Behavior**

- MUST fetch a shallow and sparse checkout limited to the `application-definitions/` and
  `registry-definitions/` folders.
- MUST authenticate with `git_auth` when it is given, and attempt anonymous access when it is not.
- The handle reflects the repo at open time. The consumer re-reads newer state with `refresh`.

### resolve

**Purpose** resolve an application and version to its artifact download-info, using the consumer's registry
credentials.

**Signature** `resolve(app, version, registry_credentials, strategy = "release-first") -> DownloadInfo`

**Parameters**

- `app` (string, required): the application name. An AppDef MUST exist for it.
- `version` (string, required): a release version or a `-SNAPSHOT` version.
- `registry_credentials` (RegistryCredentials, required): the lookup from `credId` to secret, used to mint
  auth and to probe and download.
- `strategy` (Strategy, optional, default `release-first`): the tier-probing order.

**Returns** `DownloadInfo`.

**Errors** `AppNotFound`, `RegistryNotFound`, `ArtifactNotFound`, `RegistryUnreachable`, `Unauthorized`.

**Behavior**

- MUST join the AppDef to its RegDef by `registryName`. A missing RegDef is `RegistryNotFound`.
- MUST mint the registry auth from the RegDef `authConfig` and `registry_credentials`, per the provider and
  the method.
- MUST set `kind` from the AppDef `solutionDescriptor` flag, `sd.yaml` when it marks a solution
  descriptor and `dd.json` otherwise, and probe for that artifact.
- MUST probe the maven tiers in the order `strategy` defines and return the first tier that holds the
  artifact. No tier holding it is `ArtifactNotFound`.
- For a `-SNAPSHOT` version, MUST resolve the timestamped artifact from `maven-metadata.xml`.
- MUST NOT persist any secret. It reads `registry_credentials` only to build `authHeaders`.
- Read-only, with no side effect on the defs repo.

### download

**Purpose** fetch a resolved artifact to a local path.

**Signature** `download(info, dest) -> path`

**Parameters**

- `info` (DownloadInfo, required): a resolve result.
- `dest` (path, required): the local destination.

**Returns** the local path of the downloaded file.

**Errors** `RegistryUnreachable`, `Unauthorized`, `ArtifactNotFound`.

**Behavior**

- MUST get `info.downloadUrl` with `info.authHeaders` and write it to `dest`.

### get_regdef

**Purpose** return a RegDef by name, with no application and no version.

**Signature** `get_regdef(name) -> RegDef`

**Parameters**

- `name` (string, required): the RegDef name.

**Returns** the v2 RegDef object.

**Errors** `DefNotFound`.

**Behavior**

- MUST return the RegDef as stored. Read-only.

### get_appdef

**Purpose** return an AppDef by name.

**Signature** `get_appdef(name) -> AppDef`

**Parameters**

- `name` (string, required): the AppDef name.

**Returns** the AppDef object.

**Errors** `DefNotFound`.

**Behavior**

- MUST return the AppDef as stored. Read-only.

### create

**Purpose** create a new RegDef or AppDef. The two entry points, one per object, share this contract.

**Signature** `create_regdef(obj) -> RegDef` and `create_appdef(obj) -> AppDef`

**Parameters**

- `obj` (the def object, required): the RegDef or AppDef to create.

**Returns** the written object.

**Errors** `ValidationError`, `DefExists`, `WriteConflict`, `GitUnauthorized`.

**Behavior**

- MUST validate `obj` against its schema and validate that the name is kebab-case and DNS-safe. A failure
  is `ValidationError`.
- MUST fail with `DefExists` when a def with that name already exists.
- MUST write the file to the matching folder, commit, and push with a fetch-rebase retry on a
  non-fast-forward. A real overlap, two commits changing the same def, is `WriteConflict`.
- After it returns, the same DefsSource reads the new def at once, from the local checkout.

### update

**Purpose** update an existing RegDef or AppDef. The two entry points, one per object, share this contract.

**Signature** `update_regdef(name, obj) -> RegDef` and `update_appdef(name, obj) -> AppDef`

**Parameters**

- `name` (string, required): the def name.
- `obj` (the def object, required): the full def object.

**Returns** the written object.

**Errors** `ValidationError`, `DefNotFound`, `WriteConflict`, `GitUnauthorized`.

**Behavior**

- MUST validate `obj` against its schema and the name.
- MUST fail with `DefNotFound` when no def with that name exists.
- MUST commit and push with a fetch-rebase retry on a non-fast-forward. A real overlap is `WriteConflict`.

### refresh

**Purpose** re-fetch the defs repo to the latest `ref`.

**Signature** `refresh() -> None`

**Parameters** none.

**Returns** none.

**Errors** `GitUnreachable`, `GitUnauthorized`.

**Behavior**

- MUST re-fetch and reload. Reads after it reflect the new state.

## Behaviors

```gherkin
Scenario: resolve a release version from the release tier
  Given an AppDef "billing" pointing at RegDef "shared-platform"
  And the maven release tier holds "billing:1.2.3"
  When resolve("billing", "1.2.3", creds, strategy="release-first")
  Then the DownloadInfo downloadUrl points at the release tier
  And kind is "dd.json"

Scenario: resolve an application whose artifact is a solution descriptor
  Given an AppDef "platform" with solutionDescriptor true
  When resolve("platform", "2.0.0", creds)
  Then kind is "sd.yaml"
  And the downloadUrl points at the sd.yaml artifact

Scenario: resolve a snapshot version through maven-metadata
  Given the maven snapshot tier holds "billing:1.2.3-SNAPSHOT"
  When resolve("billing", "1.2.3-SNAPSHOT", creds)
  Then the timestamped artifact is resolved from maven-metadata.xml
  And the downloadUrl points at the timestamped artifact

Scenario: the strategy sets the tier order
  Given "release-first" and "snapshot-first" strategies
  When resolve runs with each
  Then the tiers are probed in the strategy order
  And the first tier that holds the artifact wins

Scenario: the artifact is in no tier
  Given no maven tier holds "billing:9.9.9"
  When resolve("billing", "9.9.9", creds)
  Then it fails with ArtifactNotFound

Scenario: the AppDef points at a missing RegDef
  Given an AppDef whose registryName has no RegDef
  When resolve runs for that app
  Then it fails with RegistryNotFound

Scenario: open a private defs repo
  Given a private defs repo
  When open_defs(url, git_auth=token)
  Then the checkout succeeds
  And open_defs(url) without git_auth fails with GitUnauthorized

Scenario: open an anonymous public defs repo
  Given a public defs repo
  When open_defs(url) without git_auth
  Then the checkout succeeds

Scenario: create a def that already exists
  Given a RegDef "shared-platform" exists
  When create_regdef with name "shared-platform"
  Then it fails with DefExists

Scenario: update a def that does not exist
  Given no AppDef "unknown"
  When update_appdef("unknown", obj)
  Then it fails with DefNotFound

Scenario: create a def with an invalid name
  Given a def object with name "Shared Platform"
  When create_regdef(obj)
  Then it fails with ValidationError

Scenario: a write races an external push
  Given an external push lands between the local commit and the push
  When the push is a non-fast-forward on an unrelated def
  Then the write fetch-rebase retries and succeeds

Scenario: a write overlaps the same def
  Given an external push changed the same def
  When the write retries
  Then it fails with WriteConflict

Scenario: read your own write in one DefsSource
  Given create_regdef("new-registry") returned
  When get_regdef("new-registry") on the same DefsSource
  Then it returns the created RegDef
```

## Error model

| Error               | Raised when                                                              |
|---------------------|--------------------------------------------------------------------------|
| `AppNotFound`       | no AppDef exists for the application                                      |
| `RegistryNotFound`  | the AppDef `registryName` has no RegDef                                   |
| `ArtifactNotFound`  | no maven tier holds the application and version                          |
| `RegistryUnreachable` | the registry could not be reached to probe or download                 |
| `Unauthorized`      | the registry rejected the minted auth                                    |
| `DefNotFound`       | a get or update addressed a def that does not exist                      |
| `DefExists`         | a create addressed a def that already exists                             |
| `ValidationError`   | the def fails its schema, or the name is not kebab DNS-safe              |
| `WriteConflict`     | a write overlaps a concurrent change to the same def                     |
| `GitUnreachable`    | the defs repo could not be reached                                       |
| `GitUnauthorized`   | the defs repo rejected the git credentials, or none were given           |
