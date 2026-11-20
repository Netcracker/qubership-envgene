# PLACE-12 complete ParameterSet relocation implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` for this requested implementation.

**Goal:** Propose complete ParameterSet relocation with existing bindings preserved when the complete source is eligible.

**Architecture:** Add a conservative selector beside PLACE-12 and reuse the existing recommendation renderer.
TemplateContext checks the selected destination. Partial candidates retain descriptor guidance.

**Tech stack:** Python, ruamel.yaml, pytest, and the existing HTML and JSON renderers.

**Spec:** [Relocation design](/modules/envgene-linter/docs/superpowers/specs/2026-11-11-place12-paramset-relocation-design.md).

- [Constraints and review focus](#constraints-and-review-focus)
- [Implementation and verification](#implementation-and-verification)

## Constraints and review focus

- Preserve every existing candidate guard, source reference, scalar type, and instance binding order.
- Never edit customer sources, access external artifacts, publish results, or commit customer data.
- Reject partial files, occupied names, extra consumers, multiple sources, and unsupported fields.
- Document metadata normalization and the instance-only resolver limitation.
- Keep Information / Review and the six JSON fields. Leave changes uncommitted.

## Implementation and verification

**Files:** `paramset_relocation.py`, `template_context.py`, `template_default_guidance.py`, `rules/place12.py`,
PLACE-12 tests, the algorithm, specification index, and functional changelog.

**Interfaces:** A relocation selector consumes existing candidate owners and local context.
It returns a complete file proposal or a reason to retain partial guidance.

- [x] Add failing tests for whole-file guidance, partial payloads, conflicts, metadata, and extra bindings.
- [x] Implement the selector and destination guard without changing the shared instance resolver.
- [x] Integrate the whole-file recommendation into HTML and JSON through the existing hint field.
- [x] Run focused tests, the full suite, and Python and documentation linters.
- [x] Run a private check against the selected instance and template repositories.
- [x] Try the proposed relocation in temporary copies and compare actual EnvGene ParameterSet processing.
- [x] Review the change and record remaining artifact and resolver uncertainties.
