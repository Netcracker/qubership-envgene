# PLACE-12 reference resolution implementation plan

- [Contract](#contract)
- [Tasks](#tasks)
- [Checks](#checks)

## Contract

Implement the approved
[reference resolution design](/modules/envgene-linter/docs/superpowers/specs/2026-11-13-place12-reference-resolution-design.md).
Preserve the pending merge and cleanup changes. Do not commit, push, publish, or modify corpus configurations.

## Tasks

1. Inspect local instance and template inputs without running generation or changing repository reports.
   Keep corpus paths and evidence in local investigation artifacts only.
2. Add failing regression tests for clear blocked recommendations and supported dynamic selectors.
3. Implement a data-only reference evaluator and bounded unconditional-prefix checks.
   Pass participant contexts through source comparison, existing-file merge planning, and whole-file relocation.
4. Retain located Review for incomplete or unsupported inputs and explain what prevented a recipe.
5. Update the algorithm, readmes, index, and functional changelog. Run focused tests and independent review.
6. Run the full suite with case-sensitive temporary paths, build and verify packages, and run the installed CLI
   against the existing local instance/template pair. Verify unchanged source configurations.

## Checks

Exercise different values in participants, missing fields, invalid selectors, protected paths, parser limits,
missing or ambiguous target files, harmless later control flow, actual list changes, and reference duplication.
Ensure candidate evidence and report schemas remain unchanged and no template code is executed.
