# Schema migration and validation

- [Problem](#problem)
- [Example](#example)
- [Design](#design)
- [Outputs without a schema check at write time](#outputs-without-a-schema-check-at-write-time)
- [What changes for the user](#what-changes-for-the-user)
- [Verification](#verification)
- [Out of scope](#out-of-scope)
- [Open questions](#open-questions)
- [Constraints](#constraints)

## Problem

EnvGene loads schemas through several paths. Callers pass local file paths, packages carry duplicate copies, and `CurrentEnvInstanceStore.flush()` sorts and writes without validating the final object. Validation is spread across mutation steps, so an object may be validated more than once and later mutations may not be covered.

The approved spreadsheet lists schemas to migrate or remove and includes per-file notes. The base image
does not supply schemas. The image build copies the repository `schemas/` directory to `/schemas`.

## Example

Before, callers select local schema paths and validate objects during processing:

```python
schema_path = get_schema_dir() / "namespace.schema.json"
validate_yaml_by_scheme_or_fail(input_yaml_content=namespace, schema_file_path=str(schema_path))
store.beautify(namespace_path, schema_path)
```

Callers select an exact schema filename. The store validates the object once when it binds the model:

```python
store.beautify(namespace_path, "namespace.schema.json")
store.flush()
```

The schema getter resolves the filename from `JSON_SCHEMAS_DIR`.

## Design

`envgene-shared` owns schema lookup and the common validation function. `envgenehelper` exports `get_schema` for its callers.
Shared-only consumers such as the GSF pre-commit hook use `envgene-shared` directly.

The getter accepts an exact schema filename and returns parsed schema content from `JSON_SCHEMAS_DIR`, which defaults to `/schemas`. It rejects path components and reports an unknown filename clearly. EnvGene keeps the only schema source in the root `schemas/` directory, and consumers configure that directory explicitly.

The image build copies the repository `schemas/` directory to `/schemas`. The base image does not supply
schemas, so there is no merge step. Relative `$ref` references resolve against that directory.

All schema files remain in the root `schemas/` directory. Python packages do not include schema copies. Runtime images and standalone hook packages stage files from this directory and set `JSON_SCHEMAS_DIR` to the staged directory. The canonical config schema's `save_artifacts` block is kept in the root schema.

For generated environment objects, `CurrentEnvInstanceStore.beautify()` binds a model and records its schema filename.
The first binding validates the object against JSON Schema. `get(path)` then returns the model during processing.
Field assignments and changes to typed containers use model validation without rerunning JSON Schema validation.
The models preserve YAML comments and formatting. `flush()` sorts, formats, and writes the model's YAML representation.
Replacing a stored object validates the replacement before it becomes available to callers.
Validation logs and model construction errors include the target file path and schema filename.

Credential models enforce type-specific data fields and external credential restrictions.
Registry V2 models enforce nested configuration fields, provider-specific authentication methods, and conditional fields.
Environment Definition and Template Descriptor models validate their nested objects and containers.
ParameterSet models require `parameters` or `applications`, as the schema does.

`bg_domain.yml` uses `bg-domain.schema.json`. The store binds its model after rendering.
`validate_bgd()` checks that the namespaces it references exist.
The controller URL is optional because existing templates omit it. Its value must be a string when provided.

The SBOM generator uses `generated-application.sbom.schema.json`, moved from its Python package without changing its
validation rules. This schema permits generated SBOMs without serial numbers or timestamps. The separate
`application.sbom.schema.json` contract remains unchanged. `solution.sbom.schema.json` also moves to the common directory.

Direct writers validate each final object once before serialization. AppDefs and RegDefs written in `dual` mode share that
validation across both copies. Cached validators serve repeated input checks and resolve relative references from the
configured directory. Standalone sorting runs the common validator before the sorting library.
The artifact searcher's Registry V2 parser uses the same cached validator.

## Outputs without a schema check at write time

The following paths do not run JSON Schema validation immediately before writing.
Input validation and typed models cover some paths. Others have no matching schema in `schemas/`.

| Output                                               | Writer                        | Current coverage or gap                                               |
|------------------------------------------------------|-------------------------------|-----------------------------------------------------------------------|
| `Inventory/env_definition.yml`                       | `env_inventory_generation.py` | Content checked through `env-inventory-content.schema.json` on input. |
| `Inventory/parameters/*.yml`                         | `handle_objects()`            | Content checked through `paramset.schema.json` on input.              |
| `Inventory/credentials/*.yml`                        | `handle_objects()`            | Content checked through `credential.schema.json` before encryption.   |
| `Inventory/resource_profiles/*.yml`                  | `handle_objects()`            | Content checked through `resource-profile.schema.json` on input.      |
| `Inventory/env_definition.yml` after version changes | `set_template_version.py`     | No final schema check after the version update.                       |
| `configuration/registry.yml`                         | `generate_sboms.py`           | Registry models cover new entries. No final check of the merged file. |
| `bg_domain.yml`                                      | `generate_bgd_file()`         | A typed model checks structure. `validate_bgd()` checks references.   |
| `Inventory/namespace-map.yml`                        | `namespace_render.py`         | No matching schema.                                                   |
| `Inventory/deploy-plan.yml`                          | `EnvgeneDeployPlan.write()`   | Deployment plan models validate content. No matching JSON schema.     |
| `Inventory/solution-descriptor/sd.yaml`              | `process_sd.py`               | No matching schema.                                                   |
| `Inventory/templateVariables/*.yml`                  | `handle_objects()`            | Free-form mappings checked by the inventory content input schema.     |
| `shared_template_variables/*.yml`                    | `handle_objects()`            | Free-form mappings checked by the inventory content input schema.     |

The table covers environment generation, inventory generation, version updates, and generated registry writes.
It does not assign an unrelated schema to an output that has no contract in this repository.

## What changes for the user

- Invalid schema-backed generated output fails before the file is written.
- Schema lookup by filename returns the same schema regardless of the caller's working directory.
- GSF shared-only validation continues to work without installing `envgenehelper`.

## Verification

- Test exact-name lookup, unknown names, path-like names, and every schema in the approved inventory.
- Test `$ref` resolution from the schema directory.
- Test that invalid mutations fail during processing and JSON Schema validation runs once at model binding.
- Test BGD structure, model mutations, and namespace reference checks during generation.
- Test schema-backed direct writers and shared-only config and credential validation.
- Test schema loading outside the repository root with `JSON_SCHEMAS_DIR` configured.
- Run the `envgene-shared` and `envgenehelper` tests, then `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/`.

## Out of scope

- Adding models to outputs without an applicable schema.
- Changing validation rules or schema contents beyond reconciling approved migrated schemas and existing duplicate drift.
- Validating YAML outputs that have no applicable JSON schema.
- Runtime network access to fetch schemas from Qubership.

## Open questions

- Confirm the exact filename disposition and replacement mapping for each row in the approved spreadsheet.

## Constraints

- Keep the implementation to the minimum code that solves the approved scope. Add no speculative features or single-use abstractions.
- Change only code required by this design, match local style, and do not clean up unrelated code.
- Test the real schema loader, validator, and write path. Mock only external dependencies, not the behavior under test.
- Use meaningful names, add no comments or docstrings, avoid compose-only wrappers, and do not assert log text.
