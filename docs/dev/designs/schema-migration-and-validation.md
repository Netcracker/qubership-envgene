# Schema migration and validation

## Problem

EnvGene loads schemas through several paths. Callers pass local file paths, packages carry duplicate copies, and `CurrentEnvInstanceStore.flush()` sorts and writes without validating the final object. Validation is spread across mutation steps, so an object may be validated more than once and later mutations may not be covered.

The approved spreadsheet screenshot lists schemas to migrate or remove and includes per-file notes. The runtime image also supplies schemas that must remain authoritative. Schemas supplied by the GitLab repository may add filenames but must not replace image schemas.

## Example

Before, callers select local schema paths and validate objects during processing:

```python
schema_path = get_schema_dir() / "namespace.schema.json"
validate_yaml_by_scheme_or_fail(input_yaml_content=namespace, schema_file_path=str(schema_path))
store.beautify(namespace_path, schema_path)
```

After, callers select by exact filename and register the final output schema. The shared write path validates once before serialization:

```python
store.beautify(namespace_path, "namespace.schema.json")
store.flush()
```

The schema getter resolves the filename from the effective schema set. The GitLab schema assembly adds only filenames absent from the base image.

## Design

`envgene-shared` owns schema lookup and the common validation function. It is already a dependency of `envgenehelper` and is used by shared-only consumers such as the GSF pre-commit hook. Shared callers must not import `envgenehelper`.

The getter accepts an exact schema filename and returns parsed schema content from `JSON_SCHEMAS_DIR`, which defaults to `/schemas`. It rejects path components and reports an unknown filename clearly. EnvGene keeps the only schema source in the root `schemas/` directory, and consumers configure that directory explicitly.

The effective schema set contains image-provided schemas first and GitLab-provided additions second. Assembly copies a GitLab schema only when the destination filename does not exist. A filename collision preserves the image schema and does not replace it. Relative `$ref` references resolve against the effective schema directory.

All schema files remain in the root `schemas/` directory. Python packages do not include schema copies. Runtime images and standalone hook packages stage files from this directory and set `JSON_SCHEMAS_DIR` to the staged directory. The canonical config schema's `save_artifacts` block is kept in the root schema.

For generated environment objects, `CurrentEnvInstanceStore` records a schema filename for each schema-backed output. `flush()` validates the final in-memory object once, then sorts, formats, and writes it. Store writes without schema metadata are not silently treated as validated. Schema-backed direct writers use the same shared validation function immediately before serialization. Input validation remains where it protects data before the build uses it and is not a duplicate output check.

Typed object models do not change in this work. Objects remain dictionaries or YAML mappings.

## What changes for the user

- Invalid schema-backed generated output fails before the file is written.
- A GitLab schema can add a new filename but cannot replace an image-provided schema.
- Schema lookup by filename returns the same schema regardless of the caller's working directory.
- GSF shared-only validation continues to work without installing `envgenehelper`.

## Verification

- Test exact-name lookup, unknown names, path-like names, and every schema in the approved inventory.
- Test `$ref` resolution from the effective schema set.
- Test that a colliding GitLab filename preserves the base schema and a new filename is added.
- Test that an invalid final object fails at flush after mutation, before any output is written, and that the validator runs once for that output.
- Test schema-backed direct writers and shared-only config and credential validation.
- Test schema loading outside the repository root with `JSON_SCHEMAS_DIR` configured and the image or pipeline schema assembly.
- Run the `envgene-shared` and `envgenehelper` tests, then `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/`.

## Out of scope

- Replacing dictionaries with schema-derived typed object models.
- Changing validation rules or schema contents beyond reconciling approved migrated schemas and existing duplicate drift.
- Validating YAML outputs that have no applicable JSON schema.
- Runtime network access to fetch schemas from Qubership.

## Open questions

- Confirm the GitLab schema source directory and the step that assembles it with the image schema directory.
- Identify the approved schema for `bg_domain.yml` and any schema-backed direct writer not currently registered with a schema.
- Confirm the exact filename disposition and replacement mapping for each row in the screenshot during implementation.

## Constraints

- Keep the implementation to the minimum code that solves the approved scope. Add no speculative features or single-use abstractions.
- Change only code required by this design, match local style, and do not clean up unrelated code.
- Test the real schema loader, validator, and write path. Mock only external dependencies, not the behavior under test.
- Use meaningful names, add no comments or docstrings, avoid compose-only wrappers, and do not assert log text.
