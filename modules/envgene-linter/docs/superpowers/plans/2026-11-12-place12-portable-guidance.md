# PLACE-12 portable guidance implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` in the current session.

**Goal:** Without `-t`, explain what, how, and where to add template defaults without inventing destination paths.

**Architecture:** Reconstruct the observed YAML in both modes and render a portable recipe for absent context.
The recipe uses a name substitution slot and an append-only list item. Explicit-context recipes stay unchanged.

**Tech stack:** Python 3.12, ruamel.yaml, Click, pytest, Ruff, Markdownlint, and Textlint.

**Spec:** [Guidance modes](/modules/envgene-linter/docs/superpowers/specs/2026-11-12-place12-guidance-modes-design.md).

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Portable recipes without template paths](#task-1-portable-recipes-without-template-paths)

## Global constraints

- Preserve candidate detection, grouping, source evidence, Review actions, and JSON's six fields without `type`.
- Preserve exact and unresolved explicit-context behavior and unsupported Application end-to-end diagnostics.
- Preserve existing reference order and fields. Do not automatically edit configuration files.
- Keep documentation English and customer data outside repository files and packages.
- Preserve earlier uncommitted work. Do not commit, push, publish, or start Docker.

## Review focus

- Cloud and Namespace recipes must choose the correct list for every parameter category.
- Unknown existing lists must receive an append-only item, not replacement-shaped descriptor YAML.
- Scalar, nested, multiline, application, and literal dotted values must survive YAML serialization in both modes.
- Application end-to-end recipes must retain their support warning and withhold unsupported attachment instructions.
- Without `-t`, naming must be explicitly provisional and no destination paths or entry indices may be invented.

## Task 1: Portable recipes without template paths

**Files:**

- Modify: module `src/envgene_linter/template_default_guidance.py`.
- Test: module `tests/test_template_default_guidance.py` and `tests/test_place12.py`.
- Update: module readmes, changelog, algorithms, and the current guidance modes design.

**Interfaces:**

- Retain: `build_template_default_hint(..., context: TemplateContext | None = None) -> str`.
- Produce: portable ParameterSet YAML and logical append instructions when context is absent.
- Retain: exact source-backed recipes when context is supplied.

- [x] **Step 1: Write and run failing portable-recipe assertions.**

Cover all Cloud and Namespace categories, supported application scopes, the unsupported application scope,
actual YAML values, name substitution, logical association selection, append order, and absent destination paths.
Assert restored YAML in real CLI HTML/JSON/console and preserve the six-field schema and source evidence.
Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py`.
Expected: no-context recipe assertions fail on the preceding generic advice.

- [x] **Step 2: Render the portable recipe after reconstructing YAML.**

Use `<shared-paramset-name>` consistently in ParameterSet content and the new reference item.
Identify the named environment template, association target, and category-specific override list.
Show only the new list item, retain existing fields and order, and explain later instance cleanup.
Retain support notes without unsupported attachment instructions.
Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py tests/test_template_context.py tests/test_cli.py`.
Expected: all focused tests pass.

- [x] **Step 3: Update documentation and verify.**

Correct the distinction between portable and exact guidance in the design, readmes, algorithms, and changelog.
Run the full module suite and applicable code and documentation linters.
Expected: no new failures compared with the established three Credentials casing failures.
Request one independent read-only review using this request's before snapshots.

- [x] **Step 4: Build and refresh the no-context report.**

Build offline archives and run the distribution allowlist check.
Verify both modes on temporary copies. Update the installed CLI and rerun the original instance without `-t`.
Check restored YAML, logical attachment instructions, matching HTML/JSON, and unchanged configuration inputs.
