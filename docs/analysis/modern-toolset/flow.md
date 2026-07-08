# Modern toolset flow

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. `run_cloud_passport` (берет паспорт из даунстри джобы и декриптит) уже в `env_prepare`?
2. `generate_deployment_plan`, `argocd_repo_generator`, `es-pusher`, `git_commit` лягут под `orchestrator.py`?

## AI

1. Agree with Kristina DD and zip layout
2. Agree with Lenya on using the dynamic pipeline
3. Agree with Lenya/Tema on the `process_dp` function
4. Discuss with Tema encrypting ARGO_DPG_CONTEXT.env via crypt, not DPG
5. [phase2] Consider create_if_not_exist | replace strategies for appregdef processing
6. [phase2] Design integration with the central appregdef storage
7. [phase2] Design SAVE_ARTIFACTS_STRATEGY
    1. save env_instance/ES/sd.yaml to a job artifact on SAVE_ALL
8. Design `git_commit`
    1. Depending on `PIPELINE_TYPE` and `SAVE_ARTIFACTS_STRATEGY`, commit env_instance/ES/sd.yaml or not
9. [after the flow is finalized] analyze the flow for file-read optimization
    (remove redundant reads/writes, cache within one process)

## Data exchange Rules

1. Within `orchestrator.py`, steps exchange:
   - structured data via the in-memory context `ctx.*`
   - scalars via the in-memory parameters handler `PipelineParametersHandler`
2. Crossing a separate job (`cmdb_import`, `sync`), exchange on disk:
   - structured data via files (job artifacts)
   - scalars via `build.env`
3. Crossing a following function in the same job:
   - `generate_deployment_plan`
   - `argocd_repo_generator`
   - `es-pusher`
   - effective-set calculator
   exchange:
   - structured data via contracted files
   - scalars via command parameters

## Artifacts

Producers and consumers are Target Flow step numbers. Low numbers `3` and `4` in the consumers column are the
deploy-stage jobs `cmdb_import` and `sync`, not sub-steps.

| Artifact                  | Path                                                                          | Producers      | Consumers              |
|---------------------------|-------------------------------------------------------------------------------|----------------|------------------------|
| env_definition            | `${CI_PROJECT_DIR}/environments/<cluster>/<env>/Inventory/env_definition.yml` | 7, 10, 22      | 9, 10, 11, 12, 22      |
| cloud passport            | `${CI_PROJECT_DIR}/environments/<cluster>/cloud-passport/`                    | 8              | 11, 22                 |
| artdef                    | `${CI_PROJECT_DIR}/configuration/artifact_definitions/`                       | 9              | 10                     |
| downloaded template files | `${CI_PROJECT_DIR}/tmp/` (common), `tmp/origin/`, `tmp/peer/`                 | 10             | 12, 13, 14, 16, 18, 22 |
| namespace-map.yml         | `${CI_PROJECT_DIR}/tmp/render-context/namespace-map.yml`                      | 15             | 20, 21, 22, external   |
| env instance              | `${CI_PROJECT_DIR}/environments/<cluster>/<env>/`                             | 13, 14, 16, 22 | 18, 26, 29, 3          |
| appreg defs               | env instance appregdef files                                                  | 18             | 19, 20, 23, 24         |
| sd.yaml                   | Inventory/solution-descriptor/sd.yaml                                         | 19             | 19, 21, 23, 26         |
| delta_sd.yaml             | Inventory/solution-descriptor/delta_sd.yaml                                   | 19             | 26                     |
| deploy-plan.yml           | deploy-plan.yml                                                               | 20             | 21, 23, 26, 27         |
| DD and zip                | `${APP_ARTIFACTS_DIR}`                                                        | 23             | 24, 27                 |
| sboms                     | sboms/                                                                        | 24             | 26, committed          |
| effective set             | `${CI_PROJECT_DIR}/environments/<cluster>/<env>/effective-set/`               | 26             | 27, 30                 |
| appset/app CR             | TBD                                                                           | 27             | 30                     |
| build.env                 | `${CI_PROJECT_DIR}/build.env`                                                 | 1              | 20, 27, 30, 3, 4       |
| ARGO_DPG_CONTEXT.env      | TBD                                                                           | 27             | 4                      |
| system config             | TBD                                                                           | TBD            | 9, 18                  |

