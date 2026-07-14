# Modern toolset flow

- [Modern toolset flow](#modern-toolset-flow)
  - [OQ](#oq)
  - [AI](#ai)
  - [Data exchange Rules](#data-exchange-rules)
  - [Defaults](#defaults)
  - [DD and zip layout](#dd-and-zip-layout)
  - [`deploy-plan.yml`](#deploy-planyml)
  - [`namespace-map.yml`](#namespace-mapyml)
  - [`ctx.current_env`](#ctxcurrent_env)
  - [build.env](#buildenv)
  - [APPLICATION\_VERSIONS](#application_versions)
  - [Locations](#locations)
  - [Uniq names](#uniq-names)
    - [`generate_deployment_plan`](#generate_deployment_plan)
    - [ES Calc](#es-calc)
  - [Multi env support](#multi-env-support)
  - [To deprecate](#to-deprecate)
  - [Flow](#flow)
    - [1. job `trigger_passport`](#1-job-trigger_passport)
      - [1.1. step `preprocess`](#11-step-preprocess)
      - [1.2. step `trigger_passport`](#12-step-trigger_passport)
    - [2. job `env_prepare`](#2-job-env_prepare)
      - [2.1. step `preprocess`](#21-step-preprocess)
      - [2.2. step `get_cloud_passport`](#22-step-get_cloud_passport)
      - [2.3. step `credential_rotation`](#23-step-credential_rotation)
      - [2.4. step `bg_manage`](#24-step-bg_manage)
      - [2.5. step `env_inventory_generation`](#25-step-env_inventory_generation)
      - [2.6. step `registry_discovery`](#26-step-registry_discovery)
      - [2.7. step `process_env_template`](#27-step-process_env_template)
      - [2.8. step `app_reg_def_process`](#28-step-app_reg_def_process)
      - [2.9. step `process_sd`](#29-step-process_sd)
      - [2.10. step `generate_deployment_plan`](#210-step-generate_deployment_plan)
      - [2.11. step `env_build`](#211-step-env_build)
      - [2.12. step `generate_effective_set`](#212-step-generate_effective_set)
      - [2.13. step `generate_argocd_repo`](#213-step-generate_argocd_repo)
      - [2.14. step `postprocess`](#214-step-postprocess)
      - [2.15. step `git_commit`](#215-step-git_commit)
      - [2.16. step `es_pusher`](#216-step-es_pusher)
    - [3. job `cmdb_import`](#3-job-cmdb_import)
      - [3.1. step `preprocess`](#31-step-preprocess)
      - [3.2. step `cmdb_import`](#32-step-cmdb_import)
    - [4. job `sync`](#4-job-sync)
      - [4.1. step `preprocess`](#41-step-preprocess)
      - [4.2. step `sync`](#42-step-sync)

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. `run_cloud_passport` (берет паспорт из даунстри джобы и декриптит) уже в `env_prepare`?
2. `generate_deployment_plan`, `argocd_repo_generator`, `es-pusher`, `git_commit` лягут под `orchestrator.py`?
3. В бгд кейсе что должно быть в `namespace-map.yml` в `deployPostfix` - bss или bss-peer, bss-origin?

## AI

1. [phase2] Consider create_if_not_exist | replace strategies for appregdef processing
2. [phase2] Design integration with the central appregdef storage
3. [phase2] Design SAVE_ARTIFACTS_STRATEGY
    1. save env_instance/ES/sd.yaml to a job artifact on SAVE_ALL
4. Design `git_commit`
    1. Depending on `PIPELINE_TYPE` and `SAVE_ARTIFACTS_STRATEGY`, commit env_instance/ES/sd.yaml or not
5. After the flow is finalized analyze the flow for optimization

## Data exchange Rules

1. Within `orchestrator.py`, steps exchange:
   - structured data via the in-memory context `ctx.*`
   - scalars via the in-memory parameters
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

## Defaults

1. APP_ARTIFACTS_DIR: `${CI_PROJECT_DIR}/tmp/app-artifacts/`

## DD and zip layout

`dd_downloading` stores artifacts at `APP_ARTIFACTS_DIR`:

```text
${APP_ARTIFACTS_DIR}/
  <app-name>/
    <app-version>/
      dd.json             # DD
      dd.zip              # downloaded zip artifact
      dd/                 # unzipped content
```

## `deploy-plan.yml`

```yaml
- # Mandatory
  # `<app-name>:<version>`
  version: string
  # Mandatory
  deployPostfix: string
  # Mandatory
  namespace: string
  # Mandatory
  wave: int
  # Mandatory
  # Default `UniqForApp`
  # Set from the AppDef attribute `netcracker.com/argo-app-generation-type`
  generationType: enum[`UniqForApp`, `UniqForVersion`, `UniqForRun`]
  # Mandatory
  # Sub-folder segment inserted before `values` in the deploy context.
  # Value depends on `generationType`:
  #   `UniqForApp`     -> ""
  #   `UniqForVersion` -> <version>
  #   `UniqForRun`     -> a UUID7
  generationId: string
```

Example:

```yaml
- version: app-1:1.2.3
  deployPostfix: core
  namespace: env-1-core
  wave: 0
  generationType: UniqForApp
  generationId: ''
- version: app-2:4.5.6
  deployPostfix: core
  namespace: env-1-core
  wave: 1
  generationType: UniqForRun
  generationId: 0190c7e2-1a2b-7c3d-8e4f-5a6b7c8d9e0f
```

## `namespace-map.yml`

Flat map keyed by the `deployPostfix`, value the rendered namespace name:

```yaml
<deployPostfix>: <namespace-name>
```

Example:

```yaml
# composite
core: env-1-core
oss: env-1-oss
bss: env-1-bss
```

## `ctx.current_env`

TBD

## build.env

TBD

## APPLICATION_VERSIONS

TBD

## Locations

```text
/environments/<cluster>/<env>/
  # inputs:
  Inventory/
    env_definition.yml            # env_definition
    solution-descriptor/
      sd.yaml                     # SD
      delta_sd.yaml               # SD
    deploy-plan.yml               # DP (new)
    parameters/...                # env specific paramsets
    resource_profiles/...         # env specific RPO
    credentials/...               # shared creds
    configurations/...            # shared template variables
  # outputs:
  effective-set/...               # ES
  tenant.yml                      # env instance
  cloud.yml                       # env instance
  bg_domain.yml                   # env instance
  composite_structure.yml         # env instance
  Namespaces/                     # env instance
    <ns>/                         # env instance
      namespace.yml               # env instance
      Applications/...            # env instance
  Credentials/credentials.yml     # env instance
  AppDefs/...                     # appreg defs
  RegDefs/...                     # appreg defs
```

## Uniq names

### `generate_deployment_plan`

- Путь App Def становятся одним из инпутов для `generate_deployment_plan`
- Задает `generationType` из атрибута `metadata.netcracker.com/argo-app-generation-type`
  соответствующего App Def. При отсутствии атрибута — `UniqForApp`.
- Задает `generationId` значение которое зависит от `generationType` - "", `<version>`, UUID7
- Когда необходимо `generate_deployment_plan` генерирует UUID7

### ES Calc

- Читает `deploy-plan.yml`. Для `generationType != UniqForApp` вставляет между `<application-name>`
  и `values` подпапку, равную `generationId`:

  ```text
  /environments/<cluster>/<env>/effective-set/deployment/<deployPostfix>/<application-name>/<generationId>/values/...
  ```

- Для `UniqForApp` подпапка не добавляется (поведение как сейчас).
- `UniqForVersion`: последующая операция реплейсит предыдущую папку (как сейчас).
- `UniqForRun`: папки накапливаются — каждый запуск добавляет новую, предыдущие остаются.
- Решение по каждому приложению принимается независимо от остальных.
- Политика ретеншена в ES Calc не предусмотренна

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
3. Template testing
4. `ENV_INVENTORY_INIT: true`
5. `registry_discovery`
6. `SD_SOURCE_TYPE: artifact`

## Flow

### 1. job `trigger_passport`

Triggers:

- `GET_PASSPORT: true`

#### 1.1. step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] add/align the step
2. `crypt.decrypt`
   - AI[phase2] add/align the step

#### 1.2. step `trigger_passport`

Triggers:

- always when the job runs

Functions:

1. `trigger_passport`
    - input:
      - `integration.yaml`
      - `credentials.yaml`
      - `ENV_NAMES`
    - output:
      - triggered downstream pipeline
    - actions:
      - trigger discovery repository pipeline
    - [phase1] unchanged
    - AI[phase2]: add the step

### 2. job `env_prepare`

Triggers:

- always

#### 2.1. step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `set_defaults`
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
    - [phase1] unchanged
    - AI[phase2]: move out of the before script
    - AI[phase2]: implement [#1506](https://github.com/Netcracker/qubership-envgene/issues/1506)
3. `git_fetch`
    - [phase1] unchanged
4. `crypt.decrypt`
    - [phase1] unchanged
    - AI[phase2] Check no-op if `crypt: false`

#### 2.2. step `get_cloud_passport`

Triggers:

- `GET_PASSPORT: true`

Functions:

TBD

- input:
  - `integration.yaml`
  - cloud passport in `trigger_passport` downstream pipeline
- output:
  - cloud passport
- actions:
  - find the downstream discovery pipeline via bridges, download its artifacts
  - Fernet-decrypt or re-encrypt
- [phase1] unchanged

#### 2.3. step `credential_rotation`

Triggers:

- `CRED_ROTATION_PAYLOAD`

Functions:

TBD

- [phase1] unchanged
- AI[phase2]: check UC readiness and test coverage

#### 2.4. step `bg_manage`

Triggers:

- `BG_MANAGE: true`

Functions:

TBD

- [phase1] unchanged
- AI[phase2]: check UC readiness and test coverage

#### 2.5. step `env_inventory_generation`

Triggers:

- `ENV_INVENTORY_CONTENT` or
- `ENV_SPECIFIC_PARAMS`

Ноут - критерии `ENV_INVENTORY_INIT` и `ENV_TEMPLATE_NAME` и `is_template_test` удалены по сравнению с мастером

Functions:

TBD

- output:
  - env_definition
- [phase1] unchanged
- AI[phase2]: check UC readiness and test coverage

#### 2.6. step `registry_discovery`

Triggers:

- ???

Functions:

TBD

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

#### 2.7. step `process_env_template`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY` or
- `ENV_BUILDER: true`

Functions:

1. `set_template_version`
    - input:
      - `ENV_TEMPLATE_VERSION`
      - ~~`ENV_TEMPLATE_VERSION_PEER`~~
      - ~~`ENV_TEMPLATE_VERSION_ORIGIN`~~
      - `ENV_TEMPLATE_VERSION_UPDATE_MODE`
      - env definition
    - output:
      - updated env_definition
    - actions:
      - set template version
    - [phase1] unchanged
2. `download_env_template`
    - input:
      - env definition
      - artifact definition
    - output:
      - downloaded template files
    - actions:
      - validate env definition, artifact definition
      - download env template
    - [phase1] unchanged
    - AI[phase1]: fix the template-version-setting bug
    - AI[phase2]: move template downloading from `app_reg_def_process`

#### 2.8. step `app_reg_def_process`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY` or
- `ENV_BUILDER: true`

Functions:

1. `compute_template_macros` (`render_config_env.generate_config`)
    - input:
      - env_definition
      - cloud passport
      - deployer config
    - output:
      - `ctx.current_env` with `current_env.*` macros: `name`, `environmentName`, `tenant`, `cloud`,
        `cloudNameWithCluster`, `cmdb_name`, `cmdb_url`, `description`, `owners`, `env_template`,
        `additionalTemplateVariables`, `cluster.*`, `cloud_passport`. `solution_structure` initialized to {}
    - actions:
      - generates the macro values above
    - AI[phase2]: rename `generate_config` -> `compute_template_macros`
2. `load_template_descriptor` (`render_config_env.set_env_templates`)
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
3. `generate_bgd_file`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered bg domain into env instance
    - actions:
      - renders the bg domain into the env instance
      - no-op if no bg domain
4. `generate_namespace_files`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered namespaces into env instance
    - actions:
      - render all namespaces into env instance
5. `compute_namespace_map` (new)
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
6. `generate_composite_structure`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered composite structure into env instance
    - actions:
      - render the composite structure template, validate (no-op if none)
7. `compute_composite_topology` (new)
    - input:
      - rendered composite structure into env instance
      - rendered bg domain into env instance
      - rendered namespace objects into env instance
    - output:
      - `ctx.current_env.composite_topology`
    - actions:
      - resolve baseline + satellites, each member resolves its namespace template to the rendered namespace name
    - AI[phase2]: adopt the macro computation from master
8. `run_appregdef_render`
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
    - [phase1] unchanged
    - AI[phase2]: renders only required appregdef
    - AI[phase2]: implement create_if_not_exist | replace strategies

#### 2.9. step `process_sd`

Triggers:

- (`SD_VERSION` or `SD_DATA`) and
- `PIPELINE_TYPE` is not `GITLAB_DEPLOY`

Functions:

1. `handle_sd`
    - input:
      - `SD_VERSION`
      - `SD_DATA`
      - `SD_SOURCE_TYPE`
      - `SD_REPO_MERGE_MODE`
      - sd.yaml
      - appreg defs
    - output:
      - updated sd.yaml
      - delta_sd.yaml
    - actions:
      - merge sd
    - [phase1] unchanged
    - AI[phase1]: do not call in the new flow, call in the old flow
    - AI[phase2]: remove `SD_SOURCE_TYPE`

#### 2.10. step `generate_deployment_plan`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `generate_deployment_plan`
    - input:
      - `APPLICATION_VERSION`
      - params.environment_id -> `build.env.FULL_ENV_NAME`
      - app defs
      - `namespace-map.yml`
      - filters:
        - `DEPLOY_POSTFIXES_FILTER`
        - `NAMESPACE_NAMES_FILTER`
        - `COMPONENT_NAMES_FILTER`
        - `WAVE_NAMES_FILTER`
    - output:
      - `deploy-plan.yml`
    - actions:
      - process `APPLICATION_VERSION` (download SD, merge), calculate (APPLICATION_VERSION)
      - enrich DP, plan map (namespace_map)
      - filter DP, plan filter (filter vars)
    - AI[phase1]: do not call in the old flow, call in the new flow
    - AI[phase1]: move to GitHub
    - AI[phase1]: implement uniq app names (Artem)
    - AI[phase2]: use [`artifact-searcher`](https://github.com/Netcracker/qubership-envgene/tree/main/python/artifact-searcher) lib to download SD to support public registries (Artem)

#### 2.11. step `env_build`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY` or
- `ENV_BUILDER: true`

Functions:

1. `generate_solution_structure`
    - input:
      - `sd.yaml` or `deploy-plan.yml`
    - output:
      - `ctx.current_env.solution_structure`
    - actions:
      - join applications by deployPostfix with namespace_map
      - no-op if no `sd.yaml` or `deploy-plan.yml`
    - AI[phase1]: support DP as well as SD
    - AI[phase2]: add `namespace-map.yml` as input to optimize execution time
2. `run_build_environment`
    - input:
      - downloaded template files
      - env_definition
      - `ctx.current_env`
      - `ctx.current_env_template`
      - `ctx.current_env.composite_topology`
      - `ctx.current_env.solution_structure`
      - cloud passport
    - output:
      - fully rendered env instance
      - updated env_definition
    - actions:
      - `.generate_tenant_file`
      - `.generate_cloud_file`
      - `process_cloud_passport`: merge cloud_passport into the rendered `cloud.yml`
      - `.create_external_credentials`
      - `.generate_paramset_templates`
      - `.create_credentials`
      - `apply_ns_build_filter`
    - [phase1] unchanged
    - AI[phase1]: test manually
    - AI[phase2]: prepare a UC, add tests

#### 2.12. step `generate_effective_set`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY` or
- `GENERATE_EFFECTIVE_SET: true`

Functions:

1. `dd_downloading`
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
2. `sbom_generation`
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
3. `null_validation`
    - AI[phase1]: check what exists
4. `ES Calc CLI`
    - input:
      - env instance
      - `sd.yaml` or `deploy-plan.yml`
      - sboms
    - output:
      - Effective Set
    - actions:
      - generates ES
    - AI[phase1]: support DP as well as SD
    - AI[phase1]: implement uniq app names

#### 2.13. step `generate_argocd_repo`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `generate_argocd_repo`
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
    - AI[phase1]: remove DP generation (Artem)
    - AI[phase1]: add local DD (Artem)
    - AI[phase1]: encrypt ARGO_DPG_CONTEXT.env (Artem)
    - AI[phase2]: move to GitHub

#### 2.14. step `postprocess`

Triggers:

- always when the job runs

Functions:

1. `crypt.encrypt`
   - AI[phase2] Check no-op if `crypt: false`

#### 2.15. step `git_commit`

Triggers:

- always when the job runs

Functions:

1. `git_commit`
    - input:
      - `CLUSTER_NAME`
      - `ENVIRONMENT_NAME`
    - AI[phase1]: If `PIPELINE_TYPE: GITLAB_DEPLOY` then do not commit into inventory repository:
      - env instance
      - effective set
    - AI[phase2]: depending on `SAVE_ARTIFACTS_STRATEGY`, save env_instance/ES/sd.yaml to artifacts or not
    - AI[phase2]: unify with `es-pusher`
    - AI[phase2]: chech no-op if no changes

#### 2.16. step `es_pusher`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `es-pusher`
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
    - AI[phase2]: move to GitHub
    - AI[phase2]: unify with `git_commit`

### 3. job `cmdb_import`

Triggers:

- `CMDB_IMPORT: true`

#### 3.1. step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] add/align the step
2. `crypt.decrypt`
   - AI[phase2] add/align the step

#### 3.2. step `cmdb_import`

Triggers:

- always when the job runs

Functions:

1. `cmdb_import`
    - input:
      - `build.env.FULL_ENV_NAME`
    - AI[phase1]: do not call in the new flow, call in the old flow

### 4. job `sync`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY`

#### 4.1. step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] add/align the step
2. `crypt.decrypt`
   - AI[phase2] add/align the step

#### 4.2. step `sync`

Triggers:

- always when the job runs

Functions:

1. `sync`
    - input:
      - `ARGO_DPG_CONTEXT.env`
      - `build.env.FULL_ENV_NAME`
    - output:
      - TBD
    - actions:
      - TBD
    - AI[phase1]: do not call in the old flow, call in the new flow
    - AI[phase2]: move to GitHub
