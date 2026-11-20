# PLACE-12 guidance modes implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` in the current session.

**Goal:** Give general PLACE-12 advice without `-t` and retain concrete recipes with explicit template context.

**Architecture:** Return generic advice before YAML reconstruction when `context is None`.
Keep the current template-context branches and report schema.

**Tech stack:** Python 3.12, Click, pytest, Ruff, Markdownlint, and Textlint.

**Spec:** [Guidance modes](/modules/envgene-linter/docs/superpowers/specs/2026-11-12-place12-guidance-modes-design.md).

> [!NOTE]
> Historical plan for the earlier generic-only interpretation.
> The [portable guidance plan](/modules/envgene-linter/docs/superpowers/plans/2026-11-12-place12-portable-guidance.md)
> replaces its no-context output requirements after the user's clarification.

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: General advice without template context](#task-1-general-advice-without-template-context)

## Global constraints

- Preserve all existing work, candidate detection, source locations, Review actions, and six-field JSON without `type`.
- Preserve explicit-context recipes and conservative unresolved-source behavior.
- Retain applicable Application end-to-end compatibility notes.
- Keep documentation in English and customer data outside repository files and packages.
- Do not commit, push, release, or modify original instance/template configurations.

## Review focus

- No-context advice must omit actual values and YAML even for nested or multiline parameter values.
- Application end-to-end advice must retain its compatibility note without inventing unsupported fields.
- Explicit context must retain scalar types, application containers, and exact file actions.
- HTML, JSON, and console must expose the same generic recommendation and preserve finding evidence.
- Supplying unresolved context must retain its existing reason without fabricated edit instructions.

## Task 1: General advice without template context

**Files:**

- Modify: module `src/envgene_linter/template_default_guidance.py`.
- Test: module `tests/test_template_default_guidance.py` and `tests/test_place12.py`.
- Update: module readmes, changelog, algorithms, and specifications catalog.

**Interfaces:**

- Consume and retain: `build_template_default_hint(..., context: TemplateContext | None = None) -> str`.
- Produce: generic advice when context is absent; existing explicit-context guidance otherwise.

- [x] **Step 1: Add failing no-context assertions.**

Require generic advice with no observed values, YAML blocks, or file actions.
Update real CLI report tests to assert matching generic hints and preserved evidence.
Move YAML serialization and application-container checks to a real local template fixture.
Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py`.
Expected: absent-context assertions fail before implementation.

- [x] **Step 2: Add the early return and retain compatibility notes.**

Return general advice before reconstructing parameter dictionaries.
Keep applicable Application end-to-end notes in either mode and preserve all explicit-context branches.
Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py tests/test_template_context.py tests/test_cli.py`.
Expected: all focused tests pass.

- [x] **Step 3: Update documentation and run checks.**

State the mode distinction in readmes and algorithms and record the functional change in the changelog.
Run the full module suite, Ruff, formatting, Markdownlint, and terminology Textlint.
Expected: no new failures compared with the established three macOS Credentials casing failures.
Request one independent read-only review of this request's diff against its before snapshots.

- [x] **Step 4: Verify the local build.**

Build offline archives and verify the package allowlist. Exercise the built CLI in both modes on temporary copies.
Update the installed local CLI from the tested wheel, retaining the existing original reports.
Keep changes uncommitted and retain the task ledger.
