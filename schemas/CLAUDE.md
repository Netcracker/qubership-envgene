# schemas — JSON Schemas for EnvGene Objects

All JSON schemas used for runtime validation of EnvGene objects. Validated via `envgenehelper.yaml_helper.validate_yaml_by_scheme_or_fail()` and `envgenehelper.config_helper`.

## Schema Index

| File | Validates |
|------|-----------|
| `env-definition.schema.json` | `Inventory/env_definition.yml` |
| `config.schema.json` | `configuration/config.yml` |
| `integration.schema.json` | `configuration/integration.yml` |
| `deployer.schema.json` | `configuration/deployer.yml` / `app-deployer/deployer.yml` |
| `credential.schema.json` | Credential files (`credentials.yml`) |
| `secret-stores.schema.json` | `configuration/secret-stores.yml` |
| `namespace.schema.json` | `Namespaces/<ns>/namespace.yml` |
| `application.schema.json` | `Namespaces/<ns>/Applications/<app>/application.yml` |
| `cloud.schema.json` | `Cloud/cloud.yml` |
| `tenant.schema.json` | `Tenant/tenant.yml` |
| `composite-structure.schema.json` | `CompositeStructure/composite_structure.yml` |
| `paramset.schema.json` | ParameterSet files |
| `resource-profile.schema.json` | ResourceProfile files |
| `regdef.schema.json` | Registry Definition v1.0 |
| `regdef-v2.schema.json` | Registry Definition v2.0 (also bundled in `python/envgene/envgenehelper/schemas/`) |
| `appdef.schema.json` | Application Definition |
| `artifact-definition.schema.json` | Artifact Definition v1 |
| `artifact-definition-v2.schema.json` | Artifact Definition v2 |
| `appregdef-config.schema.json` | `configuration/appregdef_config.yaml` |
| `registry.schema.json` | Deprecated `configuration/registry.yml` |
| `effectiveset.schema.json` | Effective Set output files |
| `effectiveset_mapping.schema.json` | ES `mapping.yaml` files |
| `application-manifest.schema.json` | Application manifest (SBOM) |
| `application-manifest-v2.schema.json` | Application manifest v2 |
| `env-template.sbom.schema.json` | Environment template SBOM |
| `application.sbom.schema.json` | Application SBOM |
| `template-descriptor.schema.json` | Template Descriptor |
| `custom-params.schema.json` | `CUSTOM_PARAMS` pipeline variable |
| `env-inventory-content.schema.json` | `ENV_INVENTORY_CONTENT` pipeline variable |

## Usage

Schema files are referenced by relative path from `CI_PROJECT_DIR` (e.g., `schemas/env-definition.schema.json`) or from the `envgenehelper` package resources for regdef schemas.