## Defaults

1. APP_ARTIFACTS_DIR: `${CI_PROJECT_DIR}/tmp/app-artifacts/`

## DD and zip layout

`dd_downloading` stores artifacts at `APP_ARTIFACTS_DIR`:

```text
${APP_ARTIFACTS_DIR}/
  app-1/
    version-1/
      app-1-version-1.json       # DD
      app-1-version-1.zip        # downloaded zip artifact
      app-1/                     # unzipped content
  app-2/
    version-2/
      app-2-version-2.json
      app-2-version-2.zip
      app-2/
```

- `APP_ARTIFACTS_DIR` is defaulted by `set_defaults` (step 1) to `${CI_PROJECT_DIR}/tmp/app-artifacts/` and
  written to `build.env`.
- The `<version>` folder is the raw app version. Snapshot normalization (`...-timestamp` to `-SNAPSHOT`) applies
  only to the remote maven URL, not the local folder.
- The DD and zip filenames are the basename of the remote artifact URL (`<artifact_id>-<version>.json`/`.zip`).
- The folder under `<version>` is the maven `artifact_id` (unzipped content), which often equals the app name.

## `deploy-plan.yml`

```yaml
- version: app-1:version-1
  deployPostfix: core
  namespace: ''
  wave: 0
- version: app-2:version-2
  deployPostfix: core
  namespace: ''
  wave: 1
```

## `namespace-map.yml`

TBD

## `ctx.current_env`

TBD

## build.env

TBD

## APPLICATION_VERSIONS

TBD

## Multi env support

- Single `ENV_NAMES` -> direct include `static-api.yaml`, multiple -> run generator.
- OOB launches `static-api.yaml` directly.
- Thin generator: per env emit `trigger: include static-api.yaml`, forward vars, set `ENV_NAMES=<cluster>/<env>`.
- Keep `orchestrator.py` single-env, unchanged.
- Passport jobs per env flow. no aggregation.

`gitlab-ci.yaml`:

```yaml
## --- single env: static-api directly ---
include:
  - local: static-api.yaml
    rules:
      - if: '$ENV_NAMES !~ /[,; \n]/'        # no delimiter -> one env (empty -> CLUSTER/ENV fallback)

## --- multi env: generation ---
generate_pipeline:
  ...
    script:
      - "python /module/scripts/main.py generate_pipeline"
    rules:
      - if: '$ENV_NAMES =~ /[,; \n]/'          # has a delimiter -> N envs
  ...
run_generated_pipeline:
  ...
  trigger:
    include:
      - artifact: generated-config.yml
        job: generate_pipeline
  rules:
    - if: '$ENV_NAMES =~ /[,; \n]/'
  ...
```

Generated `generated-config.yml`:

```yaml
env-prepare-cluster-01-env-1:
  trigger:
    include:
      - local: static-api.yaml
    ...
  variables:
    ENV_NAMES: "cluster-01/env-1"
  ...

env-prepare-cluster-01-env-2:
  trigger:
    include:
      - local: static-api.yaml
    ...
  variables:
    ENV_NAMES: "cluster-01/env-2"
  ...
```

AI:

- Write a new `/module/scripts/main.py generate_pipeline` on the `build_pipegene` image (or the common `envgene` one)
- Prepare `gitlab_ci.yaml`
- Add a passport generation job for the per-env flow
- Verify `orchestrator.py` needs no changes
- Verify `static-api.yaml` needs no changes
- Verify `$ENV_NAMES =~ /[,; \n]/` works correctly
- Test parallel commits
- Update the gsf package
- Update the gsf-related documentation
- Do the same on GitHub

## To deprecate

1. Fernet
2. GAV notation
3. темплейт теститнг

## Target Flow

