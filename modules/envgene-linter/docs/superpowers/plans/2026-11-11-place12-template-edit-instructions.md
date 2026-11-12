# PLACE-12 template edit instructions implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` in the current session.
> Steps use checkbox syntax for tracking.

**Goal:** Show exact template files, descriptor source positions, and YAML paths for PLACE-12 changes with `-t`.

**Architecture:** Extend `TemplateProposal` with selected-entry coordinates.
Render explicit action paths in the existing recipe builders and retain one shared recommendation for all reports.

**Tech stack:** Python 3.12, ruamel.yaml, pytest, Ruff, Markdownlint, and Textlint.

**Spec:** [Template edit instructions](/modules/envgene-linter/docs/superpowers/specs/2026-11-11-place12-template-edit-instructions-design.md).

- [Global constraints](#global-constraints)
- [Review focus](#review-focus)
- [Task 1: Exact template edit recipes](#task-1-exact-template-edit-recipes)

## Global constraints

- Apply only to PLACE-12; preserve eligibility, grouping, name reservation, and relocation decisions.
- Keep documentation in English and customer examples in local reports only.
- Preserve existing work, JSON's six fields without `type`, and source inspection safeguards.
- Do not automatically edit configuration files, commit, push, publish, or start Docker.

## Review focus

- Namespace selection beyond index zero must identify the actual entry and source line.
- A scalar Cloud association must identify the existing key before conversion to object form.
- Existing override lists and unrelated descriptor entries must survive application of the merge fragment.
- Template-directory inputs and unresolved or linked sources must retain truthful paths and conservative fallbacks.
- YAML aliases and inherited mapping keys must not direct the reader to a shared anchor or fallback coordinates.
- Whole-file transfers must preserve bindings and distinguish template creation from later instance cleanup.

## Task 1: Exact template edit recipes

**Files:**

- Modify: `src/envgene_linter/template_context.py`, `template_default_guidance.py`, and `rules/place12.py` in the module.
- Test: module `tests/test_template_default_guidance.py` and `tests/test_place12.py`.
- Update: module readmes, changelog, PLACE-12 and report algorithms, and the specifications catalog.

**Interfaces:**

- Consume: `TemplateContext.directory`, loaded descriptor positions, and the existing relocation proposal.
- Produce: `TemplateProposal.entry_path: tuple[str | int, ...]` and `entry_position: tuple[int, int] | None`.
- Produce: `build_relocation_hint(proposal, scope, *, context: TemplateContext, instance_root: Path) -> str`.
- Retain: `build_template_default_hint(...) -> str` and the existing finding and report schemas.

- [x] **Step 1: Add failing recipe tests.**

Cover absolute create/edit paths, Namespace index one and multiline coordinates, Cloud scalar/object forms,
existing override ordering, template-directory inputs, unknown destinations, and unchanged source bytes.
Update existing command-shape assertions to require exact file actions rather than obsolete relative instructions.
Add integration assertions for complete and partial HTML/JSON recommendations and full-transfer instance paths.
Cover aliased Cloud and Namespace entries and inherited root keys with a selector-only review fallback.

- [x] **Step 2: Verify the tests fail on the old guidance.**

Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py` from the module.
Expected: new action-path and location assertions fail while existing eligibility tests remain green.

- [x] **Step 3: Carry selected-entry coordinates.**

In `TemplateContext.propose`, retain the exact Cloud or Namespace YAML path and its loaded source position.
Populate source coordinates only when the occurrence is established. Do not introduce another source parse.
If anchors or inherited keys prevent local occurrence coordinates, retain the selector and withhold file actions.

- [x] **Step 4: Render explicit template change actions.**

Use the supplied template root for absolute `Create file:` and `Edit file:` paths.
Render selected-entry coordinates and the full YAML path to the relevant override list.
Keep copyable ParameterSet YAML, merge-only descriptor guidance, append order, and conservative fallbacks.
Pass context and instance root to complete-transfer guidance, with absolute cleanup sources after publication.

- [x] **Step 5: Verify recipes and update documentation.**

Run: `python3 -m pytest -q tests/test_template_default_guidance.py tests/test_place12.py tests/test_template_context.py tests/test_cli.py`.
Expected: all focused tests pass. Document observable paths, selectors, and the unchanged review-only workflow.

- [x] **Step 6: Run final checks and one independent review.**

Run: `python3 -m pytest -q` and compare failures with the baseline.
Expected: no new failures; record known macOS failures by name.
Run Ruff, formatting checks, Markdownlint with the repository configuration, and terminology Textlint.
Expected: applicable checks pass without restyling unrelated files.
Request one read-only review of this request's diff against its before snapshots.
Fix important findings in one regression-test pass and retain the ledger while changes remain uncommitted.

- [x] **Step 7: Build and regenerate the local example.**

Build offline wheel and source archives and run the exact distribution allowlist check.
Install the tested local wheel, then run the established instance/template pair with `-i` and `-t`.
Verify absolute actions, source coordinates, matching HTML/JSON, and unchanged configuration inputs.
