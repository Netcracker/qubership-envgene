# INT-4: review unreferenced authored entities

- [Candidate scope](#candidate-scope)
- [Reference evidence](#reference-evidence)
- [Uncertainty and findings](#uncertainty-and-findings)
- [Implementation and tests](#implementation-and-tests)

Design: [INT-4 specification](/modules/envgene-linter/docs/superpowers/specs/2026-09-24-int4-design.md).

INT-4 reports recognized authored entities for which no reference was found in available local sources.
Every finding is Information / Review. The rule does not establish that removal is safe or delete anything.
It runs after INT-3 and is enabled by default.

## Candidate scope

The candidate catalog is separate from Connections. Unconnected candidates do not become inputs to other rules.
A ParameterSet, Shared Template Variable, or Resource Profile Override is checked as a file.
Credentials are checked as individual entries, excluding `sops` metadata.

At repository, cluster, and environment Inventory scopes, the rule scans these typed locations:

- `parameters`: nonrecursive ParameterSet discovery before staging removes shadowed files.
- `resource_profiles` and `rp_override`: recursive Resource Profile Override discovery.
- `shared-template-variables` and `shared_template_variables`: recursive Shared Template Variable discovery.
- `credentials`, `Credentials`, and `shared-credentials`: recursive Credential catalog discovery.

Authored Inventory `Profiles` files are also candidates. Selected legacy profile and Shared Template Variable
locations are included when bindings establish their type. Arbitrary YAML in `configuration` is not a candidate.
The root system catalog and selected passport/deployer companion catalogs supply additional Credential entries.

Generated environment Credential catalogs, generated Profiles, and Cloud/Namespace objects are not cleanup candidates.
Inventory-generation credentials have an implicit consumer and are excluded.
Empty, unreadable, and structurally invalid file candidates produce generic skip notes.
An empty Credential mapping contributes no entries. Jinja candidate contents are not evaluated.

File aliases retain their applicable environments but share one physical candidate.
Directory enumeration does not follow symlinks. Candidate reads reject paths outside the repository or inside `.git`.
These guards apply after the common index is built. Existing discovery failures before rule execution remain outside
INT-4's error-handling boundary.
Hard-linked Credential catalogs can produce a false review finding because reference matching still compares paths.

## Reference evidence

Raw environment bindings establish file references and identify dynamic bindings.
A literal reference protects same-name files in the consumer's applicable lookup scopes, including shadowed definitions.
INT-3 handles cross-scope naming conflicts. Equal names in unrelated environments do not establish use.

Credential filename bindings select catalogs but do not mark every entry used.
Literal `creds.get` calls, structured `credRef` objects, and supported bare ID fields establish entry references.
System consumers use the existing source-selection rules for deployer, registry, integration, artifact registry,
and Cloud Passport inputs. Secret payloads are never recursively interpreted as reference expressions.

The analysis also reads supported parameter bags in unconnected authored ParameterSets.
This is direct reference analysis, not transitive dead-code elimination.
Local Cloud/Namespace objects supply references even when no explicit ParameterSet binding selects a namespace.
Their top-level ParameterSet lists and profile selectors are examined separately from parameter bags.
A template profile baseline name alone does not select an instance override.

An explicit system or passport catalog determines the Credential lookup context.
For generated catalogs, matching IDs protect entries in applicable connected authored catalogs conservatively.
The analysis never compares secret values to infer their origin.
An unavailable authoritative system or generated catalog does not fall back to a different authored catalog.
Security-source records retain logical paths so resolved paths cannot bypass candidate path guards.
Malformed parameter bags contribute uncertainty and cannot establish positive reference evidence.
Repository and cluster Shared Template Variable directories outside supported generator lookup locations remain
reviewable unless applicable reference evidence exists.

## Uncertainty and findings

Candidates with positive reference evidence produce no finding, even if another consumer is unavailable.
Each remaining physical file or Credential entry produces one finding, with applicable uncertainty reasons aggregated.
File findings use line 1, column 1. Credential findings point to entry keys without copying IDs into finding text.

Message:

```text
No references to this {entity type} were found in the available sources.
```

Every hint explains that external template consumers and rendered references are not fully analyzed.
Additional reasons identify dynamic references, unreadable consumers, missing consuming environments,
uncertain generated-catalog provenance, or unsupported lookup locations.
No severity escalation asserts that an entity is definitely unused.

Findings and new skip notes omit Credential IDs, document values, expressions, and raw parser exceptions.
Navigable file paths remain visible. Disabling INT-4 bypasses its additional analysis.
Findings retain the CLI's exit code 0 behavior.

## Implementation and tests

- [Candidate discovery](/modules/envgene-linter/src/envgene_linter/usage_candidates.py)
- [Scoped reference analysis](/modules/envgene-linter/src/envgene_linter/usage_references.py)
- [Analysis records](/modules/envgene-linter/src/envgene_linter/usage_model.py)
- [Finding construction](/modules/envgene-linter/src/envgene_linter/rules/int4.py)
- [Rule tests](/modules/envgene-linter/tests/test_int4.py)
- [Candidate tests](/modules/envgene-linter/tests/test_usage_candidates.py)
- [Reference tests](/modules/envgene-linter/tests/test_usage_references.py)
- [Runnable examples](/modules/envgene-linter/testdata/rules/int4)
