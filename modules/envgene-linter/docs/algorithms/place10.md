# PLACE-10

- [PLACE-10](#place-10)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-10 (MUST) directly compares each connected entity's directory with the directory required for its type. Correct placement is silent; incorrect placement produces Warning / Fix. The check runs independently of other rules, including PLACE-9.

| Type | Required directory |
| --- | --- |
| ParameterSet | `parameters/` |
| Resource Profile Override | `resource_profiles/` |
| Shared Template Variables | `shared-template-variables/` |
| Shared credentials | `credentials/` |
| Cloud Passport | `cloud-passport/` |

Type comes from the established connection, not an inference from YAML content. Unused files and unresolved references remain outside the check.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Repository discovery | Yes | None | `RepoIndex` | Repository and indexed scope paths |
| `connections` | Engine / shared resolver | No | Computed when omitted | Typed selected physical paths | Selects files and their entity types |
| `envTemplate.sharedTemplateVariables` | Environment definition | No | Empty list | List of exact file stems | Establishes Shared Template Variable use alongside existing typed selections |

## Processing flow

1. **Select connected typed files**

   1. Reuse the supplied connection index or compute it from the discovered repository.
   2. Collect selected ParameterSets, Resource Profile Overrides, Shared Template Variables, shared credentials and Cloud Passports.
   3. Keep each physical file once per entity type. A file used as two types must meet each type's requirement independently.

2. **Resolve Shared Template Variable bindings**

   1. Read string entries of the `envTemplate.sharedTemplateVariables` list. Skip malformed containers, non-string entries and dynamic Jinja references.
   2. Search these scope directories in order: Inventory/configuration, Inventory/configurations, cluster/configuration, cluster/configurations, environments/configuration, environments/configurations, then Inventory itself.
   3. Within a directory, search recursively for the exact `.yml`/`.yaml` filename stem, using the local generator's first-match traversal order. Stop at the first matching file; do not merge multiple files with that name.
   4. Do not follow directory symlinks or traverse `.git`. Reject external/unsafe matching winners without promoting a lower-priority file. No YAML content is needed to establish this input's use.
   5. Add selected paths to global and per-environment connections. The canonical Inventory/shared-template-variables directory can resolve through the final Inventory search. Do not invent use for unresolved directories.

3. **Determine the actual scope and directory**

   1. Resolve physical identity and exclude external and `.git` paths.
   2. Find the deepest matching indexed scope base: an environment Inventory, a cluster, or repository environments.
   3. Compare the first directory component below that base with the type's exact required directory. Nested paths inside that directory are allowed; a canonical name nested under a different directory does not qualify.
   4. If the selected physical file is inside the repository but outside these scope bases, treat it as misplaced and use repository environments as the suggested destination base.

4. **Create findings for mismatches**

   1. Correct directory: produce no finding. Incorrect directory: identify the type, file and expected directory in a Warning / Fix finding.
   2. Point to the relevant selected file at `1:1`; do not read content, rename files or move them.
   3. Do not suppress a finding because another rule also reports this file. Deduplicate only the same physical file/type pair.
   4. Sort findings by path, key and line.

## Result

The returned findings use `PLACE-10`, severity `warning`, issue type `Warning`, action `Fix`, the filename stem as key and the actual scope as scope. Each has one file location at `1:1` and a hint naming the expected directory.

Catalog description: `Entities belong in their type directories`. The console always prints eighteen rule headers; PLACE-10 follows PLACE-9 and precedes SEC-1, while SEC-5 follows SEC-4 later in the catalog. A silent block shows `No findings`. HTML retains only sections with findings. Findings preserve CLI exit code `0`; no new flags or automatic edits are introduced.

## Error handling

**1a.** Unused files, unresolved references and unselected ambiguous passports give no finding. Existing Jinja selection restrictions remain in force.

**2a.** The local generator resolves Shared Template Variables through legacy configuration directories, whereas PLACE-10 requires `shared-template-variables/`. The rule reports the used legacy placement; it does not change generator lookup or guess new supported search paths.

**2b / 3a.** External and `.git` inputs are excluded. An unsafe matching winner must not cause a lower-priority file to be treated as used.

**4a.** Invalid or empty YAML does not suppress the placement check when selection established use. The rule does not infer types, validate schemas, read credentials or check missing files.

## Example

A selected ParameterSet in `Inventory/parameters/service-deploy.yml` passes. A selected Resource Profile Override at `Inventory/parameters/service-profile.yml` fails: its required directory is `resource_profiles/`.

```yaml
# Inventory/env_definition.yml
envTemplate:
  envSpecificResourceProfiles:
    cloud: service-profile
```

If the selected file is `Inventory/rp_override/service-profile.yml`, PLACE-10 produces one warning pointing to that file and recommends `Inventory/resource_profiles/`. An unreferenced copy in `rp_override/` is silent.

Shared credentials selected from `shared-credentials/` fail the directory check even though the generator can resolve them. A selected passport in `cloud-passports/` fails PLACE-10 independently of PLACE-9.

A Shared Template Variable selected as `common` from `Inventory/configuration/common.yml` requires `Inventory/shared-template-variables/`. A selected nested `Inventory/resource_profiles/team/service-profile.yml` is valid; `Inventory/parameters/resource_profiles/service-profile.yml` is not.

## Related documentation

- [Connected entities](connections.md)
- [Implementation](../../src/envgene_linter/rules/place10.py)
- [Tests](../../tests/test_place10.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Design](../superpowers/specs/2026-09-11-place10-design.md)
