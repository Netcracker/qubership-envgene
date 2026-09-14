# PLACE-2

- [PLACE-2](#place-2)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-2 detects connected ParameterSet values that repeat an already supplied value instead of changing it. It compares environment-authored values with repository/cluster inputs, then cluster-authored values with repository inputs. There is no repository-versus-template comparison.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Repository discovery | Yes | None | `RepoIndex` | Supplies clusters and discovered environments |
| `full` | Effective Set | Yes | None | Environment → scopes → leaves | Repository + cluster + environment inputs |
| `lower` | Effective Set | Yes | None | Same shape | Repository + cluster inputs |
| `site` | Effective Set | Yes | None | Same shape | Repository inputs only |

## Processing flow

1. **Read the environment projections**

   1. Use actual selected inputs, resolved before projection filtering; never restore a shadowed file.
   2. For each discovered environment, obtain `full`, `lower`, and `site`. Skip the environment if any projection entry is missing.
   3. Start a shared deduplication set for the whole rule run.

2. **Check environment restatements**

   1. Iterate `full` scopes and leaves, keeping only leaves whose provenance layer is environment.
   2. Find the identical scope and leaf path in `lower`.
   3. If absent or unequal, skip it. If equal, it is a restatement; proceed to step 4.

3. **Check cluster restatements**

   Repeat step 2 using `lower` against `site`, keeping only cluster-authored leaves. Perform this comparison after step 2 for each environment.

4. **Deduplicate and build findings**

   1. Use `(source file path, dotted leaf key)` as the marker across both comparisons and all environments. Scope is not part of it.
   2. Skip a previously emitted marker. Otherwise remember it and create one finding on the restating leaf's YAML position.
   3. Use the environment full name as scope owner for environment leaves; for cluster leaves use the source file's cluster, falling back to `repository`.
   4. Record the lower value's provenance in `related`. Preserve encounter order when returning findings.

## Result

Each restatement produces Warning / Fix. The message identifies the key and restating layer. The hint asks to remove the key from this file or change its value if the override is intentional. Primary location is the restating source, not the source it repeats. No files are changed. No matches yields an empty list (`No findings` in CLI); findings preserve exit code `0`.

## Error handling

**1a.** Unresolved references, unrendered Jinja, and unreadable ParameterSets cannot supply usable leaves. Discovery/resolution notes remain separate from rule findings.

**1b.** Missing projection entries skip the environment.

**2a / 3a.** An absent lower value is a new contribution; a different value is a genuine override. Neither is an error or a PLACE-2 finding.

**4a.** Repeated observations of the same source/key are suppressed, including shared cluster files and multiple targets.

## Example

An environment binds `[shared, env-deploy]` under `envSpecificParamsets.cloud`:

```yaml
# environments/c/parameters/shared.yml
name: shared
parameters:
  LOG_LEVEL: info
  REPLICAS: 2
```

```yaml
# environments/c/e/Inventory/parameters/env-deploy.yml
name: env-deploy
parameters:
  LOG_LEVEL: info
  REPLICAS: 3
```

One finding points to the environment's `LOG_LEVEL`; `REPLICAS` is a real change and is silent.

For the cluster-versus-repository case, `environments/parameters/shared.yaml` and `environments/c/parameters/shared.yml` may both survive selection and repeat a value. Using the same staged filename at both levels would shadow the repository file, so it must not be used as an example of two participating inputs.

## Related documentation

- [Русская версия](ru/place2.md)
- [Connections](connections.md)
- [Effective Set](effective-set.md)
- [Implementation](../../src/envgene_linter/rules/place2.py)
- [Tests](../../tests/test_place2.py)
