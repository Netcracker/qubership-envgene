# PLACE-1

- [PLACE-1](#place-1)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-1 identifies equal parameter values authored independently by at least two participating environments or clusters and recommends moving them to the shared layer. Equal restatements of an existing lower-layer value are handled by PLACE-2 instead. The rule considers only resolved, connected ParameterSets; there is no template layer.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Repository discovery | Yes | None | `RepoIndex` | Supplies clusters and discovered environments |
| `full` | Effective Set | Yes | None | Environment → scopes → leaves | Repository + cluster + environment inputs |
| `lower` | Effective Set | Yes | None | Same shape | Repository + cluster inputs |
| `site` | Effective Set | Yes | None | Same shape | Repository inputs only |
| `catalogs` | Passport catalogs | No | `None` | Environment/cluster → top-level key set | Excludes passport contract keys; supplied by the engine |
| Minimum agreement | Rule constant | Fixed | `2` | Two or more participants | Minimum number of contributors per scope; not a CLI option |

## Processing flow

1. **Prepare connected Effective Set projections**

   1. The engine resolves actual ParameterSet inputs before filtering them into `full`, `lower`, and `site`. A projection never restores a shadowed file.
   2. Each leaf retains its authoring layer, source file, reference, and YAML position. A scope is target × category, optionally × application.

2. **Collect environment contributions within each cluster**

   1. Process environments in name order. Skip an environment if `full` or `lower` is missing.
   2. Keep only `full` leaves authored at the environment layer.
   3. Exclude a leaf when its top-level key belongs to the environment passport catalog, if catalogs were supplied.
   4. Compare the same scope and leaf path in `lower`. If the value exists and is equal, exclude this restatement. An absent or different value leaves a genuine contribution.

3. **Find values shared by participating environments**

   1. For each scope, participants are environments with at least one remaining contribution in that scope. Other environments neither support nor block agreement.
   2. Require at least two participants. Intersect their leaf paths: every participant must contribute the path.
   3. Require all values at that path to compare equal. Emit one finding recommending the cluster layer.

4. **Collect cluster contributions**

   1. Skip clusters without environments. For each remaining cluster, process environments in name order.
   2. Apply step 2 to `lower` versus `site`, keeping cluster-authored leaves and excluding cluster passport catalog keys.
   3. Keep the first contribution for each scope/path. If another environment in that cluster supplies a different cluster-authored value for the same scope/path, mark it conflicting.
   4. Remove every conflicting path after processing the cluster. Drop empty scope contributions.

5. **Find values shared by participating clusters**

   Apply step 3 to cluster contributions. At least two contributing clusters must contain the path and agree on its value. Emit one finding recommending the repository layer.

6. **Build findings and source locations**

   1. Use the first participant's source as the primary file, line, and column; use the dotted leaf path as the key.
   2. Include source positions of all owners, deduplicated by file/line/column, and provenance notes for each owner.
   3. Return environment-to-cluster findings first, then cluster-to-repository findings. Scopes and common paths are processed in sorted order.

## Result

Each qualifying shared value yields Warning / Fix. The scope is `<cluster> <scope>` or `repository <scope>`. Messages identify the key and number of agreeing environments/clusters; hints identify the shared destination and removal of lower copies. The rule changes no files. No matches returns an empty findings list; the CLI prints `No findings`. Findings do not change the CLI exit code from `0`.

## Error handling

**1a.** Unresolved references and unrendered Jinja do not supply Effective Set leaves; unreadable YAML is reported separately as a skipped input.

**2a / 4a.** Missing projection entries skip that environment for the corresponding comparison. Passport keys and restatements are normal exclusions, not errors.

**3a / 5a.** Too few participants, a missing common path, or unequal values yield no finding. No majority vote is used.

**4b.** Disagreement inside a cluster removes that path from its contribution; it does not fail the rule.

## Example

Two environments bind `env-deploy` under `envSpecificParamsets.cloud`. Each has its own `Inventory/parameters/env-deploy.yml`:

```yaml
name: env-deploy
parameters:
  LOG_LEVEL: info
```

There is no selected lower-layer value for `LOG_LEVEL`. Both environments contribute it, so PLACE-1 emits one finding recommending `environments/<cluster>/parameters/`.

If both environments also bind a cluster file that already supplies `LOG_LEVEL: info`, their copies are restatements: PLACE-1 is silent and PLACE-2 handles them. A third environment with no contribution in this scope does not block the first case. A third participant contributing another key but missing `LOG_LEVEL` does block it.

## Related documentation

- [Russian version](ru/place1.md)
- [Connections](connections.md)
- [Effective Set](effective-set.md)
- [Implementation](../../src/envgene_linter/rules/place1.py)
- [Tests](../../tests/test_place1.py)
