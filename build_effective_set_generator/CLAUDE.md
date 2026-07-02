# build_effective_set_generator — Effective Set Generator Docker Image

Docker image `qubership-effective-set-generator`. Wraps the Java-based Calculator CLI with Python orchestration scripts. Runs the `generate_effective_set` pipeline job.

## Scripts (`scripts/`)

| File | Responsibility |
|------|---------------|
| `effective_set_entrypoint.py` | Main entry point: reads `ES_GENERATION_MODE`, dispatches to `_run_full_generation`, `_run_forward_merge`, or `_run_reverse_merge`; calls Java CLI via `run_effective_set_cli.sh` |
| `crypt_manager.py` | Click CLI: `decrypt_cred_files`, `encrypt_cred_files`, `validate_creds`, `validate_parameters` — used in pipeline jobs before/after ES generation |
| `handle_effective_set_config.py` | Parses `EFFECTIVE_SET_CONFIG` JSON env var; extracts `--effective-set-version`, `--app_chart_validation`, consumer-specific schema paths into extra CLI args |
| `sboms_retention_policy.py` | Applies SBOM retention rules from `config.yml` (`sbom_retention.enabled`, `keep_versions_per_app`); removes legacy files, trims per-app versions, enforces 1200 MB size cap |

## Generation Modes (implemented in `effective_set_entrypoint.py`)

**Full generation** (`_run_full_generation`):
```
delete effective-set/ dir → run Calculator CLI with full sd.yaml
```

**Forward merge** (`_run_forward_merge`, for `basic-merge` / `extended-merge`):
```
read delta_sd.yaml → delete affected per-app dirs from deployment/ and runtime/ →
delete topology/, pipeline/ → run CLI with delta_sd.yaml →
merge new mapping.yaml into existing mapping files (upsert, preserve unchanged namespaces)
```

**Reverse merge** (`_run_reverse_merge`, for `basic-exclusion-merge`):
```
read delta_sd.yaml (apps being removed) + sd.yaml (remaining apps) →
delete per-app dirs for removed apps →
if namespace has no remaining apps in full SD: delete NS dirs + remove from mapping files
(Calculator CLI is NOT called — no new ES output needed)
```

## Java CLI Invocation

`_build_cli_cmd` assembles:
```
/module/scripts/utils/run_effective_set_cli.sh
  --env-id=<FULL_ENV_NAME>
  --envs-path=$CI_PROJECT_DIR/environments
  --output=<effective-set-dir>
  [--sd-path=<sd.yaml>]
  [--registries=$CI_PROJECT_DIR/configuration/registry.yml]
  [--sboms-path=$CI_PROJECT_DIR/sboms]
  [extra args from EFFECTIVE_SET_CONFIG]
  [--extra_params=DEPLOYMENT_SESSION_ID=...]
  [--custom-params=<CUSTOM_PARAMS>]
```

## Tests

```bash
cd build_effective_set_generator/scripts
python -m pytest
```
Test files: `test_effective_set_entrypoint.py`, `test_sboms_retention_policy.py`.
