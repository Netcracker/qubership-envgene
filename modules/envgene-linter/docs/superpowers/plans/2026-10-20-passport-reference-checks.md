# Cloud Passport check implementation plan

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Check selected passport paths](#task-1-check-selected-passport-paths)
- [Task 2: Check explicit passport references](#task-2-check-explicit-passport-references)
- [Verification](#verification)
- [Verification results](#verification-results)

> **For agentic workers:** Use `superpowers:executing-plans` to implement the approved tasks in order.

**Goal:** Remove false PLACE-3 alias findings and expose unresolved explicit Cloud Passport references in INT-2.

**Architecture:** PLACE-3 consumes selected per-environment passport records rather than every indexed physical alias.
INT-2 reuses its safe directory lookup for explicit passport bindings, independently of legacy passport candidate selection.

**Tech stack:** Python 3.12, pathlib, the existing YAML loader, and pytest. No dependencies are added.

**Specs:** [PLACE-3](/modules/envgene-linter/docs/superpowers/specs/2026-09-04-place3-design.md) and
[INT-2](/modules/envgene-linter/docs/superpowers/specs/2026-09-18-int2-design.md).
The user approved both changes in conversation on October 20, 2026.

## Global constraints

- Work in the current feature branch. Preserve the previous uncommitted input-error work.
- Keep optional absent passports silent. Do not search another cluster or external templates.
- Keep existing report fields, rule IDs, and CLI exit codes. Use generic INT-2 messages without reference values.
- Use synthetic committed fixtures. Corpus analysis is read-only and stores results outside the repository.
- Do not alter the shared legacy passport resolver or other rules' connection scope in this bounded change.
- No commit, push, issue comment, release, or installation into the user's CLI environment is requested.

## Review focus

- An unselected alias must not gain a PLACE-3 finding just because its physical target was selected elsewhere.
- Two selected logical paths to one physical file can have different placement outcomes.
- An unavailable higher-priority lookup must block a definite missing claim or successful lower fallback.
- Explicit passport checks must run even when `envTemplate` is absent and must not infer template-supplied passports.
- Lookup uncertainty, target parser failures, and multiple candidates must retain Review and source redaction.

## Task 1: Check selected passport paths

**Files:** modify `rules/place3.py`, `tests/test_place3.py`, the PLACE-3 specification and algorithm, and changelog.

**Interfaces:** consume `Connections.environment_passports: dict[str, PassportFile]`.
Deduplicate findings by selected logical path. Preserve `check()` and its existing finding fields and hints.

- [x] Add synthetic cases for an unused root alias, an unused environment alias, repeated selected uses,
   a selected root alias to a cluster file, and two selected misplaced aliases to one file.
- [x] Run `python -m pytest -q tests/test_place3.py --tb=short`.
   Expected: the unused-alias cases fail before implementation.
- [x] Build PLACE-3 candidates from selected records and retain logical placement identity.
- [x] Update the current English specification and algorithm. Keep historical decisions marked as historical.
- [x] Run the focused command again. Expected: all PLACE-3 cases pass.

## Task 2: Check explicit passport references

**Files:** modify `rules/int2.py`; create `tests/test_int2_passports.py`; update the INT-2 specification,
algorithm, rule matrix, readmes, and functional changelog.

**Interfaces:** `_Checker.passport(env, reference) -> str | None` returns `missing`, `unknown`, or resolved `None`.
Reuse `named_paths(env, reference, PASSPORT_FOLDERS)` and the rule's safe reader.
Check truthy `inventory.cloudPassport` before `bindings()` examines `envTemplate`.

- [x] Add cases for exact missing location, absent/empty/null references, readable local targets at all search
   levels, another cluster, dynamic references, malformed or unsafe targets, incomplete enumeration,
   higher-priority matches, multiple candidates, and `.j2` uncertainty.
- [x] Add engine/JSON integration, disabled-rule filtering, and generic-message redaction assertions.
- [x] Run `python -m pytest -q tests/test_int2_passports.py --tb=short`.
   Expected: explicit missing and unknown reference cases fail before implementation.
- [x] Add the reference check using the generator's level and folder priority. A complete missing lookup is Fix.
   Unsupported context or several distinct candidates in one directory is Review. Do not claim the generator rejects
   duplicates: its current explicit lookup returns the first file.
- [x] Run `python -m pytest -q tests/test_int2_passports.py tests/test_int2.py tests/test_place3.py --tb=short`.
   Expected: all focused cases pass.
- [x] Update the current English rule contract, algorithms, user-facing scope, and changelog.

## Verification

- [x] Run the complete module suite. Report the three known macOS casing failures separately by name.
- [x] Run Markdown, terminology, local-link, and whitespace checks for changed documentation.
- [x] Obtain one fresh read-only review of this task's delta against its saved worktree baseline.
   Address material findings with failing regressions before fixes.
- [x] Repeat PLACE-3 and INT-2 on all corpus roots without writing reports or ignore entries into them.
- [x] Build wheel and source archives and verify the release allowlist without publishing.

## Verification results

Verified on October 20, 2026:

- The focused suite passed 94 tests. The complete suite passed 1,673 tests and retained three baseline failures.
  The baseline before this task passed 1,631 tests with the same failures, so 42 additional cases now pass.
- The final reviewer found one material issue: a readable file in place of a passport directory could incorrectly
  establish resolution. Four regressions failed before the fix and passed afterward, including internal symlinks
  and lower-priority fallback candidates. The unavailable directory now receives Review.
- Both rules ran on all 25 instance roots without exceptions. PLACE-3 produced no findings. The new passport check
  produced three Fix findings and one Review for an unreadable target. The other 50 roots are template-only and
  outside these two checks. A targeted repeat after the review fix retained the same results.
- Wheel and source archives passed the exact release allowlist. A CLI smoke check imported the built wheel,
  suppressed an unused alias, reported missing and unavailable passports, and generated HTML and JSON reports.
  No corpus data entered the source tree or distribution.

The three unchanged macOS failures are:

- `tests/test_discovery.py::test_place8_entities_are_separate_from_name2_entities`
- `tests/test_place8.py::test_discovers_empty_credentials_aliases_recursively[Credentials]`
- `tests/test_place8.py::test_visible_binding_resolves_each_search_level_and_alias[environments/c/e/Inventory/Credentials/nested/slot.yml-credentials]`

These concern case-sensitive directory aliases on a case-insensitive filesystem. This task does not fix or hide them.
The review also identified a similar pre-existing directory-sentinel risk in other INT-2 consumers. That requires
separate Credential and Resource Profile regressions and remains outside this passport-only change.
