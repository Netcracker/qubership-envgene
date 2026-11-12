# PLACE-12 template edit instructions

- [Purpose and approach](#purpose-and-approach)
- [Recommendation contract](#recommendation-contract)
- [Validation](#validation)

## Purpose and approach

When `-t` supplies local template sources, PLACE-12 identifies the exact files and descriptor entry to change.
The user confirmed that this applies to PLACE-12. PLACE-1 and PLACE-2 keep their existing recommendations.

The chosen approach extends the existing recipe with absolute action paths and the selected entry's source position.
Repository labels alone leave the reader to combine paths manually. Automatic editing would exceed this request.
Keep the existing source eligibility, name reservation, grouping, and relocation decisions.

## Recommendation contract

Begin eligible local recipes with `Template repository changes:`.
For a new ParameterSet, show `Create file:` with the absolute destination under the supplied template repository,
followed by the complete proposed ParameterSet YAML. Mention parent directory creation when needed.

For a partial match, show `Edit file:` with the absolute selected descriptor path, entry line, and column.
Show the exact YAML path, such as `namespaces[1].template_override.deployParameterSets`.
Indices in these paths are zero-based. Keep the association target in the instruction.
Append the new reference last, preserving the existing reference order.
Show the descriptor merge fragment and state that the reader merges only the selected entry and relevant list.
Retain unrelated entries and override fields.

For a complete transfer, retain the original name and show the absolute destination.
Keep the existing complete Inventory reference lists as observations, not replacement YAML.
Explain why no descriptor override is needed. Identify source copies with absolute instance paths and require
artifact publication, environment updates, and generation verification before removal.

If local selection is unresolved, show the reason and the absolute descriptor path when known.
Do not invent an edit location or destination. Without local context, keep the existing observation-only guidance.
Anchored entries and inherited keys can lack occurrence-specific coordinates.
In that case, retain the known YAML entry selector and require review before suggesting any create or edit action.
Accept both template repository roots and their `templates/` directories without bypassing link safeguards.

HTML, JSON, and console receive the same recommendation. Keep the JSON schema at six fields without `type`.
No template, instance, or descriptor file is changed by this feature.
Keep documentation and repository fixtures generic; customer examples remain in local reports only.

## Validation

Use real descriptors for Cloud string/object forms and Namespace entries beyond the first list item.
Verify file paths, entry coordinates, YAML selectors, appended reference order, preserved YAML types,
complete-transfer bindings, unresolved fallbacks, unchanged sources, and matching HTML/JSON guidance.
Run the full module suite, compare known baseline failures, lint the changes, build the package,
and rerun the existing local example with `-i` and `-t`.
