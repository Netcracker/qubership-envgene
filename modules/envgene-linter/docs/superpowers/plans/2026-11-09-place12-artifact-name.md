# PLACE-12 artifact name grouping implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Compare PLACE-12 environments using an artifact name independently of its version.

**Architecture:** Preserve raw discovery identity and derive a separate grouping key inside PLACE-12.
Use that key in recommendations and retain original references in related evidence.

**Tech stack:** Python, pytest, Click, and the existing report and packaging code.

**Spec:** [Artifact name design](/modules/envgene-linter/docs/superpowers/specs/2026-11-09-place12-artifact-name-design.md).

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Group artifact versions](#task-1-group-artifact-versions)
- [Task 2: Verify reports and update documentation](#task-2-verify-reports-and-update-documentation)
- [Task 3: Verify and update the installed CLI](#task-3-verify-and-update-the-installed-cli)

## Global constraints

- Split at the first colon. Preserve literal artifact names and template names without case or whitespace normalization.
- Keep raw full references, existing eligibility guards, Information / Review, and the six JSON fields.
- Keep the current version number and runtime dependencies. Do not render, download, publish, commit, or push.
- Preserve the existing managed worktree and uncommitted branch changes.

## Review focus

- Empty artifact prefixes cannot form a comparison group.
- Dynamic version expressions remain excluded under the existing literal-field contract.
- A conflicting or incomplete consumer on another version cannot be ignored.
- Reports cannot attribute a mixed-version group to one arbitrary full artifact reference.
- Local template proposals and installed CLI behavior must use the same grouping as direct rule checks.

## Task 1: Group artifact versions

**Files:** `src/envgene_linter/rules/place12.py`, `tests/test_place12.py`.

**Interfaces:** Keep `EnvModel.template_identity` unchanged. `place12.check()` derives the group key locally.

- [ ] Add positive tests for differing versions, SNAPSHOTs, versionless artifacts, and first-colon splitting.
- [ ] Add negative tests for empty prefixes, other artifact names, other template names, and conflicting
      or incomplete consumers on another version. Verify full references remain in source evidence.
- [ ] Run `python3 -m pytest tests/test_place12.py -q -p no:cacheprovider`.
      Expected: new version-group and evidence assertions fail before implementation.
- [ ] Implement the group key and report identity without the version. Retain original references in related evidence.
- [ ] Repeat the command. Expected: all PLACE-12 tests pass.

## Task 2: Verify reports and update documentation

**Files:** PLACE-12 integration tests, normative standard, algorithm, specifications, readmes, matrix, and changelog.

**Interfaces:** HTML and JSON consume the same normalized artifact name. JSON retains six fields.

- [ ] Extend the real CLI integration fixture to compare two artifact versions and assert one grouped finding.
- [ ] Run `python3 -m pytest tests/test_place12.py tests/test_template_context.py -q -p no:cacheprovider`.
      Expected: the integration assertions pass with Task 1 and retain distinct source positions.
- [ ] Update English documentation to distinguish raw artifact references from the group key.
- [ ] Run the focused CLI, discovery, and report tests, followed by Markdown and terminology checks.
      Expected: all focused checks pass except any explicitly identified baseline filesystem test.

## Task 3: Verify and update the installed CLI

**Files:** Existing distribution scripts and local verification artifacts. No additional production interface.

- [ ] Run the full suite. Expected: no new failures beyond the three established macOS path-case failures.
- [ ] Run one fresh final code review and address Important findings with RED-to-GREEN regression tests.
- [ ] Transfer only verified changes to the main checkout, preserving HEAD, index, and concurrent user edits.
- [ ] Build and validate the wheel and source archive. Install the wheel without changing dependencies.
- [ ] Run the ordinary installed CLI on synthetic mixed-version input and the selected real repository.
      Expected: one synthetic cross-version finding and valid updated real HTML/JSON reports.
