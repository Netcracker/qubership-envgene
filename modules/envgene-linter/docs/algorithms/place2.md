# PLACE-2

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

PLACE-2 finds selected ParameterSet values that repeat a lower-layer value and checks whether the specific
source entry can be removed. It compares environment-authored values with repository/cluster inputs,
then cluster-authored values with repository inputs. There is no repository-versus-template comparison.

Equality preserves decoded YAML types: `true`, `1`, `1.0`, and `"1"` differ.
Quote style does not affect string equality. Lists and mappings inside lists compare recursively.
A matching lower-layer value alone does not establish that removal preserves the result.

## Input parameters

| Parameter   | Source                 | Format                            | Effect                                           |
|-------------|------------------------|-----------------------------------|--------------------------------------------------|
| `index`     | Repository discovery   | `RepoIndex`                       | Selected sources and known local consumers       |
| `full`      | Effective Set          | Environment -> scopes -> leaves   | Repository, cluster, and environment inputs      |
| `lower`     | Effective Set          | Environment -> scopes -> leaves   | Repository and cluster inputs                    |
| `site`      | Effective Set          | Environment -> scopes -> leaves   | Repository inputs                                |

## Processing flow

1. **Read projections and collect consumers.** Resolve actual inputs before filtering them into projections.
   A shadowed repository file remains absent. Record every environment, target, and category selecting each
   physical file, including uses where its value is neither a restatement nor the final winner.
   Skip candidate collection for an environment with a missing projection.

2. **Collect possible restatements.** Compare environment-authored `full` leaves with the same scope/path
   in `lower`, then cluster-authored `lower` leaves with `site`. An absent or definitely different value is silent.
   Confirmed or uncertain equality proceeds to removal analysis.

3. **Identify the exact source entry.** Use the resolved physical file path plus the complete YAML source path.
   The path includes `parameters` or `applications[i].parameters` and every nested key.
   Global/application entries and literal dotted/nested keys remain separate candidates.
   Multiple observations of the same physical entry share one result and one finding.

4. **Check the available merge context.** Every binding group selecting the candidate's physical file must
   have readable ordinary YAML sources for all its references. The supported shape is a mapping with mapping
   parameter bags and an optional application list. Application identities must be nonempty literal strings.
   Unresolved or dynamic references, selected parse errors, and relevant Jinja sources make the result uncertain.
   Anchors, aliases, YAML merge keys, custom tags, and unsupported values also prevent confirmation.

5. **Replay without the source entry.** For every known consuming environment, compute full parameter bags
   before and after omitting that exact source entry. Reuse the Effective Set selection, application scopes,
   reference order, file order, and `dict_merge` behavior. Omit the entry at every selection of its physical file.
   Preserve the file and parent mappings, including empty mappings. Do not remove a file, restore a shadowed
   source, or edit an indexed document. Compare all resulting scopes and complete bags with typed equality.

6. **Choose the outcome.** A definite change makes the override necessary and produces no PLACE-2 finding.
   Confirmed equality and preservation produce Warning / Fix. Otherwise produce Information / Review.
   Cache baseline bags per environment and removal results per source entry within this rule run.

## Result

| Condition                               | Severity      | Action   | Guidance                                      |
|-----------------------------------------|---------------|----------|-----------------------------------------------|
| Removal preserves all known uses        | Warning       | Fix      | Remove the repeated key or change its value   |
| Removal changes a known result          | None          | None     | No finding                                    |
| Equality or preservation is uncertain   | Information   | Review   | Review sources and merge context              |

The primary location is the candidate's source entry. The scope owner is the environment full name for
an environment entry or the source cluster for a cluster entry. Confirmed findings retain lower-value provenance
in `related`. Review messages contain no parameter values or parser exception details and give no deletion advice.
Findings preserve encounter order. No files are changed, and findings leave the CLI exit code at `0`.

Each Fix describes one independent removal against the current configuration.
The rule does not prove that deleting several findings together preserves the result.
The proof covers known local selected bindings. It does not discover remote consumers, evaluate Jinja,
or resolve a complete template dependency graph.

## Error handling

Unreadable and unrendered inputs remain separate discovery diagnostics. If their absence leaves a candidate's
merge context incomplete, the candidate receives Review. A source that supplies no usable candidate leaf cannot
produce a PLACE-2 finding by itself. No candidate yields an empty list (`No findings` in the console report).

Unsupported application shapes, unknown scalar equality such as YAML `.nan`, repeated container graphs,
and comparison limits prevent a Fix. Comparison and source validation each stop after 20,000 visited items.
Recursion, shape, or source-path errors during replay produce uncertainty rather than removal advice.

## Example

An environment binds `[shared, env-deploy]` under `envSpecificParamsets.cloud`:

```yaml
# environments/c/parameters/shared.yml
name: shared
parameters:
  LOG_LEVEL: "info"
  REPLICAS: 2
```

```yaml
# environments/c/e/Inventory/parameters/env-deploy.yml
name: env-deploy
parameters:
  LOG_LEVEL: "info"
  REPLICAS: 3
```

Removing the environment's `LOG_LEVEL` preserves the full bag, so it receives Fix.
`REPLICAS` differs from the lower value and remains silent.

If bindings instead apply `base`, `early`, and `late` with `REPLICAS` values `2`, `5`, and `2`,
the last entry is necessary. Removing it would expose `5`, even though it repeats the cluster value `2`.
PLACE-2 remains silent. A shared cluster entry is also necessary if any known consuming environment needs it.

For cluster-versus-repository comparisons, files with the same staged filename shadow each other.
Only sources that survive selection can supply a candidate or its lower value.

## Related documentation

- [Connections](/modules/envgene-linter/docs/algorithms/connections.md)
- [Effective Set](/modules/envgene-linter/docs/algorithms/effective-set.md)
- [Rule implementation](/modules/envgene-linter/src/envgene_linter/rules/place2.py)
- [Removal analysis](/modules/envgene-linter/src/envgene_linter/removal_analysis.py)
- [YAML value comparison](/modules/envgene-linter/src/envgene_linter/yaml_values.py)
- [Tests](/modules/envgene-linter/tests/test_place2.py)
