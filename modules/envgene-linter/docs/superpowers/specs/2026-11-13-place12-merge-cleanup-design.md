# PLACE-12 existing ParameterSets and instance cleanup

- [Requirements](#requirements)
- [Design](#design)
- [Acceptance](#acceptance)

## Requirements

PLACE-12 recommendations describe template changes followed by the corresponding instance cleanup.
All proposals remain Review and require publication, environment updates, and generation checks before cleanup.
The CLI does not edit configuration files. Candidate detection and the six JSON fields remain unchanged.

Remove the generic four-sentence footer about precedence, instance priority, removal review, and source uncertainty.
Retain specific reasons that prevent a concrete proposal.
Show exact source files, positions, and YAML paths for eligible key removal in both CLI modes.
Literal dotted keys and nested keys must remain distinct. Preserve Application containers.
Whole-file relocation retains its existing source and consumer checks before proposing file removal.

With local template context, reuse a uniquely named existing ParameterSet when possible.
Prefer the common original reference name, then the standard generated common name.
Different original names do not establish one original destination name.
Do not select arbitrary files with other names.

Absent keys can be added. Typed-equal values can be reused without adding them again.
Conflicting values or types retain both template and instance entries and receive explicit conflict notes.
Lists inside parameter values compare as complete ordered values.
Only ParameterSet reference lists receive an appended item. Existing references keep their position without duplicates.

## Design

Keep candidate detection in the rule and separate merge planning from recommendation rendering.
Inspect ordinary YAML and valid JSON sources, retaining source positions.
Duplicate stems, inconsistent names, dynamic membership, custom tags, anchors, and unsupported containers block merging.
Unresolved descriptor context also blocks concrete merging and cleanup.

The planner records additions, reused values, conflicts, and blocked targets.
Coordinate all claims to one physical destination before rendering any finding.
Conflicting claims for a key, including parent/child paths, invalidate the affected proposals and their cleanup.
Application claims are separated by their application identity.

Render only added fields as a merge fragment. Preserve unrelated fields and do not copy unrelated values into reports.
Use JSON fragments for JSON destinations. Values that cannot preserve their YAML types in JSON remain conflicts.
Match Application entries by identity and preserve other entries.
An existing Inventory reference requires no descriptor addition.
Otherwise, retain an already selected template reference or append the new reference last.

Cleanup lists only accepted source entries with occurrence-specific coordinates.
Withhold cleanup for anchored entries and source files also selected by consumers outside the proposal's scope.
Blocked targets and conflict-only proposals contain no cleanup instructions.
A merge into an existing file proposes key removal. Whole-file deletion remains limited to complete relocation.
Without local template context, preserve portable YAML and logical attachment guidance without guessed destination paths.

Considered alternatives were always creating a new file and replacing conflicting template values.
The selected approach reuses matching names while retaining conflicts for human review.

## Acceptance

- Remove the requested footer in HTML, JSON, and console recommendations.
- Cover both CLI modes, all categories, nested and dotted keys, and Application parameters.
- Test same-name selection, generated-name fallback, ambiguous inputs, and malformed JSON.
- Preserve scalar types and ordered lists. Preserve unrelated fields and existing reference order.
- Test cross-finding conflicts and cleanup withheld for other consumers.
- Verify copyable YAML/JSON fragments and unchanged configuration files.

The [PLACE-12 algorithm](/modules/envgene-linter/docs/algorithms/place12.md) describes the complete processing flow.
