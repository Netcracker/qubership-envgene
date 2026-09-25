# NAME-8 specification and design

- [Requirement and agreed scope](#requirement-and-agreed-scope)
- [Naming contract](#naming-contract)
- [Implementation design](#implementation-design)
- [Reporting](#reporting)
- [Acceptance criteria](#acceptance-criteria)
- [Related documents](#related-documents)

## Requirement and agreed scope

Status: implemented. This document retrospectively records the bounded design approved in conversation on
September 25, 2026, and the resulting implementation. It does not introduce additional behavior.

[NAME-8 in the configuration standard](/docs/configuration-standard.md#name-8---name-the-cloud-passport-passport-should)
requires the default Cloud Passport filename stem `passport` and its companion Credential filename stem `passport-creds`.
The standard permits both `.yml` and `.yaml`.

Check only passports selected by supported local references or automatic association, together with their selected
companion files. Apply this naming check at every supported lookup scope. PLACE-9 owns directory placement.
Exclude the exact stem `passport-infra` and its companion because their naming belongs to NAME-9.
Do not infer an infra role from another filename ending in `-infra`.

Unselected passports and ambiguous unresolved lookups do not produce NAME-8 findings.
Missing companions do not constitute a filename violation. Jinja files are excluded.
The rule does not read Credential entries, validate passport contents, render templates, or rename files.

## Naming contract

Compare the logical filename stem with the required stem using exact, case-sensitive equality.
Both `passport.yml` and `passport.yaml` satisfy the passport requirement.
A selected passport named after its cluster still receives a finding even when automatic association succeeds.

Find the companion using the existing local source-selection convention, relative to the passport's parent directory:

1. `credentials/<passport-stem>.yml`.
2. `<passport-stem>-creds.yml`.

The first existing path or symlink occupies the slot. If that path is not a safe file, do not substitute the second slot.
A selected companion with any stem other than `passport-creds` receives a finding.
This includes the legacy location `credentials/passport.yml`.

The generator's companion lookup searches `.yml` only. Preserve that behavior even though the standard permits `.yaml`.
Do not invent a companion relationship for an adjacent `.yaml` file or an arbitrary Credential catalog.
Changing resolution belongs to a separate change.

## Implementation design

Implement the rule in `src/envgene_linter/rules/name8.py` using the existing rule interface:

```python
def check(index: RepoIndex, connections: Connections | None = None) -> list[Finding]:
    ...
```

Compute Connections only when the caller does not supply it.
Iterate `Connections.environment_passports` in deterministic environment order.
Use the selected record's logical path for naming, companion lookup, and navigation.

Resolve paths strictly before accepting them. Require logical and resolved paths inside the repository and outside `.git`.
Reject non-files, missing targets, and broken or cyclic aliases without reading their contents.
These guards apply after common discovery and do not change failures that occur before the rule runs.

Aggregate violations by resolved physical path, collecting consuming environments and failed naming requirements.
If passport and companion aliases refer to the same physical file, emit one finding containing both requirements.
This avoids duplicate findings across roles and repeated environment uses.

Register NAME-8 in the engine, metadata catalog, source configuration, and report ordering.
Enable it by default after NAME-4. Disabling it bypasses the check.
Preserve Connections, other rules' findings, and the CLI's nonfatal findings behavior.

## Reporting

Use Warning severity, Warning issue type, and Fix action.
Locate each finding at the retained logical path, line 1, column 1, with the generic key `filename`.
Aggregate environment names into the scope and sort findings by path and message.

Messages state the expected filename stem. Hints recommend renaming and updating dependent references while keeping
passport and companion names consistent. When both roles share one physical file, recommend separate files with the
required names. Do not include Credential IDs, values, or parser exceptions.

Console and HTML reports use the shared catalog and finding model. Findings retain exit code 0.

## Acceptance criteria

- Canonical `.yml` and `.yaml` passport names produce no finding.
- Explicitly selected noncanonical names and cluster-name auto-association produce Warning / Fix.
- The exact infra passport name and its companion produce no NAME-8 finding.
- Unused files and unresolved ambiguous passport references remain silent.
- Companion lookup honors the legacy-first priority and does not expand to `.yaml` or unrelated files.
- Invalid first companion slots do not cause fallback selection.
- Missing companions do not create findings.
- Multiple consuming environments and file aliases do not duplicate a physical-file finding.
- A passport and companion sharing one physical file produce one finding with both naming requirements.
- Unsafe paths and cyclic links encountered after indexing produce no NAME-8 finding.
- Credential IDs and values do not appear in NAME-8 findings.
- Disablement bypasses execution, and enabling the rule does not change other rules' findings.
- Console and HTML reports include NAME-8, and CLI findings retain exit code 0.

## Related documents

- [Current algorithm](/modules/envgene-linter/docs/algorithms/name8.md)
- [Implementation](/modules/envgene-linter/src/envgene_linter/rules/name8.py)
- [Tests](/modules/envgene-linter/tests/test_name8.py)
- [Runnable examples](/modules/envgene-linter/testdata/rules/name8)
- [Shared scope](/modules/envgene-linter/docs/algorithms/connections.md)
