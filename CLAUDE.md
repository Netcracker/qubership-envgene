# CLAUDE.md — EnvGene Persistent Knowledge Base

## Project Purpose

**EnvGene** (Environment Generator) is a git-based tool that generates, versions, and manages cloud environment configurations from reusable templates. It solves the problem of managing parameters for large fleets of similar cloud environments (tenants, namespaces, applications) without manual duplication.

Core pipeline flow:
1. **Inventory Generation** — create/update `env_definition.yml` per environment
2. **SD Processing** — download and merge Solution Descriptors (app manifests from Maven artifacts)
3. **Env Build** — render Jinja2 templates into concrete YAML objects (Tenant, Cloud, Namespace, etc.)
4. **Effective Set Generation** — compute fully-resolved parameter set consumed by ArgoCD / deployment tooling

Two repository types:
- **Template Repository** — Jinja2 templates, base parameter sets, registry/app definitions
- **Instance Repository** — generated environment configs, credentials, SBOMs, effective sets

---

## Tech Stack & Dependencies

### Runtime (`build_envgene/build/requirements.txt`)
| Package | Version | Role |
|---|---|---|
| Jinja2 | 3.1.6 | Template rendering |
| pyyaml / ruamel.yaml | 6.0.2 / 0.18.5 | YAML read/write |
| pydantic | 2.10.6 | Data models & validation |
| jschon | 0.11.0 | JSON Schema evaluation |
| jsonschema | 4.24.1 | Schema validation |
| cryptography | 46.0.5 | Fernet encryption for credentials |
| GitPython | 3.1.45 | Git operations |
| deepmerge | 2.0 | Parameter set merging |
| aiofiles | 24.1.0 | Async file I/O |
| qubership-pipelines-common-library | 2.0.6 | Shared pipeline utilities |
| semantic-version | 2.10.0 | Maven artifact version parsing |

### Internal Python Packages (`python/`)
| Package | pyproject version | Role |
|---|---|---|
| `envgenehelper` | 0.0.1 | Core helpers: YAML, file, crypto, models, plugin engine |
| `artifact_searcher` | 1.0.0 | Downloads Maven artifacts (Nexus/S3/GCS); async via aiohttp |
| `jschon-sort` | 0.2.0 | YAML/JSON schema-aware sorting (`beautifyYaml`) |

### Test Dependencies (`dependencies/tests_requirements.txt`)
- `pytest==8.3.5`, `pytest-bdd`, `junitparser==5.0.0`, `cryptography==46.0.5`

### External Tools
- **SOPS v3.9.0** — secret encryption/decryption (installed at `/usr/local/bin/sops` in CI)
- **Maven/Nexus** — artifact distribution for templates and SDs
- **Python 3.12** — required (both `pyproject.toml` files specify `~=3.12`)

---

## Project Architecture & Directory Structure

