# PLACE-12 guidance with and without template context

- [Purpose and approach](#purpose-and-approach)
- [Behavior](#behavior)
- [Validation](#validation)

## Purpose and approach

Without `-t`, PLACE-12 explains what to add, how to connect it, and which logical template association to update.
With `-t`, local template inspection adds concrete destination files and source positions.
The user clarified that abstract advice means no concrete destination path, not removal of YAML instructions.

Render the observed ParameterSet values in both modes.
Without source inspection, use a clearly identified name placeholder and an append-only reference item.
Generic advice alone does not explain a fix. Guessing descriptor paths or existing reference lists would be misleading.
Candidate detection and report schemas remain unchanged.

## Behavior

Without local template context, show the actual repeated values as ParameterSet YAML, preserving scalar types,
nested and literal dotted keys, and application containers.
Use `<shared-paramset-name>` as a substitution slot and explain that the chosen name must be unused and match
the ParameterSet filename and reference.

Identify the existing Cloud association or Namespace association target in the named environment template.
Name the appropriate `template_override.deployParameterSets`, `template_override.e2eParameterSets`, or
`template_override.technicalConfigurationParameterSets` list.
Show only the new reference item and instruct the reader to append it last, retaining existing references and fields.
Explain how to create the override list when absent and how to retain a Cloud string's value in `template_path`
when converting that association to object form.

Require artifact publication, environment updates, generation verification, and consumer review before removing
only the shown duplicate parameter entries. Keep other values and existing instance references.
Mention `-t` / `--template-repo` for exact local destinations and source comparisons.
Do not invent absolute or relative destination filenames, descriptor paths, list indices, or existing reference lists.
Retain the unsupported Application `e2eParameters` note and withhold an attachment instruction for that scope.

Keep findings, grouping, source locations, parameter keys, template identity, Review actions, and exit codes unchanged.
The recommendation text is identical in HTML, JSON, and console output.

An explicitly supplied template context retains its existing recipes, typed YAML, exact edit locations,
complete-transfer guidance, and unresolved-source diagnostics. Do not invent actions for unresolved context.
Configuration files remain unchanged. This task does not alter other rules or publish a release.

## Validation

Verify portable recipes include actual values, logical targets, category-correct append instructions, and no invented
destination paths across parameter categories and supported application scopes.
Run real CLI checks without `-t` and compare HTML, JSON, console, findings, and source bytes.
Keep typed-YAML and application-container tests in both modes.
Retain exact-recipe and unresolved-source tests, then run the full module suite and applicable linters.
