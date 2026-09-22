# PLACE-4

- [PLACE-4](#place-4)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-4 (SHOULD) reports Cloud Passport contract keys stored in connected ParameterSets.
The rule checks all selected layers and recommends moving the key to the appropriate
cloud-passport. It reads bindings and YAML without computing effective values or editing files.
Passport file placement belongs to PLACE-3.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Discovery → `check` | Yes | None | `RepoIndex` | Supplies environments, bindings, and discovered files |
| `connections` | Caller → `check` | No | `None`: `compute_connections(index)` | `Connections` | Selects physical files and records their uses |
| `TABLE` | `passport.py` | Yes | Built-in catalog | Set of exact contract-key strings | Defines which top-level parameter keys are prohibited |

## Processing flow

1. **Select connected ParameterSets**

   1. Use the supplied connections, or calculate them from `index`.
   2. Iterate `connections.parameter_files`, deduplicated by resolved physical path.
      Repository, cluster, and environment entries surviving shared resolution participate.
      Shadowed, unbound, unrelated same-stem files and Jinja templates are excluded.

2. **Read the parameters mapping**

   1. Use the selected file's loaded YAML document. In normal discovery, selected files
      already have a loaded document; files without one are skipped.
   2. Require a mapping root and a mapping at root `parameters`.
      `applications[].parameters` is not scanned.

3. **Match contract keys**

   1. Walk `leaves(parameters)`: recurse through mappings; lists and scalar values are leaves.
      Empty mappings contain no leaves.
   2. Convert each leaf's first path component to a string and match it exactly against `TABLE`.
      Do not add keys from actual passport files to the catalog.
   3. Keep each matching top key once per file, regardless of the number of nested leaves.

4. **Build findings**

   1. Resolve the top key's position with `LoadedYaml.position(("parameters", key))`.
   2. Create one Warning / Fix finding per file and key, then sort by
      `(path.as_posix(), key, line)`.

## Result

`check(index, connections=None)` returns a list of `Finding` records. Each has rule
`PLACE-4`, severity `warning`, issue type `Warning`, action `Fix`, and the contract
key as `key`. The sole location points to that key in the ParameterSet; `related`
is empty. Scope follows the file's layer: `repository`, `<cluster>`, or `<cluster>/<env>`.

Message: `{key} is a Cloud Passport contract key; do not store it in a ParameterSet.`

Hint: `Move {key} to the cluster cloud-passport, or to this environment's cloud-passport if the value is an override.`

The report catalog uses `Cloud Passport keys do not belong in ParameterSets`.
Console and HTML place this rule after PLACE-3 and before PLACE-6, including an
empty rule block. These warnings alone retain exit code 0. Files are unchanged.

## Error handling

**1a.** A reference without a selected physical ParameterSet contributes no file to scan.

**2a.** Missing or unreadable loaded YAML, a non-mapping root, or a non-mapping
`parameters` value produces no finding. The helper's fallback YAML read for a
manually supplied Jinja record catches `YamlReadError`; normal shared connections
exclude Jinja records before this step and never render them.

**4a.** If the exact source position is unavailable, `LoadedYaml.position` uses the
last available ancestor position, initially line 1, column 1.

## Example

Assume an environment binds `shared` and shared resolution selects
`environments/parameters/shared.yml`:

```yaml
parameters:
  CLOUD_API_HOST:
    internal: api.example.invalid
    external: public.example.invalid
  APP_MODE: demo
```

PLACE-4 returns one Warning / Fix finding for `CLOUD_API_HOST` at its top key,
with scope `repository`. The two nested values do not produce two findings.
An unbound copy of this file produces none; `CLOUD_API_HOST: {}` also has no leaf to report.

## Related documentation

- [Connected entities](connections.md)
- [Russian version](ru/place4.md)
- [PLACE-4: implementation](../../src/envgene_linter/rules/place4.py)
- [PLACE-4: tests](../../tests/test_place4.py)
- [`compute_connections`](../../src/envgene_linter/connections.py)
- [YAML positions and traversal](../../src/envgene_linter/yamlio.py)
