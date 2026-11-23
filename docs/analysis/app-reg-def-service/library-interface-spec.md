# App Reg Def resolver - interface specification

- [Overview and scope](#overview-and-scope)
- [Concepts and data contracts](#concepts-and-data-contracts)
- [Operations](#operations)
  - [open_defs](#open_defs)
  - [resolve](#resolve)
  - [provider_for](#provider_for)
  - [get_regdef](#get_regdef)
  - [get_appdef](#get_appdef)
  - [create](#create)
  - [update](#update)
  - [refresh](#refresh)
- [Behaviors](#behaviors)
- [Error model](#error-model)

This specifies the App Reg Def resolver library (working name `appregdef-resolver`) at the contract level,
enough for a developer to implement without prescribing the internals. The key words MUST, SHOULD, and MAY
follow RFC 2119. The object shapes are in [data-model-and-layout.md](design/data-model-and-layout.md) and
the schemas under `/schemas`.

## Overview and scope

The library resolves an application to its registry definition and artifact coordinates from a dedicated
defs git repo, and maps a RegDef v2 to a provider of the artifacts_finder common library
(`qubership_pipelines_common_library.v2.artifacts_finder`). It is the EnvGene-specific defs layer. It does
not search for or download artifacts. That is artifacts_finder.

It does:

- fetch the defs repo by git, a shallow and sparse checkout of the def folders.
- parse the AppDef and RegDef v2 objects.
- join an AppDef to its RegDef by `registryName`.
- map a RegDef v2 to a configured artifacts_finder provider, and an AppDef and version to an
  artifacts_finder artifact.
- create and update defs, validating them and committing to git.

It does not:

- probe registry tiers, resolve snapshots, execute the registry auth, or download artifacts. The library
  returns the provider and the artifact, and the consumer runs artifacts_finder with them.
- run as a long-lived service, hold a shared cache, or need HA. Freshness is the consumer's git fetch.
- hold or persist secrets. It passes the consumer's credentials into the provider it builds, nothing is
  stored.
- migrate v1 defs to v2. That stays a separate one-time CLI.

The handoff is: `resolve` returns a `ResolvedTarget`, and the consumer runs
`ArtifactFinder(target.provider).find_artifact_urls(artifact=target.artifact)` and `download_artifact`.
The tier probing, the snapshot resolution, the auth, and the download are artifacts_finder's contract.

The consumer supplies git access to the defs repo and the registry credentials for the artifact
registries.

## Concepts and data contracts

- **DefsSource** - a handle bound to a local checkout of the defs repo at a ref. All operations run against
  it.
- **Artifact** - an artifacts_finder artifact, the `groupId`, `artifactId`, `version`, and `extension`
  (`json` for a DD, `yaml` for an SD). The library builds it, artifacts_finder consumes it.
- **Provider** - a configured artifacts_finder provider (Artifactory, Nexus, AWS, GCP, or Azure), its
  repositories set to the RegDef tiers and its credentials from the RegDef `authConfig`. The library builds
  it, artifacts_finder consumes it.
- **ResolvedTarget** - what `resolve` returns: the `artifact`, the `kind` (`DD` or `SD`), the `provider`,
  and the `appdef` metadata. It is the handoff to artifacts_finder.
- **RegistryCredentials** - a lookup from a `credId` to its secret material, supplied by the consumer. The
  library passes it into the provider credentials.
- **GitAuth** - a token or an ssh key for a private defs repo. Omitted for an anonymous public repo.
- **TierOrder** - the order the RegDef tiers are listed in the provider, which sets artifacts_finder's
  probe order. An optional input with a default.

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

**Purpose** resolve an application and version to the artifact coordinates and the configured provider that
artifacts_finder needs to fetch it.

**Signature** `resolve(app, version, registry_credentials, tier_order = default) -> ResolvedTarget`

**Parameters**

- `app` (string, required): the application name. An AppDef MUST exist for it.
- `version` (string, required): a release version or a `-SNAPSHOT` version. It is carried into the
  artifact coordinates, not interpreted here.
- `registry_credentials` (RegistryCredentials, required): the lookup from `credId` to secret, passed into
  the provider credentials.
- `tier_order` (TierOrder, optional, default release-first): the order the tiers are listed in the
  provider.

**Returns** a `ResolvedTarget`.

**Errors** `AppNotFound`, `RegistryNotFound`, `UnsupportedProvider`, `UnsupportedAuthMethod`.

**Behavior**

- MUST join the AppDef to its RegDef by `registryName`. A missing RegDef is `RegistryNotFound`.
- MUST build the artifact from the AppDef `groupId` and `artifactId`, the `version`, and the extension,
  `json` for a DD and `yaml` for an SD, chosen by the AppDef `solutionDescriptor` flag. The `kind` is `DD`
  or `SD` accordingly.
- MUST build the provider by mapping the RegDef: the provider type from the RegDef provider, the
  repositories from the RegDef tiers in `tier_order`, and the credentials from the RegDef `authConfig` and
  `registry_credentials`.
- MUST fail with `UnsupportedProvider` or `UnsupportedAuthMethod` when the RegDef uses a provider or a
  method artifacts_finder does not support.
- MUST NOT contact the registry or download anything. It returns the inputs for artifacts_finder.
- Read-only, with no side effect on the defs repo.

### provider_for

**Purpose** map a RegDef to a configured artifacts_finder provider, for flows that address a registry
directly, such as publish and promote.

**Signature** `provider_for(regdef, registry_credentials, tier_order = default) -> Provider`

**Parameters**

- `regdef` (RegDef, required): the registry definition.
- `registry_credentials` (RegistryCredentials, required): passed into the provider credentials.
- `tier_order` (TierOrder, optional, default release-first).

**Returns** a configured artifacts_finder `Provider`.

**Errors** `UnsupportedProvider`, `UnsupportedAuthMethod`.

**Behavior**

- MUST map the RegDef provider, the tiers in `tier_order`, and the `authConfig` with
  `registry_credentials` to the provider.
- MUST NOT contact the registry.

### get_regdef

**Purpose** return a RegDef by name.

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
Scenario: resolve maps a nexus-backed application to a provider and an artifact
  Given an AppDef "billing" pointing at a nexus RegDef "shared-platform"
  When resolve("billing", "1.2.3", creds)
  Then the ResolvedTarget artifact is billing's groupId, artifactId, "1.2.3", extension "json"
  And kind is "DD"
  And the provider is a Nexus provider with the RegDef tiers as its repositories

Scenario: resolve an application whose artifact is a solution descriptor
  Given an AppDef "platform" with solutionDescriptor true
  When resolve("platform", "2.0.0", creds)
  Then the artifact extension is "yaml"
  And kind is "SD"

Scenario: resolve maps an aws assume-role RegDef to aws credentials
  Given a RegDef whose authConfig is aws with assumeRole
  When resolve runs for an app on that RegDef
  Then the provider carries assume-role credentials built from registry_credentials

Scenario: the tier order sets the provider repository order
  Given a RegDef with snapshot, staging, and release tiers
  When resolve runs with tier_order release-first
  Then the provider repositories list release before snapshot

Scenario: the application is unknown
  Given no AppDef "unknown"
  When resolve("unknown", "1.0.0", creds)
  Then it fails with AppNotFound

Scenario: the AppDef points at a missing RegDef
  Given an AppDef whose registryName has no RegDef
  When resolve runs for that app
  Then it fails with RegistryNotFound

Scenario: the RegDef provider is unsupported
  Given a RegDef with a provider artifacts_finder does not support
  When resolve runs for an app on that RegDef
  Then it fails with UnsupportedProvider

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

Scenario: a write overlaps the same def
  Given an external push changed the same def
  When the write fetch-rebase retries
  Then it fails with WriteConflict

Scenario: read your own write in one DefsSource
  Given create_regdef("new-registry") returned
  When get_regdef("new-registry") on the same DefsSource
  Then it returns the created RegDef
```

## Error model

The library raises the defs and mapping errors below. The registry errors, an artifact not found, a
registry unreachable, or a registry auth rejection, are raised by artifacts_finder when the consumer runs
it, not by this library.

| Error                   | Raised when                                                          |
|-------------------------|---------------------------------------------------------------------|
| `AppNotFound`           | no AppDef exists for the application                                 |
| `RegistryNotFound`      | the AppDef `registryName` has no RegDef                              |
| `UnsupportedProvider`   | the RegDef provider has no artifacts_finder provider                 |
| `UnsupportedAuthMethod` | the RegDef `authMethod` has no artifacts_finder credentials mapping  |
| `DefNotFound`           | a get or update addressed a def that does not exist                  |
| `DefExists`             | a create addressed a def that already exists                         |
| `ValidationError`       | the def fails its schema, or the name is not kebab DNS-safe         |
| `WriteConflict`         | a write overlaps a concurrent change to the same def                 |
| `GitUnreachable`        | the defs repo could not be reached                                   |
| `GitUnauthorized`       | the defs repo rejected the git credentials, or none were given       |
