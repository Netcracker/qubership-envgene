# PLACE-9: count and placement of used Cloud Passports

Status: implemented. The user approved the exact `passport-infra` role classification.
Russian version: [ru/2026-09-11-place9-design.md](ru/2026-09-11-place9-design.md).

## Purpose and scope

For each consuming cluster, allow at most one selected default passport and one selected infra passport. A consuming cluster is the cluster of the environment that uses the passport. A stem is the filename without `.yml` or `.yaml`: exactly `passport-infra` means infra; every other selected stem means default. This is role classification, not NAME-8/9 filename validation.

Check only passports reached through `inventory.cloudPassport` or existing automatic resolution. Missing references, missing passports or credentials, and unused files produce no findings. Do not inspect credential contents.

A physical file is the target after resolving symbolic links. Several aliases to that target count as one file. Exclude paths outside the repository and inside `.git`.

## Ambiguous passport lookup

An attempted lookup can establish a conflict even if it cannot select one passport. This is PLACE-9's explicit exception to the normal selected-file scope: the candidates of that used attempt participate in ambiguity checking, but not in content rules.

1. For an explicit reference, collect matching candidates from the existing Inventory, cluster and repository passport search roots.
2. For automatic resolution, try the cluster-name passport first, then `passport`. Stop at the first nonempty candidate group; do not combine fallback names.
3. Deduplicate physical paths. If the used attempt has multiple distinct candidates, emit one duplicate-resolution finding for that candidate set.
4. Combine environments that encounter the same candidate set into one finding. Include all candidate files at line 1, column 1 and all affected environment-definition binding positions. For automatic lookup use definition position `1:1`.

Use structured resolver candidates, not text parsed from skip notes. Preserve existing successful resolution behavior for other rules.

## Number of selected passports

Group successfully selected physical files by consuming cluster and role. Multiple environments using the same file do not increase the count.

Emit one Warning / Fix finding for each role with more than one distinct selected file, including those passports. Do not count ambiguous candidate groups again here.

Examples:

- One `passport.yml` and one explicitly selected `passport-infra.yml`: allowed.
- Two used files `business-a.yml` and `business-b.yml`: two default passports, so report one count finding.
- An unreferenced `backup.yml`: does not affect the count.

## Passport directory

PLACE-3 checks whether a selected passport is outside the cluster layer. PLACE-9 does not repeat that layer finding.

For a selected cluster-layer passport, require the owning cluster's canonical `cloud-passport/` directory. The plural `cloud-passports/` is incorrect. Nested directories within `cloud-passport/` are allowed.

## Used passport credentials

For each uniquely selected passport, follow the local generator's exact lookup order relative to the passport's parent directory:

1. `credentials/<passport-stem>.yml`
2. `<passport-stem>-creds.yml`

Only the first existing file is used. If it resolves outside the repository or inside `.git`, skip the companion check without promoting the second path. Do not infer `.yaml` companion lookup: the local loader checks these `.yml` paths only. Passport files themselves support both extensions.

The used credentials file must be beside its passport and under the proper cluster `cloud-passport/` directory. Consequently, a used `credentials/<stem>.yml` subdirectory input is reported even when an unused adjacent `<stem>-creds.yml` also exists.

Emit one finding per misplaced used physical credentials file, with that file's location and its associated passport. Missing files and unused lower-priority copies are silent. Never read credential content for this rule.

## Findings and reporting

Sort by path, key and line. All findings use Warning / Fix and preserve CLI exit code `0`. Catalog description: `One Cloud Passport per cluster`. No automatic changes, new CLI flags, networking or source-value output.

At introduction, PLACE-9 added the twelfth console header after PLACE-8 and before NAME-1. [PLACE-10](2026-09-11-place10-design.md) subsequently added a header between PLACE-9 and NAME-1; the current total is thirteen. The console always shows all catalog headers. HTML keeps only sections with findings, in the same rule order.

## Verification and documentation

Use synthetic fixtures covering:

- Automatic default selection; default plus explicitly selected infra; multiple used custom default names; unused extras and missing references.
- Explicit duplicates across levels, `.yml`/`.yaml` ambiguity, repeated conflicts across environments and automatic fallback priority.
- Physical aliases, external and `.git` paths, and malformed selected passports that still count.
- PLACE-3-only layer findings, a plural cluster passport directory and valid nested directories.
- Correct adjacent credentials, used subdirectory credentials even when an adjacent copy exists, and missing or unused credentials.
- Direct rule/engine parity, exact binding positions, console and HTML integration.

Describe the algorithm in English and Russian using the agreed seven-section processing-flow format. Preserve historical decisions with explicit supersession notes when later rules change shared scope or reporting.

## Related documents

- [Common connected-only scope](2026-09-11-connected-only-design.md)
- [Current algorithm](../../algorithms/place9.md)
- [Implementation](../../../src/envgene_linter/rules/place9.py)
- [Tests](../../../tests/test_place9.py)