```
qubership-envgene/
├── scripts/                        # Main pipeline logic (PYTHONPATH entry)
│   ├── pipeline/
│   │   ├── orchestrator.py         # Entry point: PipelineStep chain
│   │   ├── pipeline_parameters.py  # PipelineParametersHandler.from_env()
│   │   └── pipeline_manager.py
│   ├── build_env/                  # Env build: Jinja rendering, template version
│   ├── inventory/
│   │   └── env_inventory_generation.py  # ENV_INVENTORY_CONTENT / ENV_SPECIFIC_PARAMS
│   ├── sd/
│   │   └── process_sd.py           # SD download, merge modes, delta
│   ├── effective_set/              # ES computation and SBOM retention
│   ├── creds_rotation/             # Credential rotation handler
│   ├── bg_manage/                  # Blue-green state management
│   ├── cloud_passport/             # Cloud passport / CMDB integration
│   └── tests/                      # Unit tests for scripts/ scope
├── python/
│   ├── envgene/envgenehelper/      # Core library: models, YAML helpers, crypt, plugin engine
│   ├── artifact-searcher/          # Maven artifact download (async)
│   ├── jschon-sort/                # Schema-aware YAML sorter
│   └── integration/                # Integration utilities
├── tests/                          # BDD integration tests
│   ├── conftest.py                 # mock_nexus (session), workspace (function) fixtures
│   ├── framework/
│   │   ├── workspace.py            # EnvGeneWorkspace: isolated tmp dir + run_pipeline()
│   │   ├── data_builders.py        # DataBuilder: create_inventory_file, paramset, creds, etc.
│   │   └── base_workspace.py
│   ├── features/                   # Gherkin .feature files
│   │   ├── environment-inventory-generation.feature
│   │   ├── environment-inventory-generation-esp.feature  # @xfail: SCHEMAS_DIR bug
│   │   ├── unified_pipeline_success/
│   │   │   ├── sd-processing.feature
│   │   │   ├── environment-instance-generation.feature
│   │   │   └── eig-positive.feature   # @xfail: jschon_tools.process_json_doc missing
│   │   ├── environment_instance_generation/
│   │   │   └── eig-negative-and-params.feature
│   │   └── effective_set_generation/
│   │       ├── effective-set-deployment.feature
│   │       └── effective-set-no-sbom.feature   # @xfail: jschon_tools bug
│   ├── shared_steps/               # Reusable step definitions
│   │   ├── common_steps.py         # pipeline_log_shows, pipeline_fails, golden compare
│   │   ├── unified_pipeline_steps.py  # initialize_workspace, run_orchestrator
│   │   ├── inventory_gen_steps.py  # ENV_INVENTORY_CONTENT steps
│   │   └── esp_steps.py            # ENV_SPECIFIC_PARAMS steps
│   ├── step_defs/                  # Test entry points (import scenarios + steps)
│   └── mock_server.py              # Simple HTTP file server for mock Nexus (port 8000)
├── test_data/                      # Static fixtures for BDD tests
│   ├── e2e/base/                   # Base environment workspace (no SD)
│   ├── e2e/with-sd/                # Workspace with pre-existing Full SD
│   └── golden/                     # Reference output directories for golden tests
├── docs/                           # All documentation
│   ├── features/                   # Feature specs (authoritative for behavior)
│   ├── how-to/                     # Step-by-step guides
│   ├── use-cases/                  # UC-* scenario definitions
│   ├── test-cases/                 # TC-* test definitions
│   ├── tutorials/
│   ├── instance-pipeline-parameters.md  # Canonical parameter reference
│   ├── envgene-objects.md          # Object model reference
│   └── envgene-pipelines.md
├── schemas/                        # JSON schemas for pipeline parameters
│   ├── env-inventory-content.schema.json
│   └── resource-profile.schema.json
├── build_envgene/build/
│   ├── requirements.txt            # Production runtime deps
│   └── pip.conf                    # Private registry config (if present)
├── .github/
│   ├── workflows/                  # CI definitions
│   └── actions/run-tests/action.yml  # Composite action for test execution
└── dependencies/
    └── tests_requirements.txt      # Additional test-only deps
```

---

## Documentation & Specifications Analysis

### Core Concepts & Terminology

**Pipeline Parameters** (`docs/instance-pipeline-parameters.md`) — all string type, read from env vars:
- `ENV_NAMES` — `<cluster>/<env>` notation, mandatory
- `ENV_BUILD` — triggers Jinja rendering + YAML beautification
- `GENERATE_EFFECTIVE_SET` — triggers ES computation
- `SD_SOURCE_TYPE` — `artifact` | `json`; `SD_VERSION` = GAV notation (`app:1.0.0`)
- `SD_REPO_MERGE_MODE` — `replace` | `basic-merge` | `extended-merge` | `basic-exclusion-merge`
- `ENV_INVENTORY_CONTENT` — JSON payload for atomic inventory operations (current API)
- `ENV_SPECIFIC_PARAMS` — JSON payload for partial inventory update (deprecated, has `SCHEMAS_DIR` bug)
- `ENV_INVENTORY_INIT` — boolean to create new inventory (deprecated, has Inventory dir creation bug)
- `CRED_ROTATION_PAYLOAD` — triggers credential rotation (mutually exclusive with `GET_PASSPORT`)
- `BG_MANAGE` / `BG_STATE` — blue-green deployment management

