# EnvGene — Repository Overview

EnvGene is a git-native tool that generates and versions cloud environment configurations from Jinja2 templates. It bridges a **Template Repository** (Jinja templates) and an **Instance Repository** (per-environment generated YAML + credentials) to produce an **Effective Set** consumed by ArgoCD/deployers.

## Module Map

This branch runs all pipeline jobs as **one consolidated job** (`scripts/pipeline/orchestrator.py::run_unified_pipeline`), not as separate per-job Docker images/scripts. Most job logic lives under `scripts/`.

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Single-job pipeline: `pipeline/` (orchestrator + params), `build_env/`, `cloud_passport/`, `creds_rotation/`, `effective_set/`, `bg_manage/`, `inventory/`, `sd/`, `build_template/`, `utils/`, `tests/` |
| `python/envgene/` | `envgenehelper` pip package — core Python library shared by all modules |
| `python/artifact-searcher/` | Async Maven artifact URL resolver (multi-cloud auth) |
| `build_effective_set_generator/` | Java/Maven multi-module project (Quarkus CLI) — the Effective Set generator engine, invoked from `scripts/effective_set/` via `scripts/utils/run_effective_set_cli.sh` |
| `build_envgene/` | Docker image + scripts for `git_commit` (Python, `git_commit.py`) and credential diff minimization |
| `schemas/` | JSON schemas for all EnvGene objects (validated at runtime) |
| `docs/` | Comprehensive documentation — start with `docs/envgene-objects.md` and `docs/envgene-configs.md` |

**Removed from `main` in this branch** (no directory exists here for these; superseded by the single-job consolidation): the standalone `base_modules/`, top-level `creds_rotation/`, and `python/integration/` modules were dissolved into `envgenehelper`/`scripts/utils/`/`scripts/cloud_passport/` (credential rotation moved to `scripts/creds_rotation/` — see `scripts/CLAUDE.md`); `python/jschon-sort/` is now an external pip dependency (`jschon-tools`), not local source (see `python/envgene/CLAUDE.md`).

## Core Concepts

- **Template Repository** → Jinja2 templates for Tenant/Cloud/Namespace/Application objects, ParameterSets, ResourceProfiles, Registry/Application Definitions.
- **Instance Repository** → `environments/<cluster>/<env>/` tree: `Inventory/env_definition.yml`, `Namespaces/`, `Credentials/credentials.yml`, `Inventory/solution-descriptor/sd.yaml`.
- **Effective Set** → `effective-set/{topology,pipeline,deployment,runtime,cleanup}/` — final YAML for deployers.
- **Solution Descriptor (SD)** — list of `application:version` + `deployPostfix` entries driving ES generation. Merge modes: `basic-merge`, `extended-merge`, `basic-exclusion-merge`, `replace`.

## Key Environment Variables (runtime)

- `CI_PROJECT_DIR` — root of the instance repository
- `FULL_ENV_NAME` — `<cluster>/<env-name>`; `CLUSTER_NAME` and `ENVIRONMENT_NAME` are its split parts
- `SECRET_KEY` — Fernet encryption key; `ENVGENE_AGE_PRIVATE_KEY` / `PUBLIC_AGE_KEYS` for SOPS/AGE
- `SD_DATA` / `SD_VERSION` / `SD_REPO_MERGE_MODE` — Solution Descriptor inputs
- `EFFECTIVE_SET_CONFIG` — JSON config for the ES generator
- `ENV_NAMES` — multi-value `<cluster>/<env>` list for batch operations
- `ENVGENE_LOG_LEVEL` — logging verbosity

## Credentials

All credential files (matching `*credentials*.yml`, `*creds*.yml` in `Credentials/` or `configuration/`) are encrypted at rest. Encryption backend is configured in `configuration/config.yml` (`crypt_backend: Fernet | SOPS`). The `type` field is never encrypted.

## Tests

Each Python sub-package has its own pytest suite. Run from its directory:

```bash
cd python/envgene && python -m pytest
cd build_envgene/scripts && python -m pytest
```

The single-job pipeline scripts under `scripts/` are tested from the repository root with `scripts/` on `PYTHONPATH` (matches CI's `PYTHONPATH=$GITHUB_WORKSPACE:$GITHUB_WORKSPACE/scripts`; see `scripts/CLAUDE.md`):

```bash
PYTHONPATH=".:./scripts" python -m pytest scripts/tests/
```

The Effective Set generator is a Maven project; from `build_effective_set_generator/`:

```bash
./mvnw test
```

### BDD End-to-End Tests

Cucumber BDD tests are located in the `cucumber_tests/` directory. These tests run the full pipeline orchestrated via Docker or a local Python environment.

To run them, navigate to the `cucumber_tests` directory and use one of the wrappers:
```bash
cd cucumber_tests
./run_bdd_tests.sh
```
Or on Windows:
```powershell
cd cucumber_tests
.\run_bdd_tests.ps1
```
