# INT-3

- [Description](#description)
- [Inputs](#inputs)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Boundaries](#boundaries)
- [Examples](#examples)
- [Related documentation](#related-documentation)

## Description

INT-3 reports a used reference name defined at multiple scopes with **Warning / Fix**.
It implements the naming requirement in
[the configuration standard](/docs/configuration-standard.md#int-3---no-shadowed-same-name-overrides-should).
Scopes are environment Inventory, the environment's cluster, and repository `environments`.

ParameterSets can merge across scopes during generation. INT-3 still reports their duplicate reference names
without claiming that all lower-scope files are ignored. See
[Effective Set computation](/modules/envgene-linter/docs/algorithms/effective-set.md) for merging and staging.

## Inputs

Each discovered environment supplies these bindings from `envTemplate`:

| Entity                    | Binding                                                                                  |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| ParameterSet              | `envSpecificParamsets`, `envSpecificE2EParamsets`, and `envSpecificTechnicalParamsets`   |
| Shared Credential file    | `sharedMasterCredentialFiles`                                                            |
| Resource Profile Override | `envSpecificResourceProfiles`                                                            |
| Shared Template Variables | `sharedTemplateVariables`                                                                |

A reference must be a nonempty literal filename stem with a connected local target in that environment.
INT-3 excludes expressions, path references, and Jinja files. It supports `.yml` and `.yaml`.
An internal `name` field or a Credential ID does not define a filename reference.

## Processing flow

1. Collect used names separately for each environment and entity type. Repeated bindings share one check.
2. Collect matching ParameterSets from the index before staging removes repository files hidden by cluster files.
   ParameterSet discovery remains nonrecursive.
3. Collect profile and shared Credential candidates from indexed records and their logical aliases.
   Search environment, cluster, and repository scopes. Retain the first matching directory at each scope.
   Profile directories are `resource_profiles`, `rp_override`, `Profiles`, and `parameters` in that order.
   Credential directories are `credentials`, `Credentials`, and `shared-credentials` in that order.
4. Enumerate Shared Template Variables recursively under `configuration` and `configurations` at each scope,
   followed by the environment Inventory fallback. Reuse the existing resolver to identify the selected alias.
   Its lookup order remains authoritative even when sorted enumeration produces a different order of candidates.
5. Reject paths outside the repository, paths within `.git`, directory symlinks, and unavailable file targets.
   Deduplicate physical paths, preferring the selected logical alias when aliases cross scopes.
6. Report when the remaining physical definitions occupy at least two scopes.
   Include the participating files in environment, cluster, and repository order, then by path within each scope.
7. Sort findings by environment, entity type, and participating paths.

INT-3 inspects additional definitions hidden by a used reference's lookup.
Those candidates remain outside other rules' connected input sets.

## Result

Each environment, entity type, and reference name produces at most one finding.
Findings include all participating file locations at `1:1`, because the conflict concerns filenames.
Messages identify the environment and entity type. They omit reference expressions, Credential IDs, and document values.
File paths remain visible.

The suggested action is to use distinct names and update bindings, or retain the definition at one scope.
ParameterSet findings also explain that generation can merge fragments despite the naming violation.

The rule runs after INT-2 and before NAME-1. Disable it through `RULE_ENABLED["INT-3"]` before building.
The CLI retains exit code `0` for findings and does not modify configuration files to fix them.

## Boundaries

- Files used only by another environment or cluster cannot establish this environment's conflict.
- Multiple candidates at only one scope do not trigger INT-3. INT-2 owns applicable ambiguous-target checks.
- Empty and malformed YAML can still occupy filenames. INT-3 does not parse candidate contents to compare names.
- Missing targets and dynamic references alone do not produce INT-3 findings.
- Repeated Credential IDs in differently named files are not filename conflicts.
- Generated Cloud/Namespace references alone, generated Credential catalogs, passport companions,
   and fixed inventory-generation credentials do not establish INT-3 bindings.
- Shared Template Variable lookup follows the generator's legacy directories and Inventory fallback.
   Repository and cluster `shared-template-variables` directories alone do not establish candidates.
- Failed INT-3 directory enumeration produces a generic skip note, without exception contents.
   Existing discovery runs before INT-3 and retains its own error behavior, including failures on some cyclic symlinks.

## Examples

A bound `service-deploy` has files at these two locations:

```text
environments/demo-cluster/parameters/service-deploy.yml
environments/demo-cluster/demo-env/Inventory/parameters/service-deploy.yml
```

INT-3 reports both files even if their parameters are disjoint and generation merges them.
Removing the unused duplicate or giving the files distinct reference names removes that naming conflict.
Review the bindings and intended values before changing the configuration.

The runnable [positive example](/modules/envgene-linter/testdata/rules/int3/ok) defines each reference at one scope.
The [negative example](/modules/envgene-linter/testdata/rules/int3/not-ok) duplicates all four entity types
across environment and cluster scopes. Expectations apply to INT-3. Other rules can report independent findings.

## Related documentation

- [Specification and design](/modules/envgene-linter/docs/superpowers/specs/2026-09-24-int3-design.md)
- [Implementation plan](/modules/envgene-linter/docs/superpowers/plans/2026-09-24-int3.md)
- [Connected entities](/modules/envgene-linter/docs/algorithms/connections.md)
- [Implementation](/modules/envgene-linter/src/envgene_linter/rules/int3.py)
- [Tests](/modules/envgene-linter/tests/test_int3.py)
