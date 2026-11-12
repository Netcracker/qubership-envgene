# PLACE-12 template report implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Make PLACE-12 recommendations readable as grouped ParameterSet proposals
with optional local template evidence.

**Architecture:** Preserve candidate selection, then group compatible leaves before formatting one recommendation.
A separate static source inspector supplies descriptor locations, occupied names, and existing definitions.

**Tech stack:** Python, Click, ruamel.yaml, pytest, and the existing HTML and JSON renderers.

**Spec:** [Template report design](/modules/envgene-linter/docs/superpowers/specs/2026-11-06-place12-template-report-design.md).

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Group compatible candidates](#task-1-group-compatible-candidates)
- [Task 2: Inspect explicit local template context](#task-2-inspect-explicit-local-template-context)
- [Task 3: Integrate reports and verify the installed CLI](#task-3-integrate-reports-and-verify-the-installed-cli)
- [Task 4: Explain descriptor placement and reference order](#task-4-explain-descriptor-placement-and-reference-order)

## Global constraints

- Keep Information / Review and the six existing JSON fields. Do not restore `type`.
- Never edit source configurations, render templates, access the network, or publish customer data.
- Keep actual values in local recommendations and preserve YAML types.
- Keep all existing candidate guards and incomplete-input suppression.
- Leave changes uncommitted for user review. Preserve the managed worktree and ledger.

## Review focus

- Different source-reference combinations and applications must remain separate groups.
- Normalized names, existing stems, and multiple artifacts must not produce colliding proposals.
- Dynamic selectors, ambiguous descriptors, external parents, and partial Jinja sources must show uncertainty.
- Malformed or linked local context must not crash the check or read outside the selected template root.
- Grouped source positions and YAML values must remain complete and escaped in both reports.

## Task 1: Group compatible candidates

**Files:** `rules/place12.py`, `template_default_guidance.py`, and their tests.

**Interfaces:** `check(index, full, catalogs, template_repo=None)` returns grouped `Finding` objects.
The formatter consumes a list of `(path, value)` entries and an optional static template context.

- [ ] Add tests for two shared values in one group, differing references, scopes, and exact source positions.
- [ ] Run `python3 -m pytest tests/test_place12.py -q -p no:cacheprovider`.
      Expected: new grouping assertions fail before implementation.
- [ ] Group only already eligible leaves. Keep single-value keys compatible with existing consumers.
- [ ] Add formatter tests for nested paths, typed values, application end-to-end, and missing template context.
- [ ] Replace repeated recipes with one grouped YAML observation and a short uncertainty explanation.
- [ ] Run `python3 -m pytest tests/test_place12.py tests/test_template_default_guidance.py -q -p no:cacheprovider`.
      Expected: all tests pass.

## Task 2: Inspect explicit local template context

**Files:** Create `template_context.py` and `tests/test_template_context.py`.
Modify `cli.py`, `engine.py`, the formatter, and integration tests.

**Interfaces:** `run_check(root, *, template_repo=None)` passes explicit local source context to PLACE-12 only.
`TemplateContext` resolves descriptor entries and reserves readable names per check.

- [ ] Add tests for direct Cloud paths, Namespace postfixes, existing overrides, inherited entries,
      extension priority, Jinja prefixes, duplicate stems, malformed sources, traversal, and symbolic links.
- [ ] Run `python3 -m pytest tests/test_template_context.py -q -p no:cacheprovider`.
      Expected: the missing source inspector fails the tests.
- [ ] Implement bounded static source inspection and concise descriptor fragments.
- [ ] Test and implement `--template-repo`, including absent context and invalid paths.
- [ ] Run `python3 -m pytest tests/test_template_context.py tests/test_template_default_guidance.py
      tests/test_place12.py tests/test_cli.py tests/test_rule_config.py -q -p no:cacheprovider`.
      Expected: all tests pass.

## Task 3: Integrate reports and verify the installed CLI

**Files:** `html_report.py`, `report.py`, report tests, readme files, changelog, algorithm, and spec index.

**Interfaces:** JSON keeps all positions. HTML shows unique files followed by expandable exact positions.

- [ ] Test compact grouped source lists, HTML escaping, PLACE-12 ordering, and an empty PLACE-12-only run.
- [ ] Run the affected report tests. Expected: new assertions fail before implementation.
- [ ] Implement report integration and update English documentation with synthetic examples.
- [ ] Run focused tests, the full suite, Ruff, documentation linters, and distribution validation.
      Expected: no new failures. Record the three established macOS filesystem failures separately.
- [ ] Obtain one fresh final review and fix important findings with regression tests.
- [ ] Transfer verified changes to the working branch, build the wheel, and run its installed CLI locally.
      Expected: the selected example has three PLACE-12 groups covering the same 26 eligible values.

## Task 4: Explain descriptor placement and reference order

**Files:** `template_default_guidance.py`, its tests, PLACE-12 CLI integration tests, algorithm, design, and changelog.

**Interfaces:** The existing recommendation string supplies both HTML and JSON reports.
Keep `TemplateContext.propose` and the six JSON fields unchanged.

- [x] Test Cloud and Namespace instructions for all three parameter categories.
      Check the selected entry, exact list, retained references, and the new reference at the end.
- [x] Verify that the new placement assertions fail before changing the formatter.
- [x] Explain where to update the existing descriptor entry and append the new reference.
      Preserve other fields and entries. Explain the later priority of environment-specific ParameterSets.
- [x] Check that the CLI writes the same placement instructions to HTML and JSON.
- [x] Run focused tests, the full suite, and Python and documentation linters.
      Record the established macOS filesystem failures separately.
- [x] Generate a private report with the selected local template context and verify that source inputs stay unchanged.
