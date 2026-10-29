# Authored configuration scope implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan. Track steps with checkboxes.

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Implementation](#implementation)

**Goal:** Exclude generated output from default findings while retaining reference context for authored inputs.

**Architecture:** Share one environment-relative path policy across source readers, diagnostics, and the engine.
Keep filesystem safety independent from eligibility for findings. Generated Credential catalogs remain context.

**Tech stack:** Python 3.12, pytest, Click, Jinja2, and ruamel.yaml with existing dependency versions.

**Spec:** [Authored configuration scope](/modules/envgene-linter/docs/superpowers/specs/2026-10-28-source-scope-design.md).

## Global constraints

- No additional rule, command option, dependency, report field, or automatic configuration edit is introduced.
- Unknown paths retain their existing eligibility.
- Existing repository-confinement and symlink rules remain in force.
- Commit, push, issue comments, release, and Docker execution are outside this task.

## Review focus

- Generated names at source levels remain checked, including Template Repository `Namespaces/`.
- Generated catalogs resolve authored references without receiving secret-protection findings themselves.
- Broken generated context cannot produce parser leaks or false missing-reference fixes.
- Physical aliases cannot turn generated output into an authored finding target.
- Every rule and all three report formats observe the same boundary, including disabled-by-default naming checks.

## Implementation

### Task: Apply and document the shared boundary

Files include `source_scope.py`, source readers, security consumers, diagnostics, the engine,
`tests/test_source_scope.py`, affected rule tests, and the source-scope algorithm.

The shared interface is `is_generated_output(index: RepoIndex, path: Path) -> bool`.
Filesystem safety stays in `safe_parameter_path`. Context reads remain available separately from finding eligibility.

- [x] Add regression tests for generated trees, fixed output files, and pipeline files inside Inventory.
   Assert source results are identical before and after adding outputs with otherwise reportable content.
- [x] Add controls for authored directories with generated-looking names, generated headers in authored files,
   physical aliases, and unknown paths. Assert TPL-1 continues to identify authored Jinja.
- [x] Add valid and malformed generated-catalog context tests and a real CLI test for both reports and console output.
- [x] Run `python3 -m pytest tests/test_source_scope.py -q`. Confirm failures expose generated-file findings.
- [x] Implement the shared classifier, prune generated traversal, and restrict direct security and integrity checks.
   Retain generated data only where it provides reference or usage evidence.
- [x] Enforce the path policy in structured diagnostics and final engine findings.
- [x] Update obsolete generated-target expectations while preserving the original checks on authored fixtures.
- [x] Run the focused tests and full module suite. Report the three baseline macOS failures separately.
- [x] Update the algorithm, affected rule documentation, readmes, applicability matrix, and specification catalog.
- [x] Run Python linting, Markdown linting, terminology checks, link checks, and whitespace checks on changed files.
- [x] Request one independent review of the complete diff and address material findings with regression tests.

The changes remain uncommitted for user review.


Verification records: 40 source-scope regressions pass, including all three material independent-review findings.
The full module suite reports 1,712 passed and the three baseline macOS Credential casing failures.
Markdown linting, terminology, local links, archive allowlists, and strict package metadata checks pass.
Ruff reports no new findings. Four unused-code warnings in changed files also occur at the base revision.