1. job `trigger_passport`
   - trigger:
     - `GET_PASSPORT: true`
   - input:
     - `integration.yaml`
     - `ENV_NAMES`
   - output:
     - triggered downstream pipeline
   - actions:
     - trigger discovery repository pipeline
   - AI[phase1]: unchanged
   - AI[phase2]: add `trigger_passport` to `static-api.yaml`
2. job `env_prepare`
   1. `set_defaults`
       - trigger:
         - always
       - inputs:
         - none
       - output:
         - `build.env`
         - env variables
       - actions:
         - set defaults
       - AI[phase1]: add `APP_ARTIFACTS_DIR`
       - AI[phase2]: remove non required `build.env` vars
   2. `cert_apply`
       - unchanged
       - AI[phase2]: move out of the before script
       - AI[phase2]: implement [#1506](https://github.com/Netcracker/qubership-envgene/issues/1506)
   3. `git_fetch`
       - [phase1] unchanged
   4. `crypt` to decrypt
       - [phase1] unchanged
   5. `credential_rotation`
       - [phase1] unchanged
       - AI[phase2]: check UC readiness and test coverage
   6. `bg_manage`
       - [phase1] unchanged
       - AI[phase2]: check UC readiness and test coverage
   7. `env_inventory_generation`
       - output:
         - env_definition
       - [phase1] unchanged
       - AI[phase2]: check UC readiness and test coverage
   8. `run_cloud_passport`
       - trigger:
         - `GET_PASSPORT: true`
       - input:
         - `integration.yaml`
         - cloud passport in `trigger_passport` downstream pipeline
       - output:
         - cloud passport
       - actions:
         - find the downstream discovery pipeline via bridges, download its artifacts
         - Fernet-decrypt or re-encrypt
       - [phase1] unchanged
   9. `registry_discovery`
       - trigger:
         - always
       - input:
         - system config
         - env_definition
       - output:
         - artdef
       - actions:
         - generate artdef base from CMDB/central appreg storage
       - remove or extend (add integration with the central appregdef storage)?
       - AI[phase1]: keep it off
       - AI[phase2]: turn on (?)
       - AI[phase3]: add integration with central appregdef storage
   10. `process_env_template` (`.set_version` -> `.download`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - `ENV_TEMPLATE_VERSION`
         - `ENV_TEMPLATE_VERSION_PEER`
         - `ENV_TEMPLATE_VERSION_ORIGIN`
         - `ENV_TEMPLATE_VERSION_UPDATE_MODE`
         - env definition
         - artifact definition
       - output:
         - downloaded template files
         - updated env_definition
       - actions:
         - validate env definition, artifact definition
         - set template version
         - download env template
       - [phase1]: unchanged
       - AI[phase1]: fix the template-version-setting bug
   11. `env_build.compute_template_macros` (ex `render_config_env.generate_config`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - env_definition
         - cloud passport
         - deployer config
       - output:
         - `ctx.` with `current_env.*` macros: `name`, `environmentName`, `tenant`,
           `cloud`, `cloudNameWithCluster`, `cmdb_name`, `cmdb_url`, `description`, `owners`, `env_template`,
           `additionalTemplateVariables`, `cluster.*`, `cloud_passport`. `solution_structure` initialized to {}
       - actions:
         - generates the macro values above
       - AI[phase2]: rename `generate_config` -> `compute_template_macros`
   12. `env_build.load_template_descriptor` (ex `render_config_env.set_env_templates`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - env_definition
         - downloaded template files
         - `ctx.current_env`
       - output:
         - `ctx.current_env_template` for common/peer/origin
       - actions:
         - render the template descriptor if .j2, validate
         - load into `current_env_template`
         - repeat for the peer/origin dirs
       - AI[phase2]: rename `set_env_templates` -> `load_template_descriptor`
   13. `env_build.render_bgd` (ex `render_config_env.generate_bgd_file`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - downloaded template files
         - `ctx.current_env`
         - `ctx.current_env_template`
       - output:
         - rendered bg domain into env instance
       - actions:
         - renders the bg domain into the env instance
         - no-op if no bg domain
       - AI[phase2]: rename `generate_bgd_file` -> `render_bgd`
   14. `env_build.render_namespaces` (ex `render_config_env.generate_namespace_files`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - downloaded template files
         - `ctx.current_env`
         - `ctx.current_env_template`
       - output:
         - rendered namespaces into env instance
       - actions:
         - render all namespaces into env instance
       - AI[phase2]: rename `generate_namespace_files` -> `render_namespaces`
   15. `env_build.compute_namespace_map`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - `FULL_ENV_NAME`
         - rendered namespace in env instance
         - rendered bg domain in env instance
       - output:
         - `namespace-map.yml`
       - actions:
         - read rendered namespace name + deployPostfix for each env namespace
         - calculate deployPostfix to namespace mapping (incl. BG suffix)
       - AI[phase1]: create the function
   16. `env_build.render_composite_structure` (ex `render_config_env.generate_composite_structure`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - downloaded template files
         - `ctx.current_env`
         - `ctx.current_env_template`
       - output:
         - rendered composite structure into env instance
       - actions:
         - render the composite structure template, validate (no-op if none)
       - AI[phase2]: rename `generate_composite_structure` -> `render_composite_structure`
   17. `env_build.compute_composite_topology`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - rendered composite structure into env instance
         - rendered bg domain into env instance
         - rendered namespace objects into env instance
       - output:
         - `ctx.current_env.composite_topology`
       - actions:
         - resolve baseline + satellites, each member resolves its namespace template to the rendered namespace name
       - AI[phase2]: adopt the macro computation from master
   18. `app_reg_def_process` (ex `run_appregdef_render`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - downloaded template files
         - env instance
         - system config
         - `APPREG_DEF_STRATEGY`
       - output:
         - appreg defs
       - actions:
         - render appreg defs, validate
         - skip appregdefs already present in env instance if `APPREG_DEF_STRATEGY` == `create_if_not_exist`
           (default). do not skip if `APPREG_DEF_STRATEGY` == `replace`
       - phase1: unchanged
       - AI[phase2]: renders only required appregdef
       - AI[phase2]: implement create_if_not_exist | replace strategies
       - AI[phase2]: rename `run_appregdef_render` -> `app_reg_def_process`
   19. `process_sd` (ex `handle_sd`)
       - trigger:
         - (`SD_VERSION` or `SD_DATA`) and `PIPELINE_TYPE` !== `GITLAB_DEPLOY`
       - inputs:
         - `SD_VERSION`
         - `SD_DATA`
         - `SD_SOURCE_TYPE`
         - `SD_REPO_MERGE_MODE`
         - sd.yaml
         - appreg defs
       - outputs:
         - updated sd.yaml
         - delta_sd.yaml
       - actions:
         - merge sd
       - phase1: unchanged
       - AI[phase1]: not called in the new flow, called in the old flow
       - AI[phase2]: remove `SD_SOURCE_TYPE`
       - AI[phase2]: rename `handle_sd` -> `process_sd`
   20. `generate_deployment_plan`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY`
       - input:
         - `APPLICATION_VERSION`
         - params.environment_id -> `build.env.FULL_ENV_NAME`
         - appreg defs
         - namespace_map (`namespace-map.yml`)
         - filters:
           - `DEPLOY_POSTFIXES_FILTER`
           - `NAMESPACE_NAMES_FILTER`
           - `COMPONENT_NAMES_FILTER`
           - `WAVE_NAMES_FILTER`
       - output:
         - `deploy-plan.yml`
       - actions:
         - process `APPLICATION_VERSION` (download SD, merge)
         - filter DP
         - enrich DP
       - AI[phase1]: not called in the old flow, called in the new flow
       - AI[phase1]: create the function
       - AI[phase2]: move to GitHub
   21. `env_build.compute_solution_structure` (ex `generate_solution_structure`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - `sd.yaml` or `deploy-plan.yml`
         - `namespace-map.yml`
       - output:
         - `ctx.current_env.solution_structure`
       - actions:
         - join applications by deployPostfix with namespace_map
         - no-op if no `sd.yaml` or `deploy-plan.yml`
       - AI[phase1]: support DP as well as SD
   22. `env_build` (ex `run_build_environment`) (`.render_tenant` -> `.render_cloud` -> `process_cloud_passport`
       -> `.create_external_credentials` -> `.render_paramsets` -> `.create_credentials` -> `apply_ns_build_filter`)
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `ENV_BUILDER: true`
       - input:
         - downloaded template files
         - env_definition
         - `ctx.current_env`
         - `ctx.current_env_template`
         - `namespace-map.yml`
         - `ctx.current_env.composite_topology`
         - `ctx.current_env.solution_structure`
         - cloud passport
       - output:
         - fully rendered env instance
         - updated env_definition
       - actions:
       - renders remain env instance:
         - `.render_tenant` (ex `generate_tenant_file`)
         - `.render_cloud` (ex `generate_cloud_file`)
         - `process_cloud_passport`: merge cloud_passport into the rendered `cloud.yml`
         - `.create_external_credentials`
         - `.render_paramsets` (ex `generate_paramset_templates`)
         - `.create_credentials`
       - `apply_ns_build_filter`
         - prefer to keep as is
       - phase1: unchanged
       - AI[phase1]: test manually
       - AI[phase2]: prepare a UC, add tests
       - AI[phase2]: rename render_config_env `generate_*` methods to `env_build.render_*`
   23. `dd_downloading`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - appreg defs
         - `sd.yaml` or `deploy-plan.yml`
         - `APP_ARTIFACTS_DIR`
       - output:
         - DD and zip at `${APP_ARTIFACTS_DIR}`
       - actions:
         - resolve DD + zip per app with appreg defs
         - download DD + zip, unzip
       - AI[phase1]: extract from sbom_generator
       - AI[phase1]: add `APP_ARTIFACTS_DIR`
       - AI[phase1]: support DP as well as SD
   24. `sbom_generation`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - local DD + zip
         - appreg defs
         - `APP_ARTIFACTS_DIR`
       - output:
         - sboms
       - actions:
         - generate SBOM from local DD + zip
         - sbom retention
       - AI[phase1]: consume local DD + zip. download moved to `dd_downloading`
   25. `null_validation`
       - AI[phase1]: check what exists
   26. ES Calc CLI
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - env instance
         - `sd.yaml` or `deploy-plan.yml`
         - sboms
       - output:
         - Effective Set
       - actions:
         - generates ES
       - AI[phase1]: support DP as well as SD
   27. `argocd_repo_generator`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY`
       - input:
         - `deploy-plan.yml`
         - effective set
         - local DD (from dd_downloading)
         - `APP_ARTIFACTS_DIR`
         - params.environment_id -> `build.env.FULL_ENV_NAME`
         - TBD
       - output:
         - appset CR, app CR, TBD
         - dotenv ARGO_DPG_CONTEXT.env
       - actions:
         - TBD
       - AI[Tema]: remove DP generation
       - AI[Tema]: add local DD
       - AI[Tema]: encrypt ARGO_DPG_CONTEXT.env
       - AI[phase2]: move to GitHub or not?
         - or will `crypt` do it?
         - or merge build.env?
   28. `crypt` to encrypt
   29. `git_commit`
       - input:
         - `CLUSTER_NAME`
         - `ENVIRONMENT_NAME`
       - AI[phase1]: depending on `PIPELINE_TYPE`, commit env_instance/ES/sd.yaml or not
       - AI[phase2]: depending on `SAVE_ARTIFACTS_STRATEGY`, save env_instance/ES/sd.yaml to artifacts or not
       - AI[phase2]: unify with `es-pusher`
   30. `es-pusher`
       - trigger:
         - `PIPELINE_TYPE: GITLAB_DEPLOY`
       - input:
         - instance files
           - effective set
           - appset
         - `DCL_GIT_URL`
         - `DCL_GIT_BRANCH` defaults on the orchestrator side
         - `DCL_CONFIG_GITLAB_USER`
         - `DCL_CONFIG_GITLAB_TOKEN`
         - `GITLAB_USER_NAME`
         - `GITLAB_USER_EMAIL`
         - COMMIT_FILTER
         - params.environment_id -> `build.env.FULL_ENV_NAME`
         - params.commit_message -> `DEPLOYMENT_TICKET_ID`
         - params.rootdir -> x
         - path filter
       - output:
         - instance repo commit
       - actions:
         - push effective set and appsets to the deploy target repo
       - AI[phase1]: move to GitHub
       - AI[phase2]: unify with `git_commit`
   31. cleanup of leftovers (?)
   32. create the dotenv report (?)
3. job `cmdb_import`
   - input:
     - `build.env.FULL_ENV_NAME`
   - AI[phase1]: not called in the new flow, called in the old flow
4. job `sync`
   - trigger:
     - `PIPELINE_TYPE: GITLAB_DEPLOY`
   - input:
     - `ARGO_DPG_CONTEXT.env`
     - `build.env.FULL_ENV_NAME`
   - output:
     - TBD
   - actions:
     - TBD
   - AI[phase1]: not called in the old flow, called in the new flow
   - AI[phase2]: move to GitHub

## AI diff (since 62e1d91f, 2026-07-07)

Inline `AI[...]` changes, notation `[<step> <name>] AI[<phase>]: <text>`.

### Added

```text
[1 trigger_passport]            AI[phase1]: unchanged (new step)
[1 trigger_passport]            AI[phase2]: add trigger_passport to static-api.yaml
[1 set_defaults]                AI[phase1]: add APP_ARTIFACTS_DIR
[1 set_defaults]                AI[phase2]: remove non required build.env vars
[2 cert_apply]                  AI[phase2]: implement #1506
[11 compute_template_macros]    AI[phase2]: rename generate_config -> compute_template_macros
[12 load_template_descriptor]   AI[phase2]: rename set_env_templates -> load_template_descriptor
[13 render_bgd]                 AI[phase2]: rename generate_bgd_file -> render_bgd
[14 render_namespaces]          AI[phase2]: rename generate_namespace_files -> render_namespaces
[16 render_composite_structure] AI[phase2]: rename generate_composite_structure -> render_composite_structure
[18 app_reg_def_process]        AI[phase2]: rename run_appregdef_render -> app_reg_def_process
[19 process_sd]                 AI[phase2]: rename handle_sd -> process_sd
[22 env_build]                  AI[phase2]: rename generate_* -> env_build.render_*
[20 generate_deployment_plan]   AI[phase1,Tema]: change input for enrich from ES to namespace_map
[23 dd_downloading]             AI[phase1]: add APP_ARTIFACTS_DIR
[30 es-pusher]                  AI[phase3]: unify with git_commit
```

### Removed

```text
[20 dp_sd_adapter]  AI[phase1]: create the function to simplify migration (step dp_sd_adapter removed)
[20 dp_sd_adapter]  AI[phase2]: remove the function
[2 get_passport]    AI[phase1]: test manually            (moved to [22 env_build])
[2 get_passport]    AI[phase2]: prepare a UC, add tests  (moved to [22 env_build])
```

### Changed

```text
[17 compute_composite_topology] adopt the macro computation from master   phase2 -> phase1.5
[21 compute_solution_structure] support DP as well as SD                  phase2 -> phase1
[23 dd_downloading]             support DP as well as SD                  phase2 -> phase1
[26 ES Calc CLI]                support DP as well as SD                  phase2 -> phase1
[20 generate_deployment_plan]   move to GitHub                            phase1 -> phase2
[27 argocd_repo_generator]      move to GitHub -> move to GitHub or not?  (became a question)
[23 dd_downloading]             separate from sbom generation -> extract from sbom_generator
[24 sbom_generation]            support local DD and zip -> consume local DD + zip
```
