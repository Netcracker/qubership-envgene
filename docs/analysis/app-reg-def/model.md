# Data model and repository layout

The objects the App Reg Def capability works with, in brief. The full field definitions live in the schemas
and the RegDef v2 analysis linked below, not restated here. The behavior that uses these objects is in
[library/interface-spec.md](library/interface-spec.md).

## Objects

- **AppDef** - the stored application definition. [appdef.schema.json](/schemas/appdef.schema.json).
- **RegDef** - the stored registry definition.
  [regdef.schema.json](/schemas/regdef.schema.json)
  [regdef-v2-extensions.md](/docs/analysis/regdef-v2-extensions.md).
- **Application** - the runtime join of an AppDef and its RegDef, reused from artifact-searcher's
  `Application` model and carrying the full AppDef attributes. This is what `resolve` returns.
- **Artifact** - the artifacts_finder coordinates of the DD or SD, the `groupId`, `artifactId`, `version`,
  and `extension`.
- **ArtifactProvider** - a configured artifacts_finder provider, its type, repositories, and credentials.
- **DD and SD** - the deployment descriptor (`dd.json`) and the solution descriptor (`sd.yaml`) the
  coordinates point to.

## Repository layout

A dedicated defs repo, separate from the instance repos, is the source of truth. The defs are flat, one
file per def, with the schemas alongside.

```text
schemas/
  application-definition/
    v1.schema.json
  registry-definition/
    v1.schema.json
    v2.schema.json
application-definitions/
  <app-name>.yaml           # one AppDef per file
registry-definitions/
  <registry-name>.yaml      # one RegDef per file
```

- one branch is the source of truth. Changes may optionally go through a manual merge-request workflow.
- zero secrets in the repo, `credId` references only, no encryption.
- zone folders are deferred. There is one default zone today, and the layout stays flat until multizone
  lands.

## Schema and validation

The schemas live in the repo, so validation is versioned with the data and decoupled from a code release.

- each def carries a `kind` (`ApplicationDefinition`, `RegistryDefinition`), added by T2, and a RegDef also
  carries its `version` (absent for v1, `"2.0"` for v2). The validator maps `(kind, version)` to
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

- path identifiers, the folders, the file names, and the def `name`, are kebab-case and DNS-safe.
- object fields are camelCase.
- a `kind`, where an object carries one, is PascalCase, for example `RegistryDefinition`.
- the file stem equals the def `name`, so `registry-definitions/shared-platform.yaml` holds the RegDef
  named `shared-platform`.
