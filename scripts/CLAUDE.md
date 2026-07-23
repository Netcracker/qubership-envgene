# scripts — Single-Job Pipeline

This branch runs every pipeline job (build, passport, cred rotation, effective set generation, etc.) as **one process**, orchestrated by `pipeline/orchestrator.py::run_unified_pipeline()`. It builds a `PipelineParametersHandler` from env vars, then runs an ordered list of `PipelineStep` objects, each with `should_run(ctx)` / `execute(ctx)`; a step is skipped (logged) if `should_run` returns `False`.

Steps, in order: `PassportStep` → `CredentialRotationStep` → `BgManageStep` → `InventoryGenerationStep` → `SetTemplateVersionStep` → `AppregdefRenderStep` (`ENV_BUILDER` or `GITLAB_DEPLOY`) → `DeployPostfixNamespaceMapStep` (`ENV_BUILDER` or `GITLAB_DEPLOY` — computes `ctx.namespace_by_deploy_postfix`) → `ProcessSdStep` → `GenerateDeploymentPlanStep` (`GITLAB_DEPLOY`) → `EnvBuildStep` → `GenerateEffectiveSetStep` → `GitCommitStep` (`git_commit()` lives in `scripts/git_commit/git_commit.py`, always runs — `git_commit()` itself no-ops when there's nothing to stage).

Both the old (SD-driven) and new (`GITLAB_DEPLOY`) flows converge on the same `dpg`-based `DeployPlanEntity` model: `ProcessSdStep` adapts `sd.yaml`/`delta_sd.yaml` into a `deploy-plan.yml` via `envgenehelper.deploy_plan_adapter.adapt_sd_to_deploy_plan()` (using the namespace map already computed by `DeployPostfixNamespaceMapStep`), while `GenerateDeploymentPlanStep` produces one directly via `dpg`. `deploy-plan.yml` is always written to `Inventory/deploy-plan.yml` and is the sole application-list input to the Java Effective Set CLI (`--deploy-plan-path`) for both flows.

## Directory Map

| Directory | Responsibility |
|-----------|-----------------|
| `pipeline/` | `orchestrator.py` (steps above), `pipeline_parameters.py` (`PipelineParametersHandler.from_env()` — reads/validates all pipeline env vars, writes `envgene-vars.env` dotenv), `pipeline_manager.py` |
| `build_env/` | Environment rendering: `main.py` (`run_build_environment`, `build_environment`, template-override handling), `render_config_env.py` (`EnvGenerator` — Jinja rendering of Cloud/Namespace/composite-structure/external-cred; `generate_namespace_files_and_map()` builds real `namespace.yml` files and the `namespace_by_deploy_postfix` map in the same render pass), `appregdef_render.py` (`run_appregdef_render` — AppDefs/RegDefs only; `write_app_reg_defs`, `override_app_reg_defs`), `namespace_render.py` (`render_namespace_map()` — writes `Inventory/namespace-map.yml`, returns the map used to seed `ctx.namespace_by_deploy_postfix`), `create_credentials.py`, `env_template/` (template resolution, version), `jinja/`, `resource_profiles.py`, `templates/env_config.yml.j2` |
| `cloud_passport/` | `main.py` (`run_cloud_passport` — discovery download via `GitLabClient`; `get_integration_config` reads `configuration/integration.yml`), `cloud_passport.py` (`process_cloud_definition`, `add_cloud_passport_creds`, `mergeDeployParametersFromPassport`), `cmdb.py` |
| `creds_rotation/` | Credential rotation step — see `creds_rotation/CLAUDE.md` |
| `effective_set/` | `effective_set_entrypoint.py` (dispatches full (`_run_deploy_plan_full`) vs. partial (`_run_deploy_plan_partial`, forward-merge only — `REVERSE` partial mode raises `NotImplementedError`) generation off `ctx.deploy_plan.entities`, invokes the Java CLI via `utils/run_effective_set_cli.sh`, then nests `UniqForVersion`/`UniqForRun` output under `<generationId>`), `handle_effective_set_config.py`, `sboms_retention_policy.py` |
| `bg_manage/` | `bg_manage.py` (`run_bg_manage` — Blue-Green state transitions), `filter_namespaces.py` (`apply_ns_build_filter`, `NS_BUILD_FILTER` handling) |
| `inventory/` | `env_inventory_generation.py` (`run_inventory_generation` — generates `Inventory/env_definition.yml` + objects from `ENV_INVENTORY_CONTENT`/`ENV_SPECIFIC_PARAMS`) |
| `sd/` | `process_sd.py` (`handle_sd` — Solution Descriptor download/merge: `basic-merge`/`extended-merge`/`basic-exclusion-merge`/`replace`) |
| `deployment_plan/` | `generate_deployment_plan.py` (`run_generate_deployment_plan` — DPG calculate/map for `GITLAB_DEPLOY`, sets `ctx.deploy_plan`). The `DeployPlanEntity`/`EnvgeneDeployPlan` model and `adapt_sd_to_deploy_plan()` (SD→deploy-plan conversion for the old flow) live in `modules/envgene/envgenehelper/deploy_plan_adapter.py`, shared by both flows |
| `build_template/` | Static scaffold resources (`template/artifact_definition.yml`, `build.sh`, `description.yaml`) for new template-repository artifacts — not orchestrator code |
| `utils/` | `crypt_manager.py` (Click CLI: `decrypt_cred_files`, `encrypt_cred_files`, `validate_creds`, `validate_parameters`), `schema_validation.py` (`checkEnvSpecificParametersBySchema`, `checkCloudPassportBySchema`), `sparse_checkout.py` (CLI wrapper over `envgenehelper.git_helper.GitRepoManager.sparse_checkout`), `run_effective_set_cli.sh` (invokes the Java Calculator CLI — see `build_effective_set_generator/CLAUDE.md`), `handle_certs.sh`, `update_ca_cert.sh` |
| `tests/` | Pytest suites, one subdir per area: `app_reg_defs/`, `bg_manage/`, `creds_rotation/`, `deployment_plan/`, `effective_set/`, `env-build/`, `env-template/`, `env_inventory_generation/`, `git_commit/`, `pipeline/`, `sd/` |

## Imports

Code under `scripts/` uses **bare, top-level-relative imports** (`from build_env.appregdef_render import ...`, `from creds_rotation.creds_rotation_handler import run_cred_rotation`), not `scripts.build_env...`. This only resolves correctly when `scripts/` itself is on `PYTHONPATH` (alongside the repository root, for `envgenehelper`) — see the Dockerfile's `PYTHONPATH='/module/scripts'` and CI's `PYTHONPATH=$GITHUB_WORKSPACE:$GITHUB_WORKSPACE/scripts`.

## Tests

```bash
PYTHONPATH=".:./scripts" python -m pytest scripts/tests/
```

`scripts/tests/conftest.py` overrides `business_helper.get_schema_dir` to point at the repository's `schemas/` directory.

## Key: `utils/run_effective_set_cli.sh`

Bridge between the Python orchestration layer and the Java Calculator CLI. Its arguments are assembled by `effective_set/effective_set_entrypoint.py::_build_cli_cmd()`. Notable flags:

- `--env-id` — `FULL_ENV_NAME` (`<cluster>/<env>`)
- `--envs-path` — `$CI_PROJECT_DIR/environments`
- `--output` — path to write the ES
- `--deploy-plan-path` — path to `Inventory/deploy-plan.yml`; the sole application-list source for both the old (SD-driven) and `GITLAB_DEPLOY` flows (`--sd-path` was removed — the Java CLI no longer reads `sd.yaml` directly)
- `--registries` — path to `configuration/registry.yml`
- `--sboms-path` — path to `sboms/` directory
- `--effective-set-version` — from `EFFECTIVE_SET_CONFIG`
- `--custom-params` — from `CUSTOM_PARAMS` pipeline variable
