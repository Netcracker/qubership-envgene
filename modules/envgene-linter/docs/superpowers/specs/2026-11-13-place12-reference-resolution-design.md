# PLACE-12 local reference resolution

- [Requirements](#requirements)
- [Design](#design)
- [Validation](#validation)

## Requirements

Resolve supported dynamic ParameterSet references from each participating instance environment.
Keep candidate detection, Review actions, source provenance, report fields, and read-only configuration behavior.
A blocked recommendation explicitly states that no template relocation proposal was generated.
It identifies unresolved reference expressions or control-flow locations and explains the next review step.

Supported expressions contain literal text and current_env data paths using attributes or literal string keys.
Allow selected Cloud Passport data and the environment's name and environmentName.
Use ordinary nonempty strings or finite numeric selector values. Preserve spelling and case.
Calls, filters, arbitrary expressions, protected paths, tags, booleans, unsupported values, and unsafe names remain Review.
Never render templates, evaluate Python, read process variables, or fetch artifacts to resolve names.

## Design

Parse Jinja into an abstract syntax tree and inspect its nodes without compiling or rendering.
Read only mapping keys from a separately constructed context for each participant.
Use the selected local Cloud Passport and the authored environment definition.
Validate ancestor containers before extracting environment identity fields so custom tags cannot lose their uncertainty.
Unknown inputs in one environment cannot be supplied by another environment's context.

Resolve each dynamic reference and require exactly one readable local ParameterSet source.
Missing, ambiguous, linked, or unrendered sources retain a located explanation and no cleanup instructions.
Collect the selected references per environment and compare source definitions using those actual names.
Different resolved versions can participate in one template group without claiming artifact equivalence.

Permit a reference list in an unconditional YAML prefix only when another unconditional root key closes it
before later Jinja control flow. Inspect the remaining syntax to exclude list redefinitions, emitted expressions,
includes, calls, assignments, macros, filters, and other output-changing constructs.
Control flow affecting the list itself remains unresolved.
Require standalone statements without whitespace controls. Later emitted content must stay inside the unrelated
root value. Root-key output, including escaped or explicit key forms, remains unresolved.
Bound parser failures and syntax traversal. Uncertainty retains Review.

Keep an existing reference in its position when selected for every participant.
Mixed membership cannot justify one shared append instruction and retains Review.
Reserve resolved reference names when choosing a new ParameterSet name.
Whole-file relocation uses the same resolved membership checks while preserving its previous ownership guards.

Display resolved references in source-comparison recipes.
Keep original source coordinates and distinguish observed values from actionable recipes in blocked reports.
ParameterSet merging, scalar/list conflicts, and instance cleanup keep the
[existing merge contract](/modules/envgene-linter/docs/superpowers/specs/2026-11-13-place12-merge-cleanup-design.md).

The alternatives were leaving all expressions unresolved and executing full Jinja rendering.
Data-path resolution supports available local inputs without executing template logic.

## Validation

Test attribute and bracket paths, same and different participant values, missing inputs, and unsupported expressions.
Test missing, duplicate, and unrendered resolved targets, reference-order preservation, and mixed membership.
Test unrelated control flow, actual conditional list changes, includes, injected output, and parser limits.
Verify unchanged findings and source files, all report formats, and the six-field JSON contract.
Use synthetic fixtures. Keep real repository evidence outside committed source, tests, and documentation.
