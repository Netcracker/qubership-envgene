# PLACE-10: each connected entity belongs in its type's directory

Status: implemented. This specification describes the agreed independent directory check.

## Purpose and scope

PLACE-10 checks **all five types below**, not only ParameterSets. It checks existing files whose use is established by a local reference or known generator behavior. It does not infer an entity's type from arbitrary YAML content.

| Connected entity type | Required directory |
| --- | --- |
| ParameterSet | `parameters/` |
| Resource Profile Override | `resource_profiles/` |
| Shared Template Variables | `shared-template-variables/` |
| Shared credentials | `credentials/` |
| Cloud Passport | `cloud-passport/` |

A physical file is the file reached after resolving symbolic links. If one physical file is used as two entity types, check it once for each type. Keep a relevant selected alias (the path through which the file was selected) for the diagnostic location.

Unused files, missing references, ambiguous unselected passports, files outside the repository, and files inside `.git` do not participate. Invalid or empty YAML does not prevent a directory check when the file's use is established; no content or secret inspection is needed.

## Directory check

1. Use the existing selected paths for ParameterSets, profiles, shared credentials and passports. Resolve Shared Template Variables as described below.
2. Determine the file's actual scope from its physical path. Among indexed scope bases containing it, choose the deepest: an environment's `Inventory/`, a cluster directory, or repository `environments/`.
3. Require the first path component below that base to equal the type's directory from the table. Nested directories **inside** the required directory are allowed.
4. If a selected physical file is inside the repository but outside all those scope bases, report incorrect placement. Use `environments/<type-directory>/` as the suggested destination.
5. Emit one finding per physical file and type. Sort findings by path, key and line.

This check does not impose a particular layer, basename, or depth inside the required directory. Other rules can report their own findings on the same file; PLACE-10 does not suppress overlaps, including PLACE-9.

Examples:

- `Inventory/parameters/service-deploy.yml`: correct for a selected ParameterSet.
- `Inventory/resource_profiles/team/profile.yml`: correct for a selected Resource Profile Override.
- `Inventory/parameters/resource_profiles/profile.yml`: incorrect for that profile. Its first directory below `Inventory/` is `parameters/`.
- An unreferenced copy in any of these directories produces no PLACE-10 finding.

## Establishing Shared Template Variable usage

Read string elements of the `envTemplate.sharedTemplateVariables` list. Malformed containers, non-string elements and dynamic Jinja references do not select files.

For each literal reference, follow the local generator's `process_additional_template_parameters` lookup. Search these directories in order:

1. `<environment>/Inventory/configuration/`
2. `<environment>/Inventory/configurations/`
3. `<cluster>/configuration/`
4. `<cluster>/configurations/`
5. `environments/configuration/`
6. `environments/configurations/`
7. `<environment>/Inventory/`

Search recursively for a `.yml` or `.yaml` file whose stem (filename without extension) exactly matches the reference. The first matching file in the first matching directory wins. Preserve the generator's `os.walk` encounter order; do not sort files or combine multiple same-named inputs.

Do not traverse directory symlinks, including symlinked ancestors of a search root, or `.git` directories. Reject external paths. If an encountered matching file is unsafe, it occupies the lookup slot: discard it without selecting a lower-priority file. A directory excluded before traversal is not searched.

Resolve usage without parsing file contents. Add default-empty `EnvModel.shared_template_variable_bindings` and `Connections.shared_template_variables` fields without changing existing positional constructor arguments. Include the selected files in global and per-environment connection sets.

### Standard versus generator lookup

The standard names `shared-template-variables/`, while the generator recommends `configuration/` at Inventory,
cluster, and repository scopes. It supports deprecated `configurations/` and recursive Inventory fallback paths.
A used file such as `environments/configuration/variables/common.yml` therefore receives **Warning / Review**.

The hint asks the reader to review supported lookup paths before changing placement. It does not require a move to
`shared-template-variables/` or claim that generation failed. Keep generator lookup unchanged.
An environment's `Inventory/shared-template-variables/` can be reached by the final recursive search.
Do not assume support for other unresolved canonical paths.

## Findings and reporting

PLACE-10 is a MUST requirement in the standard. Shared Template Variable location mismatches use **Warning / Review**.
Other entity types retain **Warning / Fix**. Findings preserve CLI exit code `0`.

Each finding contains the entity type, selected filename, and standard directory. Shared Template Variable hints
describe supported lookup locations. Other hints give the expected path in the actual scope.
Use one location at line 1, column 1. `scope` identifies the repository, cluster, or environment, and `key` is the stem.

Catalog description: `Entities belong in their type directories`. PLACE-10 adds the thirteenth console header, after PLACE-9 and before NAME-1. The console shows headers even without findings; HTML contains only sections with findings. No new flags, automatic file changes, network calls or real-repository writes are introduced.

## Verification

Use synthetic fixtures covering:

- Correct and incorrect directories for all five types through actual bindings.
- A misplaced ParameterSet selected through an in-repository symbolic link.
- Valid nested directories and a required directory nested under the wrong directory.
- Legacy profile, shared-credentials and plural passport directories; independent findings from other rules.
- Unused, missing, Jinja, external and `.git` inputs; selected malformed files.
- Multiple aliases for one physical file and one file used as multiple types.
- Shared Template Variable lookup priority, exact stems, unsafe matches and excluded directory ancestors.
- Backward-compatible constructors, direct rule calls, engine calls, console, HTML and catalog integration.

Write English and Russian algorithm documents in the agreed seven-section processing-flow format. Update shared-selection and current rule-order descriptions. Preserve historical decisions and unrelated files.

## Related documents

- [Common connected-only scope](2026-09-11-connected-only-design.md)
- [Current processing algorithm](../../algorithms/place10.md)
- [Implementation](../../../src/envgene_linter/rules/place10.py)
- [Tests](../../../tests/test_place10.py)
