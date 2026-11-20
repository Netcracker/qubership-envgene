# PLACE-7

- [PLACE-7](#place-7)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-7 (SHOULD) requires one category per connected ParameterSet reference in
an environment. It checks instance bindings in `env_definition.yml`; the category
comes from the binding field. Reusing a reference within one category is allowed,
including under different targets. Categories from different environments are
never combined. ParameterSet contents and template-repository arrays are not inspected.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Discovery → `check` | Yes | None | `RepoIndex` | Supplies environments, bindings, and discovered files |
| `connections` | Caller → `check` | No | `None`: `compute_connections(index)` | `Connections` | Selects physical files and records their uses |

## Processing flow

1. **Select connected references**

   1. Use supplied connections or calculate them from `index`.
   2. Collect distinct `(environment, category, target, reference)` tuples from
      `connections.parameter_uses`. A name must resolve to a physical file in that environment.

2. **Group original binding occurrences**

   1. For each environment, visit categories in order: `deploy`
      (`envSpecificParamsets`), `e2e` (`envSpecificE2EParamsets`), `technical`
      (`envSpecificTechnicalParamsets`), all beneath `envTemplate`.
   2. Visit every target and enumerate its original reference list. Skip occurrences
      absent from the selected tuples, without renumbering subsequent indices.
   3. For each selected name, store its distinct categories and every path
      `("envTemplate", category.binding_field, target, original_list_index)`.
      Compare names exactly as stored in `RepoIndex`, preserving case and suffixes.
   4. Retain names in at least two categories. If none conflict, proceed to the next
      environment without reloading its definition.

3. **Locate conflicting references**

   1. Load `<env>/Inventory/env_definition.yml` once for the environment.
   2. For each conflicting name, resolve every recorded path with `LoadedYaml.position`.
   3. Deduplicate equal `(line, column)` positions and sort them. Preserve repeated
      references within one category as locations when their positions differ.
      YAML aliases that map to the same position do not duplicate it.
   4. Use the first location as primary and keep all locations in the finding.

4. **Build findings**

   1. Emit one Warning / Fix finding per environment and conflicting reference name.
   2. Join participating category names with `", "` in order `deploy`, `e2e`, `technical`.
   3. Sort findings by `(path.as_posix(), key, line)`.

## Result

Each returned finding has rule `PLACE-7`, severity `warning`, issue type `Warning`,
action `Fix`, the exact reference name as `key`, `<cluster>/<env>` as `scope`, and
empty `related`. The path is the environment definition; `locations` contains
all distinct source positions and its first entry supplies the primary line and column.

Message: `ParameterSet {name!r} is bound to multiple categories: {categories}.`

Hint: `Use a separate ParameterSet for each category, even when the parameter values are identical.`

Console and HTML use catalog description `One category per ParameterSet`, after
PLACE-6 and before PLACE-8. The empty block is `PLACE-7
No findings`; HTML displays
all locations with Warning / Fix chips. These warnings alone retain exit code 0.
Other rules may report the same reference independently. Configuration is unchanged.

## Error handling

**2a.** Unresolved references are excluded; original list indices remain unchanged.
Multiple physical resolution entries do not create extra categories or findings.

**3a.** `YamlReadError` suppresses this environment's PLACE-7 findings; processing
continues with the next environment.

**3b.** If an occurrence has no exact position, `LoadedYaml.position` retains the
last available ancestor position, initially line 1, column 1.

## Example

Assume `shared` resolves and `missing` does not:

```yaml
envTemplate:
  envSpecificParamsets:
    cloud: [missing, shared, shared]
  envSpecificTechnicalParamsets:
    bss: [shared]
```

The result is one Warning / Fix finding with message
`ParameterSet 'shared' is bound to multiple categories: deploy, technical.`
Its locations point to the original deploy list indices 1 and 2 and technical
index 0. The missing reference does not shift them.

Using separate names `shared-deploy` and `shared-technical` removes the conflict,
even when their parameter values are identical.

Runnable synthetic fixtures: [conflict](../../testdata/place7/not-ok/environments/lab-cluster/e01/Inventory/env_definition.yml)
and [valid bindings](../../testdata/place7/ok/environments/lab-cluster/e01/Inventory/env_definition.yml).

## Related documentation

- [Connected entities](connections.md)
- [PLACE-7: implementation](../../src/envgene_linter/rules/place7.py)
- [PLACE-7: tests](../../tests/test_place7.py)
- [`compute_connections`](../../src/envgene_linter/connections.py)
- [YAML positions and traversal](../../src/envgene_linter/yamlio.py)
