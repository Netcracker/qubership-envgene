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

A dedicated defs repo, separate from the instance repos, is the source of truth. Flat, one file per def.

```text
application-definitions/
  <app-name>.yaml           # one AppDef per file
registry-definitions/
  <registry-name>.yaml      # one RegDef per file
```

- one branch is the source of truth. Changes may optionally go through a manual merge-request workflow.
- zero secrets in the repo, `credId` references only, no encryption.
- zone folders are deferred. There is one default zone today, and the layout stays flat until multizone
  lands.

## Naming conventions

Casing by role, so the same identity reads consistently across the file system and the object.

- path identifiers, the folders, the file names, and the def `name`, are kebab-case and DNS-safe.
- object fields are camelCase.
- a `kind`, where an object carries one, is PascalCase, for example `RegistryDefinition`.
- the file stem equals the def `name`, so `registry-definitions/shared-platform.yaml` holds the RegDef
  named `shared-platform`.
