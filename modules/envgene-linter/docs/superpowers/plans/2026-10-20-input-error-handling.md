# Input error handling implementation plan

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Normalize source failures](#task-1-normalize-source-failures)
- [Task 2: Preserve incomplete checks and consumers](#task-2-preserve-incomplete-checks-and-consumers)
- [Verification](#verification)

> **For agentic workers:** Use `superpowers:executing-plans` to implement this approved change in order.

**Goal:** Keep expected source parser failures visible while checking independent files and writing both reports.

**Architecture:** Normalize library failures at parser calls. Collect safe read problems per analysis run,
associate them with actual consumers, and reuse structured skipped checks in reports.

**Tech stack:** Python 3.12, ruamel.yaml, Jinja2, the standard library, and pytest.

**Spec:** [Input error handling](/modules/envgene-linter/docs/superpowers/specs/2026-10-20-input-error-handling-design.md).

## Global constraints

- Work in `feature/envgene-linter-dev`, following the existing current-branch preference.
- No dependency additions, template execution, new rule IDs, report fields, or changed CLI exit codes.
- Use English documentation and synthetic fixtures. Do not inspect private corpora or `.playwright-mcp`.
- Preserve source selection, staged replacement, and unknown-consumer safety.
- No commit, push, issue comment, or release in this implementation task.

## Review focus

- A parser failure must not become an empty source or restore a shadowed input.
- Invalid environment definitions must not disappear from shared-source removal coverage.
- Context-local read diagnostics must not leak between runs or hide unexpected implementation errors.
- Template descriptor and compatibility fallback paths must expose incomplete analyses without losing independent findings.
- Disabled, unbound, and shadowed sources must respect each rule's existing scope.

## Task 1: Normalize source failures

**Files:** create `parsing.py`, `read_errors.py`, and `tests/test_input_errors.py`; modify `yamlio.py`,
`jinja_analysis.py`, `template_sources.py`, `ansible_sources.py`, `ansible_compat.py`, and template rules.

**Interfaces:** `ParseFailure` exposes safe `reason`, `line`, and `column`.
`parse_yaml(text)`, `compose_yaml(text)`, `parse_json(text)`, and `parse_jinja(environment, text)` normalize library failures.
`ReadProblem(path, reason, line, column)` contains no source values.
`collect_read_errors()` yields a per-context list. `YamlReadError` retains compatibility and safe position metadata.

- [x] Write real-parser failures for oversized YAML/JSON/Jinja literals, depth limits, malformed descriptors,
   and compatibility-only sources. Assert successful CLI completion, independent findings, and both reports.
- [x] Run `python -m pytest -q tests/test_input_errors.py tests/test_yamlio.py --tb=short`.
   Expected: the new oversized-input tests fail before implementation.
- [x] Normalize parser failures and bound decoded container depth. Preserve JSON values and position behavior.
- [x] Connect Jinja and descriptor/compatibility failures to existing located skips.
- [x] Rerun the focused command. Expected: parser failure cases pass.

## Task 2: Preserve incomplete checks and consumers

**Files:** create `diagnostics.py`; modify `discovery.py`, `model.py`, `engine.py`, `removal_analysis.py`,
`tests/test_input_errors.py`, reports documentation, readmes, specification catalog, and changelog.

**Interfaces:** `RepoIndex.read_problems` retains discovery failures.
`skip_check(index, rule, path, reason, line=1, column=1)` deduplicates safe located diagnostics.
Engine collection associates actual rule reads and selected discovery inputs with enabled rule IDs.

- [x] Add failing tests for YAML/JSON skips, disabled-rule filtering, unbound/shadowed inputs, secret redaction,
   fresh report replacement, and collector isolation. Use literal expected paths and independently derived outcomes.
- [x] Add a two-environment failure where an unreadable definition cannot justify shared-source removal.
- [x] Collect and associate read failures. Withhold uncertain PLACE-1 promotion and retain potential PLACE-2 consumers.
- [x] Run `python -m pytest -q tests/test_input_errors.py tests/test_skipped_reports.py tests/test_parameter_sources.py
   tests/test_place1.py tests/test_place2.py --tb=short`. Expected: all focused tests pass.
- [x] Update the English algorithm, design, report contract, coverage matrix, readmes, catalog, and functional changelog.

## Verification

- [x] Run the complete module suite and report all failures by name, including the three known macOS baseline failures.
- [x] Run Markdown, terminology, local-link, and whitespace checks on changed files.
- [x] Obtain one fresh read-only whole-change review and address material findings with failing regressions first.
- [x] Build wheel and sdist and verify the release allowlist without publishing artifacts.

Verification results on October 20, 2026:

- Added 41 synthetic input-error cases. The initial parser regressions failed before implementation.
- Final module suite: 1,631 passed and three unchanged macOS baseline failures.
- Markdown and terminology checks passed for all 17 changed Markdown files. All 326 local links resolve.
- Wheel and source archives passed the exact release allowlist. A wheel smoke check retained independent findings,
   replaced stale reports, and exported safe YAML/Jinja skips with the existing JSON schema.
- Fresh review identified malformed scalar constructor exceptions and discarded rewrite findings.
   Five regressions failed before the fixes and passed afterward. Both material findings are resolved.

The unchanged baseline failures are:

```text
tests/test_discovery.py::test_place8_entities_are_separate_from_name2_entities
tests/test_place8.py::test_discovers_empty_credentials_aliases_recursively[Credentials]
tests/test_place8.py::test_visible_binding_resolves_each_search_level_and_alias[environments/c/e/Inventory/Credentials/nested/slot.yml-credentials]
```
