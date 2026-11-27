# Data model and repository layout

The objects the App Reg Def capability works with, in brief. The full field definitions live in the schemas
and the RegDef v2 analysis linked below, not restated here. The behavior that uses these objects is in
[library/interface-spec.md](library/interface-spec.md).

## Objects

- **AppDef** - the stored application definition.
  - [description](/docs/envgene-objects.md#application-definition)
  - [appdef.schema.json](/schemas/appdef.schema.json)
- **RegDef** - the stored registry definition.
  - [description](/docs/envgene-objects.md#registry-definition)
  - [regdef.schema.json](/schemas/regdef.schema.json)
  - [regdef-v2-extensions.md](/docs/analysis/regdef-v2-extensions.md)
  - [regdef-v2-extended.schema.json](/docs/analysis/regdef-v2-extensions/regdef-v2-extended.schema.json)
- **client** - the opened appregdef-client over a backend, returned by `open_defs` (Git) or `connect`
  (service). One object with the defs-store operations.
  See [library/interface-spec.md](library/interface-spec.md).
- **Application** - the runtime join of an AppDef and its RegDef, reused from artifact-searcher's
  - [`Application` model](/modules/artifact-searcher/artifact_searcher/utils/models.py) and carrying the full
    AppDef attributes. This is what `resolve` returns.
- **Artifact** - the artifacts_finder coordinates of the DD or SD, the `groupId`, `artifactId`, `version`,
  and `extension`.
- **ArtifactProvider** - a configured artifacts_finder provider, its type, repositories, and credentials.
- **REGISTRY_CREDENTIALS** - the consumer CI/CD variable holding the registry secrets, keyed by `credId`.
  The caller passes it into `create_provider`, the capability never stores it.
  - [description](/docs/analysis/regdef-v2-extensions.md#ext2--the-registry_credentials-variable)
- **DD and SD** - the deployment descriptor (`dd.json`) and the solution descriptor (`sd.yaml`) the
  coordinates point to.

## Repository layout

A dedicated defs repository, separate from the instance repositories, is the source of truth. The defs are
flat, one
file per def, with the schemas alongside.

```text
schemas/
  application-definition/
    v1.schema.json
  registry-definition/
    v1.schema.json
    v2.schema.json
AppDefs/
  <app-name>.yaml           # one AppDef per file
RegDefs/
  <registry-name>.yaml      # one RegDef per file
```

- the def folders are `AppDefs/` and `RegDefs/`, matching the existing central registry repository, so the
  migration needs no folder move. This is a deliberate exception to the kebab-case path convention, kept
  for these two fixed folders.
- one branch is the source of truth. Changes may optionally go through a manual merge-request workflow.
- zero secrets in the repository, `credId` references only, no encryption.
- zone folders are deferred. There is one default zone today, and the layout stays flat until multizone
  lands.

## Schema and validation

The schemas live in the repository, so validation is versioned with the data and decoupled from a code
release.

- each def carries a `kind` (`ApplicationDefinition`, `RegistryDefinition`), and a RegDef also carries its
  `version` (absent for v1, `"2.0"` for v2). The validator maps `(kind, version)` to
  `schemas/<kind-in-kebab>/<major>.schema.json`.
- the service and the library validate each def against that committed schema, not a schema baked into the
  code. A new def shape ships as a schema commit, with no code release.
- within a major, changes are additive-only, new optional fields, so an older reader still validates a
  newer def. A breaking change bumps the major, a new `<major>.schema.json` file plus a migration.
- each schema pins its JSON Schema draft in `$schema`, so the validator behaves the same everywhere.
- behavior stays in code. The schema validates the shape, while the mapping of a RegDef to a provider and
  its auth is code, so a new auth method needs a code change, not only a schema.

## Naming conventions

Casing by role, so the same identity reads consistently across the file system and the object.

<!-- - path identifiers, the def filenames and the def `name`, are kebab-case and DNS-safe. The two container
  folders `AppDefs/` and `RegDefs/` are the inherited exception (see Repository layout). -->
- object fields are camelCase.
- a `kind`, where an object carries one, is PascalCase, for example `RegistryDefinition`.
- the filename without the extension equals the def `name`, so `RegDefs/shared-platform.yaml` holds the
  RegDef named `shared-platform`.
