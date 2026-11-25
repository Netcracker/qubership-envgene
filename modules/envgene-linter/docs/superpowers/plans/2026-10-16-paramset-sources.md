# Shared ParameterSet sources implementation plan

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Discover and select shared sources](#task-1-discover-and-select-shared-sources)
- [Task 2: Decode JSON and verify consumers](#task-2-decode-json-and-verify-consumers)
- [Verification](#verification)

> **For agentic workers:** Use `superpowers:executing-plans` to implement the tasks in order.

**Goal:** Give reference checks, merging, and content rules the same nested YAML and JSON ParameterSets.

**Architecture:** A shared source module enumerates safe files and selects staged inputs from the repository index.
JSON decoding preserves JSON values while a syntax position map supports existing findings.

**Tech stack:** Python 3.12, the standard library, ruamel.yaml 0.18.17, and pytest.

**Spec:** [Shared ParameterSet sources](/modules/envgene-linter/docs/superpowers/specs/2026-10-16-paramset-sources-design.md).

## Global constraints

- Work on the current feature branch and preserve the pending PLACE-1 and PLACE-2 changes.
- Add no dependencies, CLI flags, report fields, rule defaults, template composition, or Jinja evaluation.
- Preserve connected-only scope, filename shadowing, and the three instance layers.
- Use English documentation and synthetic test data. Do not commit, push, publish, or post issue comments in this task.

## Review focus

- Distinct nested paths with the same filename must survive selection and merge deterministically.
- An invalid shadowed source must not poison the selected higher-layer source.
- External symlinks and unreadable scans must not establish missing-target or safe-removal claims.
- JSON duplicate keys and escaped strings must preserve the JSON decoder's values and source positions.
- Unbound nested and JSON files must not gain connected content findings.

## Task 1: Discover and select shared sources

**Files:** `paramset_sources.py`, `model.py`, `discovery.py`, `effective.py`, `connections.py`,
`rules/int2.py`, `removal_analysis.py`, and `tests/test_parameter_sources.py`.

**Interfaces:** `scan_directory(directory, root)` supplies logical paths, unavailable markers, and scan completeness.
`resolve_reference(index, env, reference, layers, include_unavailable=False)` returns selected entries.
Records carry relative parameter-directory paths. The index stores incomplete parameter scans.

- [x] Write tests for nested input content checks, relative-path shadowing, distinct directory fragments,
   JSON discovery, unbound inputs, and unsafe scans. Use literal expected paths and values.
- [x] Run the focused tests and observe the expected failures before production edits.
- [x] Add the shared source module and route discovery, Connections, merging, and INT-2 through it.
- [x] Make incomplete scans prevent PLACE-2 removal confirmation.
- [x] Rerun focused tests, including the existing Effective Set and PLACE-2 regression suites.

## Task 2: Decode JSON and verify consumers

**Files:** `yamlio.py`, `usage_references.py`, `usage_candidates.py`, `tests/test_yamlio.py`,
`tests/test_parameter_sources.py`, and the applicable algorithms, coverage matrix, readme, and changelog.

**Interfaces:** `load(path) -> LoadedYaml` preserves native JSON values and key positions.
Authored ParameterSet inventory and reference evidence reuse shared enumeration, including orphan Inventory folders.

- [x] Write failing tests for strict JSON syntax, duplicate-key values and positions, application locations,
   security and value checks, INT-4 evidence, and all three report outputs.
- [x] Implement JSON decoding and token-tree positions without changing YAML behavior.
- [x] Reuse common enumeration for authored ParameterSet evidence and verify unbound source scope.
- [x] Update English design, algorithms, readme, matrix, specification index, and functional changelog.

## Verification

- [x] Run `python -m pytest -q --tb=short` in `modules/envgene-linter` and report every failure.
   Three pre-existing macOS Credential alias failures are recorded in the baseline verification.
- [x] Run markdownlint with the repository config, textlint terminology, local-link checks, and `git diff --check`.
- [x] Obtain a fresh read-only code review against the saved working-tree baseline and resolve material findings.
- [x] Build and inspect the package, retaining development docs and test data outside distribution artifacts.
