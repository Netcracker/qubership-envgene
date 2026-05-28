# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnvGene** is a Git-based infrastructure-as-code tool for generating and versioning Environment configurations from templates. It integrates with GitHub Actions CI/CD and supports: template-based environment generation, Solution Descriptor (SD) processing, Effective Set calculation, credentials management (SOPS-based encryption), and SBOM generation.

This branch (`feature/external_cred_support`) implements **External Credentials** support — integration with external secret stores (Vault, Azure Key Vault, AWS Secrets Manager, GCP Secret Manager) so that credentials never need to be stored in Git.

## Commands

### Testing

Run tests using the devtools Docker environment:

```bash
make up-tests    # Start test container
make bash-tests  # Open shell in container
make run-tests   # Run tests inside container
```

Or directly (requires packages installed via `python/build_modules.sh`):

```bash
# envgenehelper tests
cd python/envgene && pytest envgenehelper/ --capture=no -W ignore::DeprecationWarning

# build_env tests
cd scripts/build_env && pytest tests/
```

### Linting

```bash
ruff check python/<package>/
```

### Building Python packages

```bash
# Standard install
bash python/build_modules.sh

# Local dev mode (uses uv, ~2.8x faster, editable installs)
IS_LOCAL_DEV_TEST_ENVGENE=true bash python/build_modules.sh
```

Install order: `envgene` → `jschon-sort` → `integration` → `artifact-searcher`

### Docker-based development

```bash
make build-tests
make up-tests
make bash-tests
make run-tests
make down
```

## Architecture

### Python packages and their roles

```
envgenehelper (core: YAML, creds, SOPS crypto, schema validation, Pydantic models)
    ↓
jschon-sort      ──→  CLI: sort JSON/YAML by JSON Schema order
integration      ──→  integration loading framework
artifact-searcher ──→  async artifact search/download (S3, GCP, HTTP)
```

### Key directories

| Directory | Purpose |
|---|---|
| `python/envgene/envgenehelper/` | Core library |
| `scripts/build_env/` | Environment Instance generation scripts |
| `creds_rotation/scripts/` | Credential rotation handler |
| `build_effective_set_generator/` | Java/Maven Effective Set calculator |
| `build_envgene/` | Docker image for main engine |
| `build_pipegene/` | Docker image for pipeline orchestration |
| `schemas/` | JSON Schema definitions for all objects |
| `docs/` | Feature documentation |

### Environment Instance generation pipeline

```
main.py:render_environment()
    → EnvGenerator.render_config_env()     # Jinja2 rendering of templates
        → generate_external_cred()         # [external mode] render Credential Template
        → sets isExternalCredEnv flag
    → build_env()                          # process paramsets, cloud passport
        → process_cloud_passport()         # extract credIds from Cloud Passport
    → create_credentials()                 # collect and validate credentials
        → validateExternalCreds()          # [external mode] validate all credIds resolved
        → validate_cred_types()            # enforce local-only or external-only
```

### External Credentials — key concepts

**Two mutually exclusive modes per environment:**
- **local mode** — credentials stored in Git (encrypted via SOPS). Default.
- **external mode** — credentials in external secret store. Activated when `external_credential_template` is present in Template Descriptor.

**Mode detection:** `render_config_env.py:EnvGenerator.generate_external_cred()` sets `self.isExternalCredEnv = True` when it finds and processes `external_credential_template` from the Template Descriptor.

**Supported secret stores:** `vault`, `azure`, `aws`, `gcp` — configured in `/configuration/secret-stores.yml`.

**Credential Reference (`$type: credRef`):** used in `deployParameters` to point a parameter at an external credential by `credId`. Only in `deployParameters` — `e2eParameters` and `technicalConfigurationParameters` are out of scope.

**Secret delivery modes** (chosen per application at Effective Set generation — Java, not Python):
- `SECRET_FLOW=helm-values` → VALS reference (`ref+gcpsecrets://...` string)
- `SECRET_FLOW=external-values` → ESO reference (YAML object for ExternalSecret CR), requires `eso_support: true` in app SBOM

### New functions added in this branch

**`python/envgene/envgenehelper/creds_helper.py`:**
- `extract_external_cred(cred_map)` — parses `{"$type": "credRef", "credId": "..."}`, returns credId or None
- `validate_cred_types(credsMap, isExternalCredEnv, credFile)` — enforces single-category (local or external)
- `has_external_creds(credsMap)` — boolean check
- `copy_creds_to_env_creds_file(env_dir, credsYamlContent, comment, credsSchema)` — writes creds to `Credentials/credentials.yml`

**`scripts/build_env/create_credentials.py`:**
- `validateExternalCreds(envCredsMap, extCredIds)` — validates all referenced credIds exist; orphan warning
- Updated `create_credentials()` — collects `externalCredIds` set, validates mode, calls `validateExternalCreds`
- Updated `getTenantCreds`, `getCloudCreds`, `getNamespaceCreds`, `getApplicationCreds` — accept `isExternalCredEnv` and `externalCredIds`

**`scripts/build_env/render_config_env.py`:**
- `generate_external_cred()` — reads `external_credential_template` from TD, renders Jinja2, validates, copies to Credentials file, sets `isExternalCredEnv = True`

**`scripts/build_env/cloud_passport.py`:**
- `extract_cred_id(param, isExternal)` — routes to `extract_external_cred()` for dict or `get_cred_id_from_cred_macros()` for string

### Schema files

| Schema | Purpose |
|---|---|
| `schemas/credential.schema.json` | Credential object; includes `type: external` with `secretStore`, `remoteRefPath`, `create`, `properties` |
| `schemas/secret-stores.schema.json` | NEW — Secret Store config (`vault`/`azure`/`aws`/`gcp`) |

### Known gaps (not yet implemented in this branch)

- **Effective Set generation** (Java): VALS reference, ESO reference, External Credential Context, `normalizedSecretName` normalization — all in `build_effective_set_generator/`
- **Credential rotation guard**: `creds_rotation_handler.py` has no check for external mode — will fail with KeyError on `data` field if run against external credentials environment
- **`$type: credRef` in non-deploy contexts**: `e2eParameters`, `technicalConfigurationParameters`, `pipeline` context — out of scope
- **Blue-Green deployment** with external credentials
- **Template Composition** with external credentials
- **CMDB import** blocked for external credential environments

### Tooling versions

- Python ~3.12
- Pydantic `2.10.6`, ruyaml `0.91.0`, jschon `0.11.0`
- ruff `0.11.0`, Black line-length 120
- `uv` recommended for local dev (`IS_LOCAL_DEV_TEST_ENVGENE=true`)
