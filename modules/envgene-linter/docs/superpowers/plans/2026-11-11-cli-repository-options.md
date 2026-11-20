# Explicit repository paths implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan in the current session.
> Steps use checkbox syntax for tracking.

**Goal:** Accept explicit instance and template repository paths and identify both roots in ParameterSet recommendations.

**Architecture:** Extend existing Click arguments and reuse the current template context.
Add repository labels when PLACE-12 constructs its findings so every renderer receives the same recommendation.

**Tech stack:** Python 3.12, Click 8.1.7, pytest, Ruff, Markdownlint, and Textlint.

**Spec:** [Explicit repository paths](/modules/envgene-linter/docs/superpowers/specs/2026-11-11-cli-repository-options-design.md).

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Repository options and recommendation paths](#task-1-repository-options-and-recommendation-paths)

## Global constraints

- No new dependencies or automatic migration.
- Preserve legacy positional commands, current-directory defaults, and `--template-repo`.
- Preserve source inspection limits and symbolic-link safeguards.
- Preserve JSON's six fields and omit `type`.
- Preserve all existing uncommitted work. Do not commit, push, or publish as part of this task.
- Keep documentation in English and customer-specific examples outside the repository.

## Review focus

- Relative paths, spaces, and Unicode must select the intended instance directory and keep outputs there.
- Simultaneous positional and explicit instance paths must fail before replacing existing reports.
- Template context without an instance option must still use the current directory.
- A `templates/` input must identify the correct parent root without bypassing linked-source inspection limits.
- Complete, partial, and unresolved PLACE-12 recommendations must carry consistent repository labels in every report.

## Task 1: Repository options and recommendation paths

**Files:**

- Modify: `modules/envgene-linter/src/envgene_linter/cli.py`.
- Modify: `modules/envgene-linter/src/envgene_linter/rules/place12.py`.
- Test: `modules/envgene-linter/tests/test_cli.py` and `tests/test_place12.py` within the module.
- Update: module readmes, changelog, report and PLACE-12 algorithms, and the specifications catalog.

**Interfaces:**

- Consume: `run_check(root, template_repo=...)` and `TemplateContext.directory` without changing their signatures.
- Produce: `check_cmd(repo: Path | None, instance_repo: Path | None, console: bool, template_repo: Path | None)`.
- Produce: existing `Finding.hint` with absolute repository labels when template context is supplied.

- [x] **Step 1: Add failing CLI tests.**

Cover short/long instance options, short template options with and without an instance option, relative paths,
spaces, Unicode, invalid paths, help, and conflicting positional inputs. Assert both reports and `.gitignore`
appear only in the checked directory. For conflicts, retain pre-existing report and ignore-file bytes.

- [x] **Step 2: Run the new tests before implementation.**

Run: `python3 -m pytest -q tests/test_cli.py` from `modules/envgene-linter`.
Expected: new option cases fail because the options do not exist.

- [x] **Step 3: Extend Click repository selection.**

Make the positional argument optional without a default. Add `-i` / `--instance-repo` and `-t` / `--template-repo`.
Reject conflicting explicit inputs with `click.UsageError`, then resolve the selected checked root or `.`.
Keep template paths unmodified so existing inspection safeguards remain active.

- [x] **Step 4: Verify CLI tests.**

Run: `python3 -m pytest -q tests/test_cli.py`.
Expected: all CLI tests pass.

- [x] **Step 5: Add and run failing recommendation tests.**

Use real whole-file and partial candidates. Assert repository roots in JSON recommendations and matching escaped HTML.
Include a `templates/` input and an unavailable descriptor. Assert direct engine output matches CLI output and
source bytes remain unchanged. Retain the existing linked-source tests as controls.
Run: `python3 -m pytest -q tests/test_place12.py`.
Expected: new root-label assertions fail before PLACE-12 changes.

- [x] **Step 6: Add repository labels to PLACE-12 findings.**

Prepend `Instance repository: <absolute root>` and `Template repository: <absolute root>` when context exists.
Use `context.directory.parent` for the template root. Preserve the underlying recommendation and field schema.

- [x] **Step 7: Update the user and algorithm documentation.**

Document the new invocation, long aliases, conflicts, output location, and template-context scope.
Record only functional changes in the changelog and add the design to the specifications catalog.

- [x] **Step 8: Run final verification.**

Run: `python3 -m pytest -q` from `modules/envgene-linter`.
Expected: no new failures compared with the baseline. Record known macOS failures by name.
Run Ruff, formatting checks, Markdownlint with the repository configuration, and terminology Textlint on changed files.
Expected: all applicable lint checks pass. Compare this task's diff against its before snapshots.
Build an offline local package, verify its distribution allowlist, and install the tested wheel into the local CLI.
Exercise the new invocation on temporary copies of the previously selected instance and template sources.

- [x] **Step 9: Review and leave changes ready for the user.**

Request one independent read-only review. Address important findings with failing regression tests and one fix pass.
Keep the task uncommitted and retain the ledger because it is not yet recorded in Git history.
