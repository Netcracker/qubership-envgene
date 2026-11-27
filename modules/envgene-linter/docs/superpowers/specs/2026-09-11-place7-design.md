# envgene-linter: PLACE-7 (one category per ParameterSet)

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The original ability to report conflicts without existing files is historical. Under the connected-only contract, only references selecting files in the same environment contribute categories and locations. Original list indices are retained for positions. See the [current algorithm](../../algorithms/place7.md); report counts below describe this iteration.

Date: 2026-09-11

Status at design time: approved for implementation


## Contract and scope

PLACE-7 SHOULD: a ParameterSet is referenced from at most one of
`deployParameterSets`, `e2eParameterSets`, or
`technicalConfigurationParameterSets`. The referencing array assigns the
category. When the same values are needed in multiple categories, author
separate ParameterSets.

Source: `docs/configuration-standard.md`, PLACE-7, in the local
`qubership-envgene` checkout on `feature/modern-toolset`.

This implementation checks each environment's `env_definition.yml` independently,
using the corresponding instance bindings under `envTemplate`:

| Category   | Binding field                   |
|------------|---------------------------------|
| deploy     | `envSpecificParamsets`          |
| end-to-end | `envSpecificE2EParamsets`       |
| technical  | `envSpecificTechnicalParamsets` |

It reports a reference name present in at least two categories, across all
binding targets in that environment. Reuse within a single category is valid,
including repeated list entries and references under different targets.
Names are compared exactly as stored in `RepoIndex`, without case folding or
filename-suffix normalization. Categories are not aggregated across environments.

## Examples

Violation: `shared` is bound to deploy and technical in the same environment,
even though the targets differ.

```yaml
envTemplate:
  envSpecificParamsets:
    cloud: [shared]
  envSpecificTechnicalParamsets:
    bss: [shared]
```

Valid: separate names for separate categories.

```yaml
envTemplate:
  envSpecificParamsets:
    cloud: [shared-deploy]
  envSpecificTechnicalParamsets:
    bss: [shared-technical]
```

## Architecture and algorithm (original binding-only design)

Use `RepoIndex` as the source of bindings, as PLACE-6 does. Reparsing the YAML
for the binding semantics would duplicate discovery; reload it only for source
positions. No changes to discovery or Effective Set computation are required.

Create `rules/place7.py` with `check(index: RepoIndex) -> list[Finding]`.

For each environment:

1. Iterate categories in the order deploy, end-to-end, technical. For each category,
   read `env.bound_targets(category)` and visit all reference-list entries.
2. Group entries by reference name. Record distinct categories and each entry's
   YAML path: `("envTemplate", category.binding_field, target, list_index)`.
3. Keep groups with at least two distinct categories. An environment with no
   such groups produces no findings and needs no YAML reload.
4. Load `{env.path}/Inventory/env_definition.yml` once for positions. On
   `YamlReadError`, skip findings for that environment, following PLACE-6.
5. Emit one finding per environment and conflicting reference name. Include
   all its binding occurrences, including repeats within a category, in
   `locations`. Deduplicate identical locations and sort by line and column.
   Use the first location as the finding's primary position. Use the existing
   `LoadedYaml.position` behavior, including its fallback for unavailable positions.

Sort findings by `(path.as_posix(), key, line)`.

In this original design, the check uses bindings alone: it does not require the referenced ParameterSet
file to exist or parse successfully. File contents, Jinja rendering, file layers,
and reference resolution do not determine whether the binding categories overlap.
Missing or malformed binding structures retain the existing discovery behavior.

## Finding and reports

| Field | Value |
| --- | --- |
| `rule` | `PLACE-7` |
| `severity` | `Severity.WARNING` |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | environment definition; first binding occurrence |
| `locations` | all binding occurrences of the conflicting name |
| `key` | reference name |
| `scope` | `<cluster>/<env>` |
| `related` | empty |
| `message` | `ParameterSet {name!r} is bound to multiple categories: {categories}.` |
| `hint` | `Use a separate ParameterSet for each category, even when the parameter values are identical.` |

`{name!r}` means the reference name formatted with Python `repr`, including quotes. `categories` is the comma-and-space-separated list of involved category names in the
fixed order `deploy`, `e2e`, `technical`.

Catalog description: `One category per ParameterSet`.
The engine calls `check_place7(index)` after PLACE-6 and before NAME-1.
The console rule order becomes:
`PLACE-1`, `PLACE-2`, `PLACE-3`, `PLACE-4`, `PLACE-6`, `PLACE-7`,
`NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`.

Console output includes the empty `PLACE-7\nNo findings` block when applicable.
HTML uses the existing renderer with the heading
`PLACE-7: One category per ParameterSet`, all locations, and Warning / Fix chips.
Findings retain exit code 0. No autofix or new CLI options are introduced.
Other rules, including NAME-4, keep their existing behavior; findings from
different rules are not suppressed.

## Validation and documentation

Tests cover:

- Each pair of categories and all three categories; one finding per name and environment.
- Same and different binding targets across categories.
- Single-category reuse across targets and repeated list entries: no finding.
- Separate names per category, absent bindings, and empty lists: no finding.
- Multiple conflicting names and multiple environments; no cross-environment aggregation.
- Exact reference-name comparison and conflicts without ParameterSet files.
- All reference-item locations, their order, deduplication, primary position,
  exact message and hint, Warning / Fix metadata, and deterministic finding order.
- Failure to reload an environment definition: no crash or findings for that environment.
- Engine integration, console ordering and empty blocks, HTML locations and chips,
  and exit code 0 on findings.

Add `testdata/place7/ok` and `testdata/place7/not-ok` fixtures with integration
checks filtered to PLACE-7. Run focused tests during implementation and the full
pytest suite once integration is complete.

Write `docs/algorithms/place7.md` and its Russian copy. Update current algorithm
documentation that lists the report rule order or rule count to ten rules.
Historical design documents and plans retain their original scope.
