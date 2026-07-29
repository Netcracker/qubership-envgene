# EnvGene — Repository Overview

EnvGene is a git-native tool that generates and versions cloud environment configurations from Jinja2 templates. It bridges a **Template Repository** (Jinja templates) and an **Instance Repository** (per-environment generated YAML + credentials) to produce an **Effective Set** consumed by ArgoCD/deployers.

## Module Map

This branch runs all pipeline jobs as **one consolidated job** (`scripts/pipeline/orchestrator.py::dispatch`), not as separate per-job Docker images/scripts. `dispatch()` runs `run_single_env_pipeline()` for one `ENV_NAMES` value, or fans out to parallel child processes via `multi_env_runner.fan_out()` when `ENV_NAMES` lists multiple environments. Most job logic lives under `scripts/`.

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Single-job pipeline: `pipeline/` (orchestrator + params), `build_env/`, `cloud_passport/`, `creds_rotation/`, `effective_set/`, `bg_manage/`, `inventory/`, `sd/`, `build_template/`, `utils/`, `tests/`, `git_commit/` (`git_commit.py`, `minimize_cred_diffs.py`); also `report.py` (moved here from `build_envgene/scripts/`) |
| `modules/envgene/` | `envgenehelper` pip package — core Python library shared by all modules |
| `modules/artifact-searcher/` | `artifact_searcher` pip package — async Maven artifact URL resolver (multi-cloud auth) |
| `modules/external-cred-provision/` | `external-cred-provision` pip package — provisions external credentials into secret stores; `src`-layout, console script `external-cred-provision` |
| `build_effective_set_generator/` | Java/Maven multi-module project (Quarkus CLI) — the Effective Set generator engine, invoked from `scripts/effective_set/` via `scripts/utils/run_effective_set_cli.sh` |
| `build_envgene/` | Docker image build context (`build_envgene/build/Dockerfile`) — no longer holds Python scripts, see `scripts/` above |
| `schemas/` | JSON schemas for all EnvGene objects (validated at runtime) |
| `docs/` | Comprehensive documentation — start with `docs/envgene-objects.md` and `docs/envgene-configs.md` |

**Removed from `main` in this branch** (no directory exists here for these; superseded by the single-job consolidation): the standalone `base_modules/`, top-level `creds_rotation/`, and `python/integration/` modules were dissolved into `envgenehelper`/`scripts/utils/`/`scripts/cloud_passport/` (credential rotation moved to `scripts/creds_rotation/` — see `scripts/CLAUDE.md`); `python/jschon-sort/` is now an external pip dependency (`jschon-tools`), not local source (see `modules/envgene/CLAUDE.md`). `python/` (main's name for the directory below) was renamed to `modules/` in this branch — same pip packages as before, just a clearer top-level name.

## Python module layout

`modules/envgene`, `modules/artifact-searcher`, `modules/external-cred-provision` are ordinary pip packages (`pyproject.toml` + `[build-system]`), installed editable (`pip install -e`) in dev/CI and plain (`pip install`) in the Docker image — see each `pyproject.toml`'s `[project] version`, which is a required-by-setuptools formality, not a tracked release version. None of them are ever published anywhere (no PyPI, no internal registry) — `pip install -e`/`pip install <dir>` only registers the package into the local `site-packages`, nothing leaves the machine. `scripts/` itself is not a package; it's resolved purely via `PYTHONPATH` (see `scripts/CLAUDE.md`). Directory-vs-package-name note: `modules/envgene` contains package `envgenehelper`; `modules/artifact-searcher` contains package `artifact_searcher`; `modules/external-cred-provision/src` contains package `external_cred_provision`.

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

Each Python module has its own pytest suite, installed editable first (`pip install -e "modules/envgene[dev]"`, etc. — see `.github/actions/run-tests/action.yml`), then run from its own directory:

```bash
pip install -e "modules/envgene[dev]"
pip install -e "modules/artifact-searcher[dev]"
pip install -e "modules/external-cred-provision"
cd modules/envgene/envgenehelper && python -m pytest
cd modules/artifact-searcher/artifact_searcher && python -m pytest
cd modules/external-cred-provision && python -m pytest
```

The single-job pipeline scripts under `scripts/` (including `git_commit.py`/`minimize_cred_diffs.py`/`report.py`, formerly under `build_envgene/scripts/`) are tested from the repository root the same way:

```bash
PYTHONPATH=".:./scripts" python -m pytest scripts/tests/
```

The Effective Set generator is a Maven project; from `build_effective_set_generator/`:

```bash
./mvnw test
```
