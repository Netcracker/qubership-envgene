# NAME-3

- [NAME-3](#name-3)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

NAME-3 checks kebab-case in connected filenames, cluster/environment directory
names and used namespace names. YAML fields and enum values are outside its
scope. All findings are Information / Review; no names are changed.

## Input parameters

These are inputs to `check(index, connections=None)`, not additional CLI options.

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Rule argument from repository discovery | Yes | None | `RepoIndex.root`, clusters/environments, Resource Profile records and bindings | Supplies repository boundary, used directories and profile resolution |
| `connections` | Optional rule argument / shared resolver | No | `compute_connections(index)` | `Connections.selected_paths`, `parameter_files`, `parameter_uses` | Supplies selected paths, authoritative ParameterSet spellings and namespace targets |

## Processing flow

1. **Collect connected paths and targets**

   1. Reuse `connections`, or compute it from `index` when omitted.
   2. Start a physical-path map from `connections.selected_paths`. Replace each
      ParameterSet entry's display path with its selected `parameter_files`
      record's path. An unused alias cannot replace the selected spelling.
   3. Collect target names from `parameter_uses`, separately for each environment.
      Only resolved ParameterSet uses contribute.

2. **Check used directories and environment definitions**

   1. Visit indexed clusters with at least one discovered environment. Check the
      cluster name as `Cluster directory` and each environment name as
      `Environment directory`, including environments with unreadable definitions.
   2. Add each existing `Inventory/env_definition.yml` to the file map by
      resolved physical path, preserving the definition path as its spelling.
   3. Add Resource Profile targets only when `resolve_named_reference` resolves
      their binding in that environment, using the shared profile priority.
   4. For each collected target, check a namespace only if it is an existing
      immediate child of that environment's `Namespaces/`, its exact name equals
      the target, and its resolved path stays inside the repository. Exclude
      `.` and `..`, and `cloud` case-insensitively. Use kind `Namespace`.
   5. For all directory kinds, skip `.git` paths and exact names in the layout
      list: `Inventory`, `Namespaces`, `parameters`, `credentials`, `Credentials`,
      `resource_profiles`, `rp_override`, `Profiles`, `configuration`,
      `configurations`, `shared-template-variables`, `shared_template_variables`,
      `cloud-passport`, `cloud-passports`, `app-deployer`, `cloud-deployer`.

3. **Check selected filenames**

   1. Visit the deduplicated file map in path order. Keep paths lexically under
      `index.root/environments`, resolving inside `index.root`, with no `.git`
      component below `environments/`.
   2. Accept suffixes `.yml`, `.yaml`, `.json`, `.yml.j2`, `.yaml.j2`, `.json.j2`.
      A suffix alone does not establish use.
   3. Obtain the stem with `paramset_stem` (strip `.j2`, then the data extension)
      and check it as kind `File`. Used hidden names have no exemption.
      Generator inputs such as `env_definition.yml` and selected
      `inventory_generation_creds.yml` have no filename exemption either.

4. **Validate names and return findings**

   1. Require a full match of `^[a-z0-9]+(?:-[a-z0-9]+)*$` for every name
      selected in steps 2 and 3.
   2. Emit one finding per failing name at its path, line 1, column 1.
   3. Sort findings by path, key and line.

## Result

The result is a list of `NAME-3` findings with `severity=information`,
`issue_type=Information`, `action=Review`, `key` equal to the failing name,
`scope` equal to its kind, one location and empty `related`.

- Message: `{kind} {name!r} is not kebab-case.` Keep the kind's exact spelling
  from the processing flow.
- Hint: `Review whether this name can be kebab-case. Do not rename it if generation or other logic still depends on the current spelling.`
- Catalog description: `Filenames, directories, and namespaces use kebab-case`.

Console output includes the location, severity, message and hint; HTML shows the
location and Information / Review chips. An empty block is `NAME-3` followed by
`No findings`; an ordinary discovered environment is not empty because its
`env_definition` stem contains an underscore.

## Error handling

**1a.** Unselected and shadowed files contribute no names. Unused clusters and
namespace directories are ignored, even if their spelling fails the regex.

**2a.** An empty or dangling binding does not establish namespace use. Generated
directory presence and unknown template inputs do not establish use either.

**2b.** An unreadable environment definition does not prevent checking the
already discovered environment, its cluster or its definition filename.

**3a.** Paths outside the permitted subtree, escaping the repository, under
`.git`, or with other suffixes are skipped. NAME-3 checks names and does not
require selected file content to parse successfully.

## Example

Consider a discovered environment `environments/Cluster_01/Env_01` with
`Inventory/env_definition.yml`, and a resolved ParameterSet binding targeting
`Foo` that selects `Inventory/parameters/Cloud_Deploy.yml`. Assume its
`Namespaces/Foo` directory exists and there are no other selected files.

The rule produces five Information / Review findings:

| Kind | Key |
| --- | --- |
| Cluster directory | `Cluster_01` |
| Environment directory | `Env_01` |
| File | `env_definition` |
| File | `Cloud_Deploy` |
| Namespace | `Foo` |

Without a resolved ParameterSet or profile binding to `Foo`, the namespace
finding disappears. A standalone unused `Cluster_01` directory or an unbound
`Cloud_Deploy.yml` produces no finding.

## Related documentation

- [Connected entities](connections.md)
- [Rule implementation](../../src/envgene_linter/rules/name3.py)
- [Rule tests](../../tests/test_name3.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Reporting](../../src/envgene_linter/report.py)
