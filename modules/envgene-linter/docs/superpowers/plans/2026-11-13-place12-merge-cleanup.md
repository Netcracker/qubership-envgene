# PLACE-12 merge and cleanup implementation plan

- [Contract](#contract)
- [Tasks](#tasks)
- [Validation](#validation)

## Contract

Implement the approved
[merge and cleanup design](/modules/envgene-linter/docs/superpowers/specs/2026-11-13-place12-merge-cleanup-design.md).
Keep the existing candidate criteria, CLI arguments, JSON schema, and Review action.
Configuration mutation, commits, pushes, issue comments, and publication are outside this implementation step.

## Tasks

1. Add regression tests for exact instance cleanup, same-name merging, typed conflicts, and reference order.
   Run the tests against the previous implementation and confirm the expected failures.
2. Add a merge planner with existing-source lookup and batch coordination of destination claims.
   Resolve matching original names before generated names. Block ambiguity without a fallback replacement file.
   Render merge fragments and cleanup only after all claims are known.
3. Add located cleanup instructions to portable and resolved recipes.
   Preserve other parameters and bindings. Withhold cleanup for unresolved context and other known consumers.
4. Update existing report assertions and documentation.
   Run the full test suite, documentation checks, and independent code review.
5. Build isolated wheel and source artifacts, verify their contents, and install the wheel into a temporary environment.
   Run both modes against the existing local test pair and check that source configurations are unchanged.
   Retain both report variants locally and leave the report with template context in the checked instance repository.

## Validation

Test added, reused, and conflicting keys, nested mappings, literal dotted keys, and application identities.
Test typed scalar differences, ordered lists, invalid sources, linked sources, and duplicate names.
Test several findings editing the same destination, including conflicting parent/child paths.
Check all three report formats, source coordinates, and the unchanged six-field JSON contract.
Run the full suite with case-sensitive temporary paths so Credential case checks match supported filesystem semantics.
Do not copy private repository fixtures into committed tests or documentation.