**EnvGene Objects** (`docs/envgene-objects.md`):
- Template Repo: `Template Descriptor`, `Tenant/Cloud/Namespace/BG Domain Template`, `ParameterSet`, `AppRegDef`
- Instance Repo: `env_definition.yml` (inventory file), `Credential`, `Secret Store`, `Cloud Passport`, `Solution Descriptor`, `SBOM`

**Effective Set** (`docs/features/effective-set-generation.md`):
- Output location: `environments/<cloud>/<env>/effective-set/{topology,pipeline,deployment,runtime,cleanup}/`
- Contexts `topology` and `pipeline` are always generated
- `deployment`, `runtime`, `cleanup` require a Full SD with application data
- **No-SD Mode**: only `topology` + `pipeline` contexts produced (no SD and no cached Full SD)

**SD Merge Modes** (`docs/features/sd-processing.md`):
- `replace` — discard existing Full SD, use incoming
- `basic-merge` — merge multiple SDs; supports multiple `SD_VERSION` values
- `extended-merge` — deep merge of a single SD delta onto existing Full SD; **does NOT support multiple SD_VERSION** (raises `ValueError`)
- `basic-exclusion-merge` — like basic-merge but removes excluded entries

**Inventory Generation** (`docs/features/env-inventory-generation.md`):
- `ENV_INVENTORY_CONTENT` schema: `{envDefinition: {action, content}, resourceProfiles: [...], paramSets: [...], credentialFiles: [...]}`
- Env scope: per-environment files; cluster scope: per-cluster; site scope: global
- `env_definition.yml` structure: `{inventory: {environmentName, cloudName, clusterUrl}, envTemplate: {name, artifact, additionalTemplateVariables, envSpecificParamsets}}`

### Known Production Bugs (documented via @xfail tests)
1. **`SCHEMAS_DIR` undefined** in `scripts/inventory/env_inventory_generation.py:48` — breaks all `ENV_SPECIFIC_PARAMS` functionality
2. **`jschon_tools.process_json_doc` missing** from installed `jschon-sort` — breaks `ENV_BUILD=true` (YAML beautification step)
3. **`ENV_INVENTORY_INIT` Inventory dir** — `handle_env_inventory_init()` creates `environments/cluster/env/` but not `environments/cluster/env/Inventory/`, so `env_definition.yml` write silently fails

---

## Testing Suite & Strategy

### Framework
- **pytest-bdd** with Gherkin `.feature` files + Python step definitions
- BDD runner entry: `scripts/bdd_runner.py`
- Unit tests in `scripts/tests/` and `python/envgene/envgenehelper/` (plain pytest)

### Structure
```
tests/features/         → .feature files (Gherkin scenarios)
tests/shared_steps/     → reusable @given/@when/@then step implementations
tests/step_defs/        → thin entry modules: import scenarios + steps
tests/framework/        → EnvGeneWorkspace, DataBuilder, BaseWorkspace
tests/conftest.py       → session fixtures: mock_nexus, workspace; @xfail tag handler
```

### Key Fixtures
- **`mock_nexus`** (session-scoped): starts `tests/mock_server.py` on port 8000; pre-populates Maven artifact structure (`.json` index + `.zip` content) for `test-artifact`, `foo`, `project-env-template`, `test_app`, `test_app_2`
- **`workspace`** (function-scoped): creates `EnvGeneWorkspace(tmp_path)` — isolated temp dir with `configuration/`, `environments/`, `sboms/` etc.
- **`EnvGeneWorkspace.run_pipeline()`**: invokes `scripts.pipeline.orchestrator` as subprocess with proper `PYTHONPATH` and `CI_PROJECT_DIR` set to the temp dir

