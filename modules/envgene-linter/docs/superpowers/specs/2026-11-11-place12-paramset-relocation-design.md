# PLACE-12 complete ParameterSet relocation design

- [Intent and approaches](#intent-and-approaches)
- [Eligibility](#eligibility)
- [Recommendation](#recommendation)
- [Verification and limits](#verification-and-limits)

## Intent and approaches

A complete shared ParameterSet can live in the Template repository while Environment Inventory keeps its existing binding.
EnvGene stages template and instance ParameterSets into one catalog before processing those bindings.
This shares the file without assigning the ParameterSet to every consumer of the Environment Template.

The requested approach preserves the reference name, binding category, target, and reference order.
Partial matches retain the existing recommendation for a separate shared ParameterSet and descriptor override.
Automatic source changes and artifact publication remain outside the CLI check.

## Eligibility

The recommendation requires explicit local template context and all existing PLACE-12 candidate guards.
Every participant selects one readable, environment-owned source for the same literal reference name.
At least two distinct source files participate. Each filename agrees with its `name` field.
Complete `parameters` and `applications` payloads compare equal with YAML scalar types preserved.
Only `name`, `version`, `parameters`, and `applications` are supported at the top level.
Application entries support only `appName`, the generator's legacy `name` alias, and `parameters`.
Present parameter and application containers must have their expected mapping and list types.

Every parameter leaf in the complete file must belong to the current eligible finding.
This deliberately leaves files spanning several application scopes as partial recommendations.
Empty files, masked values, additional consumers or bindings, and multiple selected sources cannot establish relocation.
All explicit consumers of the reference in the same artifact must belong to the compared group and binding context.
The consumer check includes primary, origin, and peer artifact selectors.
Dependencies on the physical source through other reference names also block source removal.
Participants with distinct role-specific artifacts retain partial guidance because the destination role is unverified.

The selected descriptor must contain a unique static target with a local template path.
The destination must be readable and unlinked. Any existing or reserved ParameterSet with the same name blocks relocation.
Known references in local template objects and descriptor overrides also reserve their names.
Literal names after Jinja control flow remain potential references and conservatively block relocation.

Identical numeric `version` fields are retained. Other version combinations produce an explicit note and omit that
deprecated field from the proposed file. No source metadata is silently selected from one environment.

## Recommendation

The HTML and JSON recommendation shows the complete proposed file under `templates/parameters/` with its original name.
It lists the complete existing reference list for each participant without presenting replacement Inventory YAML.
It lists the source copies eligible for removal after migration.
The report preserves Information / Review and the existing six JSON fields.
Publication and environment artifact updates precede removal of source copies.
The recommendation states that no descriptor override is required for this storage-only alternative.

## Verification and limits

Use synthetic tests for complete and partial payloads, type differences, application content, metadata differences,
filename conflicts, extra consumers, multiple bindings, and unsupported source fields.
Verify that recommendations leave source bytes unchanged and retain existing partial guidance.
Run the selected customer example only in private temporary copies.
Compare actual EnvGene ParameterSet processing before and after the proposed relocation.

Local source inspection does not prove published artifact equivalence or discover external consumers.
The instance-only resolver used by other checks is unchanged. INT-2 can retain Review for template-only references.
This extension proposes relocation, rather than asserting that an external artifact already contains the file.
