# `process_deployment_plan`

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

The `process_deployment_plan` step writes file
`environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`. On `OPERATION_TYPE: DEPLOY` the
step also writes `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`. On
`OPERATION_TYPE: CLEAN` the step reduces the full deploy plan and does not write a delta file.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `ENV_NAMES` | Pipeline | Yes | None | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/` |
| `PIPELINE_TYPE` | Pipeline | Yes | None | `GITLAB_DEPLOY` | Step runs only when value is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY` or `CLEAN` |
| `OPERATION_TYPE` | Pipeline | Yes | None | `DEPLOY`, `CLEAN` | Selects merge path (`DEPLOY`) or reduce path (`CLEAN`) |
| `APPLICATION_VERSIONS` | Pipeline | Conditional | None | SD or application-version list | Required on `DEPLOY`; supplies applications to calculate |
| `DEPLOY_POSTFIXES_FILTER` | Pipeline | No | empty | filter expression | Filters calculated deploy plan by deploy postfix |
| `NAMESPACE_NAMES_FILTER` | Pipeline | No | empty | filter expression | Filters calculated deploy plan by namespace name |
| `COMPONENT_NAMES_FILTER` | Pipeline | No | empty | filter expression | Filters calculated deploy plan by component name |
| `WAVE_NAMES_FILTER` | Pipeline | No | empty | filter expression | Filters calculated deploy plan by wave name |
| `BG_NS_TARGET` | Pipeline | Conditional | None | `origin`, `peer` | On `DEPLOY` with BG postfixes, selects origin or peer Namespace from `namespace-map.yml` |
| `NAMESPACE_NAMES` | Pipeline | Conditional | empty | comma-separated namespace names | On `CLEAN`, namespaces to remove; empty removes all entries |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`
   and pipeline parameter `OPERATION_TYPE` is `DEPLOY` or `CLEAN`. Otherwise the Instance pipeline
   skips this step.

2. **Select processing path**

   1. When pipeline parameter `OPERATION_TYPE` is `CLEAN`, the step runs the reduce path (blocks
      6-7).

   2. When pipeline parameter `OPERATION_TYPE` is `DEPLOY`, the step runs the merge path (blocks
      3-5).

3. **Read namespace map and validate DEPLOY inputs**

   1. The step reads file
      `environments/<cluster-name>/<env-name>/Inventory/namespace-map.yml`.

   2. When the file is missing, the step fails (3a).

   3. The step reads pipeline parameter `APPLICATION_VERSIONS`.

   4. When pipeline parameter `APPLICATION_VERSIONS` is absent or empty, the step fails (3b).

4. **Calculate deploy plan from application versions**

   1. The step resolves Solution Descriptor or application-version entries from pipeline parameter
      `APPLICATION_VERSIONS` against the repository root directory.

   2. The step writes ordered deploy-plan entries to temporary file
      `Inventory/deploy-plan-calculated.yml`.

5. **Map, filter, and merge deploy plan**

   1. The step reads each calculated entry and determines whether it is a bare `deployPostfix`
      entry (`name:version`) or a `namespace:name:version` entry.

   2. For a bare `deployPostfix` entry, the step looks up the `deployPostfix` key in
      `namespace-map.yml`. When the key is absent, the step fails (5a).

   3. When the map value is a scalar, the step uses that value as the Namespace name.

   4. When the map value is an object with `origin` and `peer` keys, the step reads pipeline
      parameter `BG_NS_TARGET` and selects the Namespace name from the matching key. When
      `BG_NS_TARGET` is `origin`, the step uses the `origin` value. When `BG_NS_TARGET` is
      `peer`, the step uses the `peer` value.

   5. When the map value is an object and pipeline parameter `BG_NS_TARGET` is absent or empty,
      the step fails (5b).

   6. For a `namespace:name:version` entry, the step takes the namespace name as given and
      searches `namespace-map.yml` for a map entry whose value matches: either the scalar value
      equals the namespace name, or the `origin` or `peer` value of a per-side object equals
      the namespace name. The step resolves the `deployPostfix` from the matching key,
      independent of `BG_NS_TARGET`.

   7. When no map entry names the given namespace, the step fails (5c).

   8. The step writes temporary file `Inventory/deploy-plan-mapped.yml`.

   9. The step applies filters from pipeline parameters `DEPLOY_POSTFIXES_FILTER`,
      `NAMESPACE_NAMES_FILTER`, `COMPONENT_NAMES_FILTER`, and `WAVE_NAMES_FILTER` to the mapped
      plan.

   10. The step treats the filtered mapped plan as the current run delta.

   11. The step reads the existing full deploy plan loaded at pipeline start from file
       `Inventory/deploy-plan.yml`.

   12. The step merges the run delta into the existing full deploy plan.

   13. The step writes file `Inventory/deploy-plan.yml` with the merged full plan.

   14. The step writes file `Inventory/delta-deploy-plan.yml` with the run delta only.

   15. The step deletes temporary files `Inventory/deploy-plan-calculated.yml` and
       `Inventory/deploy-plan-mapped.yml`.

6. **Read full deploy plan on CLEAN**

   1. The step reads the existing full deploy plan loaded at pipeline start from file
      `Inventory/deploy-plan.yml`.

7. **Reduce deploy plan on CLEAN**

   1. The step reads pipeline parameter `NAMESPACE_NAMES`.

   2. When pipeline parameter `NAMESPACE_NAMES` is empty, the step sets the full deploy plan to an
      empty entry list.

   3. When pipeline parameter `NAMESPACE_NAMES` lists one or more namespace names, the step removes
      deploy-plan entries whose field `namespace` matches any listed name.

   4. The step writes file `Inventory/deploy-plan.yml` with the reduced entry list.

   5. On the reduce path, the step does not write `Inventory/delta-deploy-plan.yml`.

## Result

1. On `OPERATION_TYPE: DEPLOY`, file
   `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml` contains the merged full
   deploy plan.

2. On `OPERATION_TYPE: DEPLOY`, file
   `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml` contains only the
   current run delta.

3. On `OPERATION_TYPE: CLEAN`, file
   `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml` contains the reduced full
   deploy plan.

4. Temporary files `Inventory/deploy-plan-calculated.yml` and `Inventory/deploy-plan-mapped.yml`
   exist only during a `DEPLOY` run.

## Error handling

**3a.** The step fails on `OPERATION_TYPE: DEPLOY` when file `Inventory/namespace-map.yml` is
missing. File `deploy-plan.yml` is not updated.

**3b.** The step fails on `OPERATION_TYPE: DEPLOY` when pipeline parameter `APPLICATION_VERSIONS`
is absent or empty. File `deploy-plan.yml` is not updated.

**5a.** The step fails on `OPERATION_TYPE: DEPLOY` when a bare `deployPostfix` entry is not
present in `namespace-map.yml`. The error names the `deployPostfix`. File `deploy-plan.yml` is
not updated.

**5b.** The step fails on `OPERATION_TYPE: DEPLOY` when `namespace-map.yml` value for a
`deployPostfix` is an object and pipeline parameter `BG_NS_TARGET` is absent or empty. The error
names `BG_NS_TARGET` and the `deployPostfix` and states that `BG_NS_TARGET` must be set to
`ORIGIN` or `PEER`. File `deploy-plan.yml` is not updated.

**5c.** The step fails on `OPERATION_TYPE: DEPLOY` when a `namespace:name:version` entry names a
namespace not found in any `namespace-map.yml` value. The error names the namespace. File
`deploy-plan.yml` is not updated.

## Example

- [`namespace-map.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/namespace-map.yml)
- [`deploy-plan.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/deploy-plan.yml)

## Warmup deploy-plan delta (`create_dp_for_warmup`)

The warmup deploy-plan delta runs inside step `warmup`, not inside step `process_deployment_plan`.

Triggers: `OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup` and `PIPELINE_TYPE: GITLAB_DEPLOY`.

1. The function reads the full deploy plan from file
   `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`.

2. The function filters the full plan to entries whose field `namespace` equals the active
   Namespace name.

3. When no entries match the active Namespace name, the function fails. The error names the
   active Namespace.

4. The function copies each matched entry and sets field `namespace` to the candidate Namespace
   name. Fields `deployPostfix`, `version`, `generationId`, and `wave` stay unchanged.

5. The function writes file `Inventory/delta-deploy-plan.yml` with the rebound entries.

6. The function removes entries whose field `namespace` equals the candidate Namespace name from
   the full plan (filter-exclude `!<candidate>`).

7. The function merges the rebound entries into the reduced full plan.

8. The function writes updated `Inventory/deploy-plan.yml`.

### Result

1. File `Inventory/deploy-plan.yml` replaces the candidate slice with rebound active entries.

2. File `Inventory/delta-deploy-plan.yml` lists rebound entries for the candidate Namespace.

## Merge algorithm

Two entries match when they share `<app-name>` (from `version`) and `namespace`.
`generationType: UniqForVersion` adds `version` to identity. `generationType: UniqForRun` adds
`generationId`.

A delta entry with no counterpart in the full plan is added. A delta entry matching an existing
one collapses into one entry with the higher `wave`. The merge only adds entries and raises
`wave`. It never removes. An entry present in the full plan but absent from the delta is
retained.

## Related documentation

- [`deploy_postfix_namespace_map`](/docs/technical-design/instance-pipeline/deploy-postfix-namespace-map.md)
- [`warmup`](/docs/technical-design/instance-pipeline/warmup.md)
- [`generate_effective_set`](/docs/technical-design/instance-pipeline/generate-effective-set.md)