### Test Data
- `test_data/e2e/base/` — minimal environment workspace (no SD, `ENV_BUILD=false` compatible)
- `test_data/e2e/with-sd/` — workspace with pre-existing Full SD for delta tests
- `test_data/golden/` — reference YAML outputs for golden comparison tests

### Tags & Markers
- `@xfail` in Gherkin → mapped by `pytest_bdd_apply_tag` to `pytest.mark.xfail(strict=False)` for known-broken production code
- Steps initialize workspace via `initialize_workspace_with_test_data` which copies `test_data/<path>` into temp dir

### Test Report
`tests/all_tests_report.md` — 307 test cases tracked; statuses: `✅ Active (BDD)`, `❌ Missing`, `⏳ In Progress`

### Mocking Strategy
- **No database mocks** — tests run real pipeline orchestrator subprocess
- **Nexus mocked** at HTTP level via `mock_server.py` (simple Python HTTP server)
- **SOPS mocked** via `sops_mock.bat` / shell script placed on `PATH` in test temp dir
- **Encryption key** set via `SECRET_KEY` env var for Fernet tests

### Naming Conventions
- Feature IDs: `UC-EINV-*` (inventory), `UC-SD-*` (SD), `TC-EIG-*` (env instance gen), `UC-ES-*` (effective set)
- Step def files mirror feature files: `inventory_gen_steps.py` ↔ `environment-inventory-generation.feature`
- Test entry modules: `test_<feature_name>.py` in `step_defs/`

---

## Infrastructure & CI/CD

### GitHub Actions Workflows (`.github/workflows/`)
| Workflow | Trigger | Purpose |
|---|---|---|
| `perform_tests.yml` | PR to any branch | Run full test suite |
| `perform_e2e_tests.yml` | PR | E2E tests |
| `dev-build-docker-images.yml` | Push/PR | Build Docker images for dev |
| `docker_publish_release.yml` | Release | Publish production Docker images |
| `sonar-check.yml` | PR | SonarQube code quality |
| `check-forbidden-words.yml` | PR | Scan for forbidden strings |
| `pr-assigner.yml` | PR | Auto-assign reviewers |

### Test Execution (`action.yml`)
Container: `python:3.12-slim-bookworm`

Steps:
1. Install system deps: `build-essential`, `curl`, SOPS v3.9.0 binary
2. `pip install` from `build_envgene/build/requirements.txt`
3. `./python/build_modules.sh` (internal packages)
4. `pip install -e "python/artifact-searcher[dev]"` + `pip install -e "python/envgene[dev]"`
5. Set `PYTHONPATH=${GITHUB_WORKSPACE}:${GITHUB_WORKSPACE}/scripts`
6. Run tests in 3 separate scopes → merge JUnit XML via `junitparser`

### Test Scopes
```
cd python/envgene/envgenehelper && pytest        → junit_envgenehelper.xml
cd python/artifact-searcher/artifact_searcher && pytest  → junit_artifact_searcher.xml
pytest scripts/tests/                            → junit_scripts.xml
junitparser merge junit_*.xml junit.xml          → combined report
```

### Docker
- `build_envgene/` — Dockerfile + build scripts for envgene runtime image
- `build_pipegene/` — Dockerfile for pipeline runner image
- Images published to registry on release via `docker_publish_release.yml`

---

## Coding Standards & Design Patterns

### Pipeline Architecture
**Chain of Responsibility** — `orchestrator.py` defines `PipelineStep` ABC with `should_run(ctx)` / `execute(ctx)`. Steps executed sequentially; each decides independently whether to run based on `PipelineParametersHandler` context. Steps: `Passport → CredentialRotation → BgManage → InventoryGeneration → SetTemplateVersion → AppregdefRender → ProcessSd → EnvBuild → GenerateEffectiveSet`.

