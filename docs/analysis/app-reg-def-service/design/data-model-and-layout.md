# Data model and repository layout

The objects the service serves and how they live in git. The fields reference the schemas and the RegDef v2
analysis rather than being restated here in full. For the resolve response shape, see
[api-reference.md](api-reference.md).

## Application definition

A thin pointer from an application to its registry and its artifact coordinates. The service reads it to
pick the RegDef and to build the DD or SD download-info. The resolve request version plus the AppDef
`groupId` and `artifactId` form the maven coordinates of the artifact. Full fields in
[appdef.schema.json](/schemas/appdef.schema.json).

```yaml
# application name, the def identity
name: string
# the RegDef this application resolves against, by name
registryName: string
# maven group of the DD or SD artifact
groupId: string
# maven artifact of the DD or SD artifact
artifactId: string
# deploy behaviour, passed through
supportParallelDeploy: boolean
# parameter block, passed through, not interpreted by the service
deployParameters:
  <key>: string
# parameter block, passed through
technicalConfigurationParameters:
  <key>: string
# true when the artifact is an SD, not a DD
solutionDescriptor: boolean
# release-name and argocd options, carried into the resolve response
metadata:
  <key>: string
```

## Registry definition (v2)

The registry coordinates and the authentication for one registry, organized by artifact type. The service
returns these sections in the resolve response and never reads a secret from them. v2 carries an
`authConfig` that is blind: the provider and method, the non-secret parameters, and `credId` references
into a consumer-held credential store, never a secret value.

The target shape is the extended v2 worked out in
[regdef-v2-extensions.md](/docs/analysis/regdef-v2-extensions.md): the registry sections as a `registries`
list by artifact type, an `authConfig` with access roles and `credId` references, and `url` plus `repoName`
per repository. The committed [regdef-v2.schema.json](/schemas/regdef-v2.schema.json) is the current
baseline (`version: "2.0"`, per-type sections) and is being brought up to that shape. This doc restates
neither.

The service relies on three properties of the target shape:

- per artifact type the RegDef carries the registry coordinates a consumer needs to pull or push, with
  the type set the extensions analysis defines.
- the `authConfig` is blind, the method and non-secret parameters plus `credId` references, with no
  secrets in the repo.
- one registry per artifact type, so a resolve answer has at most one coordinate set per type.

## Deployment descriptor and solution descriptor

The artifact an AppDef points to by its maven coordinates.

- DD (deployment descriptor): the per-application artifact with services, configurations, smartplug, and
  charts.
- SD (solution descriptor): a list of `application:version` entries.

The service resolves the coordinates to download-info and returns it. It does not download or parse the DD
or the SD. The consumer downloads the artifact, and a consumer that holds an SD expands it into its own
resolve calls.

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
