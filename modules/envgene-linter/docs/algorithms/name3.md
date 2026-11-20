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

NAME-3 checks connected authored filenames and cluster and environment directory names. It follows the [authored
configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md). Generated Namespace directory names are
excluded. YAML fields and enum values are outside its scope. All findings are Information / Review.

## Input parameters

These are inputs to `check(index, connections=None)`, not additional CLI options.

| Parameter     | Source                                   | Required | Default                      | Values / format                                                   | Effect                                                        |
|---------------|------------------------------------------|----------|------------------------------|-------------------------------------------------------------------|---------------------------------------------------------------|
| `index`       | Rule argument from repository discovery  | Yes      | None                         | `RepoIndex.root`, clusters/environments, selected input records   | Supplies repository boundary, used source directories         |
| `connections` | Optional rule argument / shared resolver | No       | `compute_connections(index)` | `Connections.selected_paths`, `parameter_files`, `parameter_uses` | Supplies selected paths, authoritative ParameterSet spellings |

## Processing flow

1. Reuse or compute connections. Collect selected paths, preserving the selected ParameterSet spelling.
   An unused alias cannot replace that spelling.
2. Check each indexed cluster with discovered environments and each environment directory name.
   Retain environments with unreadable definitions. Add existing `Inventory/env_definition.yml` files to the file map.
3. Skip fixed layout directory names and `.git`. Visit selected files under `environments/` whose physical paths
   remain inside the repository. Exclude generated targets using the shared policy.
4. Accept `.yml`, `.yaml`, `.json`, and their `.j2` forms. Strip these suffixes with `paramset_stem`.
   Selected hidden files and fixed generator-input filenames have no filename exemption.
5. Require a full match of `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Emit one finding per failing name at `1:1`.
6. Sort findings by path, key, and line.

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

Unselected and shadowed files contribute no names.
Generated Namespace directories are excluded regardless of their bindings.
Unreadable environment definitions do not prevent checking directory or definition filenames.
Paths outside the permitted subtree, escaping the repository, under `.git`, or with unsupported suffixes are skipped.
Filename checks do not require readable file contents.

## Example

A discovered environment `environments/Cluster_01/Env_01` selects
`Inventory/parameters/Cloud_Deploy.yml` through a supported binding.
The rule reports `Cluster_01`, `Env_01`, `env_definition`, and `Cloud_Deploy` for review.
An existing generated `Namespaces/Foo` directory adds no finding.
An unselected `Cloud_Deploy.yml` and a cluster without discovered environments add no finding.

## Related documentation

- [Connected entities](connections.md)
- [Rule implementation](../../src/envgene_linter/rules/name3.py)
- [Rule tests](../../tests/test_name3.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Reporting](../../src/envgene_linter/report.py)
