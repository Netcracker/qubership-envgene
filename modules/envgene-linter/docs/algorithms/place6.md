# PLACE-6

- [PLACE-6](#place-6)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-6 (MUST) reports connected pipeline ParameterSet bindings whose target is
not `cloud`, compared without case sensitivity. Pipeline files may be stored at
repository, cluster, or environment level. The rule checks the binding target,
without reading ParameterSet payloads or rewriting `env_definition.yml`.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Discovery → `check` | Yes | None | `RepoIndex` | Supplies environments, bindings, and discovered files |
| `connections` | Caller → `check` | No | `None`: `compute_connections(index)` | `Connections` | Selects physical files and records their uses |

## Processing flow

1. **Select connected pipeline targets**

   1. Use supplied connections or calculate them from `index`.
   2. From `connections.parameter_uses`, collect distinct `(environment, target)` pairs
      whose category is `Category.E2E`.

2. **Find non-Cloud bindings**

   1. For each discovered environment, iterate `env.bound_targets(Category.E2E)`
      from `envTemplate.envSpecificE2EParamsets`.
   2. Skip targets with `target.lower() == "cloud"`.
   3. Skip targets absent from the selected pairs. At least one reference under the
      target must resolve physically in this environment.

3. **Locate each target**

   1. On the first qualifying target, load
      `<env>/Inventory/env_definition.yml`; reuse that document for the environment.
   2. Read the position of `("envTemplate", "envSpecificE2EParamsets", target)`.

4. **Build findings**

   1. Emit one Warning / Fix finding per environment and target, even when several
      names under that target resolve to files.
   2. Sort by `(path.as_posix(), key, line)`.

## Result

The returned list contains `PLACE-6` findings with severity `warning`, issue type
`Warning`, action `Fix`, the target as written as `key`, and `<cluster>/<env>` as
`scope`. Each has one location at the target key in `env_definition.yml`; `related` is empty.

Message: `{target} is not the Cloud; pipeline ParameterSets must bind under envSpecificE2EParamsets.cloud.`

Hint: `Move the envSpecificE2EParamsets.{target} list to cloud.`

The catalog description is `Pipeline ParameterSets bind to the Cloud`. Console
and HTML show the rule after PLACE-4 and before PLACE-7, including an empty block.
These warnings alone retain exit code 0. Deploy and technical bindings are outside
this rule; ParameterSet category conflicts are checked by PLACE-7.

## Error handling

**2a.** Missing or empty bindings, empty target lists, and unresolved-only references
produce no finding. `Cloud` and `CLOUD` are valid targets.

**3a.** `YamlReadError` stops processing this environment; other environments continue.

**3b.** A missing exact source position falls back to the last available ancestor,
initially line 1, column 1.

## Example

Assume `pipeline-a` and `pipeline-b` resolve to connected ParameterSets:

```yaml
envTemplate:
  envSpecificE2EParamsets:
    bss: [pipeline-a, pipeline-b]
    Cloud: [pipeline-a]
```

PLACE-6 returns one Warning / Fix finding at `bss`, with key `bss`. The `Cloud`
target is accepted. Moving the `bss` list to `cloud` removes this finding.

## Related documentation

- [Connected entities](connections.md)
- [PLACE-6: implementation](../../src/envgene_linter/rules/place6.py)
- [PLACE-6: tests](../../tests/test_place6.py)
- [`compute_connections`](../../src/envgene_linter/connections.py)
- [YAML positions and traversal](../../src/envgene_linter/yamlio.py)