### Python Conventions
- **Type hints required** — `mypy` configured with strict settings in `pyproject.toml` (`disallow_untyped_defs`, `strict_optional`, `warn_return_any`, etc.)
- **Line length**: 120 chars (`tool.black`)
- **Linting**: `ruff==0.11.0`
- **No string normalization** (`skip-string-normalization = true` in black config)
- **Internal packages** use `pydantic` models for data validation
- **`envgenehelper`** is the shared library imported across all scripts

### File/Path Conventions
- Environment path: `environments/<cloud-name>/<env-name>/`
- Inventory file: `environments/<cloud-name>/<env-name>/Inventory/env_definition.yml`
- Effective set: `environments/<cloud-name>/<env-name>/effective-set/<context>/`
- Credentials: `configuration/credentials/<scope>/<name>.yml`
- `CI_PROJECT_DIR` env var points to repository root at runtime

### YAML Handling
- `ruyaml` (ruamel.yaml) used for round-trip YAML editing with comment preservation
- `beautifyYaml` / `sortYaml` post-processing via `jschon-sort` after env build
- Schemas in `schemas/` (JSON Schema draft-07 format)

### Credential Encryption
- Two backends in `python/envgene/envgenehelper/crypt_backends/`: `fernet_handler.py` and `sops_handler.py`
- `SECRET_KEY` env var (base64-encoded 32-byte key) for Fernet
- SOPS used for secrets requiring external KMS

### Plugin Engine
`envgenehelper/plugin_engine/` — loads Python modules from a plugins directory at runtime; used for extensible steps like `get_sboms` in `GenerateEffectiveSetStep`

---

## Local Setup & Development Guide

### Prerequisites
- Python 3.12
- SOPS v3.9.0 (for credential tests): `brew install sops` or download binary
- Git

### Setup (Linux/macOS/WSL)
```bash
# Create and activate virtualenv
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install runtime dependencies
pip install --upgrade pip "setuptools==81" wheel
pip install -r build_envgene/build/requirements.txt

# Build and install internal Python packages
chmod +x python/build_modules.sh && ./python/build_modules.sh
pip install -e "python/artifact-searcher[dev]"
pip install -e "python/envgene[dev]"

# Install test dependencies
pip install -r dependencies/tests_requirements.txt
```

### Environment Variables for Tests
```bash
export PYTHONPATH="$(pwd):$(pwd)/scripts"
export CI_PROJECT_DIR="<path-to-repo>"     # set by EnvGeneWorkspace automatically
export SECRET_KEY="c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="  # test Fernet key
```

### Running Tests
```bash
# Unit tests for envgenehelper
cd python/envgene/envgenehelper && pytest --capture=no -W ignore::DeprecationWarning

# Unit tests for artifact-searcher
cd python/artifact-searcher/artifact_searcher && pytest --capture=no

# Script-scope unit tests
pytest scripts/tests/ --capture=no -W ignore::DeprecationWarning

# BDD integration tests (from repo root with PYTHONPATH set)
pytest tests/ --capture=no -W ignore::DeprecationWarning

# Run single BDD feature
pytest tests/step_defs/test_environment_inventory_generation.py -v

# Show xfail details
pytest tests/ -v --runxfail
```

### Windows-specific Notes
- Use the venv Python explicitly: `.venv/Scripts/python3`
- `shutil.move` must be used instead of `os.system("mv -f")` in `file_helper.py` (see memory note)
- SOPS mock: place `sops.bat` on PATH in test workspace (handled by test framework)

### Key Pipeline Parameters for Manual Testing
```bash
# Minimal inventory-only run (no build)
export ENV_NAMES="my-cluster/my-env"
export ENV_BUILD="false"
export CI_PROJECT_DIR="/path/to/instance-repo"
python -m scripts.pipeline.orchestrator

# Full build with effective set
export ENV_BUILD="true"
export GENERATE_EFFECTIVE_SET="true"
python -m scripts.pipeline.orchestrator
```

### Test Report Maintenance
`tests/all_tests_report.md` tracks implementation status. After adding tests, update the status column:
- `❌ Missing` → `✅ Active (BDD)` for passing tests
- Add `[xfail: <reason>]` annotation for tests blocked by production bugs
