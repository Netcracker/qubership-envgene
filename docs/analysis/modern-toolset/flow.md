# Modern toolset flow

- [Modern toolset flow](#modern-toolset-flow)
  - [OQ](#oq)
  - [AI](#ai)
  - [Data exchange Rules](#data-exchange-rules)
  - [Defaults](#defaults)
  - [DD and zip layout](#dd-and-zip-layout)
  - [Deploy plan](#deploy-plan)
    - [Merge algorithm](#merge-algorithm)
  - [`namespace-map.yml`](#namespace-mapyml)
  - [Instance pipeline parameters](#instance-pipeline-parameters)
    - [`APPLICATION_VERSIONS`](#application_versions)
    - [CLUSTER\_NAME](#cluster_name)
    - [ENVIRONMENT\_NAME](#environment_name)
    - [DELTA\_DEPLOY](#delta_deploy)
    - [`OPERATION_TYPE`](#operation_type)
    - [`PIPELINE_TYPE`](#pipeline_type)
    - [`BG_NS_TARGET`](#bg_ns_target)
  - [`bg_domain` in topology context](#bg_domain-in-topology-context)
  - [Locations](#locations)
  - [Uniq names](#uniq-names)
    - [`generate_deployment_plan`](#generate_deployment_plan)
    - [ES Calc](#es-calc)
  - [DD for `generate_argocd_repo`](#dd-for-generate_argocd_repo)
  - [To deprecate](#to-deprecate)
  - [Flow](#flow)
    - [1 job `env_prepare`](#1-job-env_prepare)
      - [1.1 step `preprocess`](#11-step-preprocess)
      - [1.2 step `get_passport`](#12-step-get_passport)
      - [1.3 step `credential_rotation`](#13-step-credential_rotation)
      - [1.4 step `change_bg_state`](#14-step-change_bg_state)
      - [1.5 step `warmup`](#15-step-warmup)
      - [1.6 step `env_inventory_generation`](#16-step-env_inventory_generation)
      - [1.7 step `registry_discovery`](#17-step-registry_discovery)
      - [1.8 step `set_template_version`](#18-step-set_template_version)
      - [1.9 step `process_env_template`](#19-step-process_env_template)
      - [1.10 step `appregdef_render`](#110-step-appregdef_render)
      - [1.11 step `deploy_postfix_namespace_map`](#111-step-deploy_postfix_namespace_map)
      - [1.12 step `process_sd`](#112-step-process_sd)
      - [1.13 step `generate_deployment_plan`](#113-step-generate_deployment_plan)
      - [1.14 step `env_build`](#114-step-env_build)
      - [1.15 step `generate_effective_set`](#115-step-generate_effective_set)
      - [1.16 step `generate_argocd_repo` (`argo-cd dpg`)](#116-step-generate_argocd_repo-argo-cd-dpg)
      - [1.17 step `cmdb_import`](#117-step-cmdb_import)
      - [1.18 step `postprocess`](#118-step-postprocess)
      - [1.19 step `git_commit`](#119-step-git_commit)
      - [1.20 step `es_pusher`](#120-step-es_pusher)
    - [2 job `sync`](#2-job-sync)
      - [2.1 step `preprocess`](#21-step-preprocess)
      - [2.2 step `sync`](#22-step-sync)

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. Нужны ли `process_env_template` / `appregdef_render` / `process_sd` при `OPERATION_TYPE: CLEAN`, или их
   можно скипать? Сейчас (PoC) отрабатывают все.
2. [Done]`generate_deployment_plan`
   1. всегда требует `APPLICATION_VERSION`?
      1. A: Да
   2. использует ли `deploy-plan.yml` из предыдущей операции (из репо) как инпут
      1. А: Нет, дискаверится из арги
3. `APPLICATION_VERSIONS` ?
   1. без него будет генерится только topology + pipeline
   2. с ним все контексты
      1. если `OPERATION_TYPE: !CLEAN` то `APPLICATION_VERSION` мандаторен
   3. в nocmdb только
4. Кто и когда чекаутит ES репо?
5. Как менять бг стейт в ES
   1. Пересчитывать ES полностью
   2. Ввести лайт режим калькулятора который правит только стейты
   3. Ввести пост калькулятор, питон функцию которая будет править стейты
6. Как обрабатываем `COMMIT` бг операцию? Делаем ли клин legacy нс?
   1. нет, при коммите только меняем стейт
7. Вводим ли бг-специфик фильтры (на основе `BG_NS_TARGET` и стейт файлов) в `generate_deployment_plan`?
   1. нет.

## AI

1. [phase2] Consider create_if_not_exist | replace strategies for appregdef processing
2. [phase2] Design integration with the central appregdef storage
3. [phase2] Design SAVE_ARTIFACTS_STRATEGY
    1. save env_instance/ES/sd.yaml to a job artifact on SAVE_ALL
4. Design `git_commit`
    1. Depending on `PIPELINE_TYPE` and `SAVE_ARTIFACTS_STRATEGY`, commit env_instance/ES/sd.yaml or not
5. After the flow is finalized analyze the flow for optimization
6. [phase2] Согласовать с Артемом `discovery_deployment_plan`. Узнать Кто и когда чекаутит ES репо?
7. Стейт файл из нью лука

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

1. `APP_ARTIFACTS_DIR`: `${CI_PROJECT_DIR}/tmp/app-artifacts/`
2. `OPERATION_TYPE: DEPLOY`
3. `PIPELINE_TYPE: LEGACY`
4. `DCL_GIT_BRANCH: master`

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

## Deploy plan

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

The deployment plan exists in two forms:

- **Full plan** (`deploy-plan.yaml`) — the environment's accumulated set of deployed applications, persisted in the
  repository. It is the source of truth for the current app-set (for example, the state a warmup replicates from).
- **Delta plan** (`delta-deploy-plan.yaml`) — the plan for a single operation, listing only the applications acted on
  in it. Transient, not persisted.

Per operation: `generate_deployment_plan` builds the delta from the `APPLICATION_VERSION` input, then
`merge_deployment_plan` merges the delta onto the repository full plan and commits the result.

### Merge algorithm

Each operation merges its delta plan with the repository full plan to produce the next full plan.

**Entry identity.** Two entries are the same deployment when they share `<app-name>` (from `version`) and
`namespace`. `generationType: UniqForVersion` adds `version` to the identity and `UniqForRun` adds `generationId`,
so under those modes a new version or run is a distinct entry rather than a replacement of the previous one.

**Merge rule.** A delta entry with no counterpart in the full plan is added. A delta entry that matches an existing
one is collapsed into a single entry whose `wave` is the higher of the two.

**Invariant.** The merge only adds entries and raises `wave`, it never removes. An entry present in the full plan
but absent from the delta is retained. This is the stale-app corner case.

## `namespace-map.yml`

Flat map keyed by the `deployPostfix`, value the rendered namespace name (already resolved to one concrete
namespace per postfix).

For a `deployPostfix` that belongs to a BG domain the value is resolved to the `ORIGIN` or
`PEER` namespace by `BG_NS_TARGET` (see `compute_namespace_map`, step 1.11, which resolves the BG suffix from the
rendered BG domain). Non-BG postfixes resolve to their single namespace.

```yaml
<deployPostfix>: <namespace-name>
```

Example:

```yaml
# composite, BG_NS_TARGET: ORIGIN
core: env-1-core
oss: env-1-oss
bss: env-1-bss-origin   # BG domain member, resolved to the ORIGIN side
```

## Instance pipeline parameters

### `APPLICATION_VERSIONS`

### CLUSTER_NAME

### ENVIRONMENT_NAME

### DELTA_DEPLOY

### `OPERATION_TYPE`

`OPERATION_TYPE`: enum[ `CLEAN`, `DEPLOY`, `BGD_INIT`, `BGD_WARMUP`, `BGD_PROMOTE`, `BGD_ROLLBACK`, `BGD_COMMIT` ]
default: `DEPLOY`

### `PIPELINE_TYPE`

`PIPELINE_TYPE`: enum [ `GITLAB_DEPLOY`, `LEGACY` ]
default: `LEGACY`

### `BG_NS_TARGET`

`BG_NS_TARGET`: enum [ `ORIGIN`, `PEER` ]
default: None

1. Используется в связке с `ENV_TEMPLATE_VERSION`:
   1. На основе `BG_NS_TARGET` вычисляется для какого ns обновить версию темплейта `bgNsArtifacts.origin` / `bgNsArtifacts.peer`
2. Используется в `compute_namespace_map` для резолвинга deployPostfix пира ориджина в нс

## `bg_domain` in topology context

```yaml
# parameters.yaml
bg_domain:
  name: env-1-bg-domain
  type: bgdomain
  originNamespace:
    name: env-1-bss-origin
    type: namespace
    state: active                                         # new
  peerNamespace:
    name: env-1-bss-peer
    type: namespace
    state: candidate                                      # new
  controllerNamespace:
    name: env-1-controller
    type: namespace
    url: https://controller-env-1-controller.qubership.org
# credentials.yaml
bg_domain:
  controllerNamespace:
    username: user-placeholder-123
    password: pass-placeholder-123
```

## Locations

```text
/environments/<cluster>/<env>/
  # inputs:
  Inventory/
    env_definition.yml            # env_definition
    solution-descriptor/
      sd.yaml                     # SD
    deploy-plan.yml               # full DP
    delta-deploy-plan.yml         # delta DP
    parameters/...                # env specific paramsets
    resource_profiles/...         # env specific RPO
    credentials/...               # shared creds
    configurations/...            # shared template variables
  # outputs:
  effective-set/...               # ES
  tenant.yml                      # env instance
  cloud.yml                       # env instance
  composite_structure.yml         # env instance
  bg_domain.yml                   # env instance
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

## DD for `generate_argocd_repo`

**Опция 1:**

Качать DD всегда, zip по отсутствию SBOM (сейчас качается DD + zip по отсутствию SBOM)

(-) DD качается зря в ряде кейсов

**Опция 2:**

`generate_argocd_repo` в GOPA кейсах переходит на SBOM вместо DD

(-) Требуется разовое изменение `sbom_generation` (расширение `application/vnd.qubership.app.chart`)  
(-) Будущие изменения в `generate_argocd_repo` которые потребуют новых полей DD могут потребовать изменения `sbom_generation`  
(-) Требуется реализации процедуры регенерации SBOM при новой версии SBOM-спеки (изменилась версия спеки, перегенери даже если есть кэш)  

**Опция 3:**

Кэшировать DD, sbom средствами гитлаба

(-) Высокая вероятность мискэша, потому что кэш пер раннер нода, есть ретеншен полиси кэша  

## To deprecate

1. Fernet
2. GAV notation
3. Template testing
4. `ENV_INVENTORY_INIT: true`
5. `ENV_TEMPLATE_NAME`
6. `registry_discovery`
7. `SD_SOURCE_TYPE: artifact`
8. `BG_MANAGE`
9. extended merge (removed)
10. `NS_BUILD_FILTER`
11. `BG_STATE`

## Flow

Three levels: **job**, **step**, **function**.

**Job** - a CI unit.

**Step** - the unit of orchestration, a `PipelineStep` in code. It has a `should_run` gate (the "Triggers"
below), plus a name, status, and duration reported in `PIPELINE SUMMARY`. Steps execute as the ordered list
in `run_single_env_pipeline`. A step whose `should_run` returns `False` is `SKIPPED`.

**Function** - the unit of implementation, a plain callable with domain logic invoked by a step's `execute()`.
It has no gate, status, or timing of its own. A step may call several functions.

### 1 job `env_prepare`

Triggers:

- always

#### 1.1 step `preprocess`

Triggers:

- always

Functions:

1. `set_defaults`
    - inputs:
      - none
    - output:
      - `build.env`
      - env variables
    - actions:
      - set defaults
2. `cert_apply`
    - AI[techDebt-P1]: move out of the before script
3. `git_fetch`
4. `crypt.decrypt`
    - AI[techDebt-P1]: Create as a step. Currently inside `env_build` and `generate_effective_set`

#### 1.2 step `get_passport`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- `GET_PASSPORT: true`

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

2. `get_cloud_passport`
   - input:
     - `integration.yaml`
     - cloud passport in `trigger_passport` downstream pipeline
   - output:
     - cloud passport
   - actions:
     - find the downstream discovery pipeline via bridges, download its artifacts
     - Fernet-decrypt or re-encrypt

#### 1.3 step `credential_rotation`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- `CRED_ROTATION_PAYLOAD`

Functions:

TBD

#### 1.4 step `change_bg_state`

Triggers:

- `OPERATION_TYPE: BGD_*` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `change_bg_state`
    - input:
      - `OPERATION_TYPE`
    - output:
      - BG state files
    - actions:
      - derive the target state from `OPERATION_TYPE` + current state files, create/update BG state files
    - AI[bgd]: support state change based on `OPERATION_TYPE`
    - AI[bgd]: remove `BG_STATE`, `BG_MANAGE`
    - AI[bgd-2]: support fail states
    - AI[bgd-2]: support "target" state files

#### 1.5 step `warmup`

Triggers:

- `OPERATION_TYPE: BGD_WARMUP` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `warmup`
    - input:
      - env instance
    - output:
      - updated env instance
    - actions:
      - copy active -> candidate namespace/applications
    - AI[bgd]: no updates(???)

#### 1.6 step `env_inventory_generation`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`ENV_INVENTORY_CONTENT` or `ENV_SPECIFIC_PARAMS`)

Functions:

TBD

- output:
  - env_definition
- AI[techDebt-P2]: remove `ENV_INVENTORY_INIT: true` (with bwc)

#### 1.7 step `registry_discovery`

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
- AI[techDebt-P2]: delete functionality

#### 1.8 step `set_template_version`

Triggers:

- `ENV_TEMPLATE_VERSION` present

Functions:

1. `update_version`
    - input:
      - `ENV_TEMPLATE_VERSION`
      - `BG_NS_TARGET`
      - `ENV_TEMPLATE_VERSION_UPDATE_MODE`
      - env definition
    - output:
      - updated env_definition
    - actions:
      - set template version
    - AI[bgd] support template version change base on `BG_NS_TARGET` + `ENV_TEMPLATE_VERSION`, `ENV_TEMPLATE_VERSION_UPDATE_MODE`.
    - AI[bgd] remove `ENV_TEMPLATE_VERSION_PEER`/`ENV_TEMPLATE_VERSION_ORIGIN`

#### 1.9 step `process_env_template`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `process_env_template`
    - input:
      - env definition
      - artifact definition
    - output:
      - downloaded template files
    - actions:
      - validate env definition, artifact definition
      - download env template
    - AI[techDebt-LOGS]: move template downloading from `appregdef_render`

#### 1.10 step `appregdef_render`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `generate_config`
    - input:
      - env_definition
      - cloud passport
      - deployer config
    - output:
      - template macros
    - actions:
      - generates the macro values above
    - AI[techDebt-LOGS]: rename `generate_config` -> `compute_template_macros`
2. `set_env_templates`
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
    - AI[techDebt-LOGS]: rename `set_env_templates` -> `load_template_descriptor`
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
4. `generate_composite_structure`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered composite structure into env instance
    - actions:
      - render the composite structure template, validate (no-op if none)
    - AI[bgd-2]: PoC renders composite in `env_build` after namespaces. Render it here, before
      `compute_namespace_map`, because a BG domain inside a composite carries origin/peer namespaces there
5. `generate_bgd_from_composite` (new)
    - input:
      - rendered composite structure into env instance
    - output:
      - rendered bg domain into env instance
    - actions:
      - if the composite structure embeds a `bgdomain` member, derive `bg_domain.yml` from it so it is read as before
      - no-op if the composite structure embeds no `bgdomain`
    - AI[bgd]: create the function
    - AI[bgd-2]: drops out when the flow moves to the target topology (replaces `bg_domain` and the composite)
6. `generate_namespace_files_and_map`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered namespaces into env instance
    - actions:
      - render all namespaces into env instance
7. `run_appregdef_render`
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
    - AI[techDebt-PERF]: renders only required appregdef
    - AI[techDebt-PERF]: implement create_if_not_exist | replace strategies

#### 1.11 step `deploy_postfix_namespace_map`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `compute_namespace_map`
    - input:
      - `FULL_ENV_NAME`
      - `BG_NS_TARGET`
      - rendered namespace in env instance
      - rendered bg domain in env instance
    - output:
      - `namespace-map.yml`
    - actions:
      - read rendered namespace name + deployPostfix for each env namespace
      - calculate deployPostfix to namespace mapping (incl. BG suffix)

#### 1.12 step `process_sd`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`PIPELINE_TYPE: LEGACY` and (`SD_VERSION` or `SD_DATA`))

Functions:

1. `handle_sd`
    - input:
      - `SD_VERSION`
      - `SD_DATA`
      - `SD_SOURCE_TYPE`
      - `SD_REPO_MERGE_MODE`
      - `sd.yaml`
      - appreg defs
    - output:
      - `updated sd.yaml`
    - actions:
      - merge sd
    - [phase1] unchanged
    - AI[phase1]: do not call in the new flow, call in the old flow
    - AI[techDebt-P2]: remove `SD_SOURCE_TYPE`
2. `adapt_sd_to_deploy_plan`
    - input:
      - `updated sd.yaml`
    - output:
      - `delta-deploy-plan.yml`
    - actions:
      - generate dp based on sd
    - [phase1] add the function

#### 1.13 step `generate_deployment_plan`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN`) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `run_generate_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
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
      - `delta-deploy-plan.yml`
    - actions:
      - process `APPLICATION_VERSION` (download SD, merge), calculate (APPLICATION_VERSION)
      - enrich DP, plan map (namespace_map)
      - filter DP, plan filter (filter vars)
    - AI[techDebt-P1]: use [`artifact-searcher`](https://github.com/Netcracker/qubership-envgene/tree/main/python/artifact-searcher) lib to download SD to support public registries (Artem)
2. `merge_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN`
    - input:
      - `deploy-plan.yml` from repository
      - `delta-deploy-plan.yml`
    - output:
      - updated `deploy-plan.yml`
    - actions:
      - merges deployment plans
    - AI[bgd]: Add the functions

#### 1.14 step `env_build`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN`) and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `compute_composite_topology`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - rendered composite structure into env instance
      - rendered namespace objects into env instance
    - output:
      - `ctx.current_env.composite_topology`
    - actions:
      - resolve baseline + satellites, each member resolves its namespace template to the rendered namespace name
2. `generate_solution_structure`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - `sd.yaml` or `deploy-plan.yml`
    - output:
      - `ctx.current_env.solution_structure`
    - actions:
      - join applications by deployPostfix with namespace_map
      - no-op if no `sd.yaml` or `deploy-plan.yml`
    - AI[phase1]: support DP as well as SD
    - AI[phase1]: remove SD support
    - AI[techDebt-P1]: add `namespace-map.yml` as input to optimize execution time
3. `run_build_environment`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
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
    - AI[techDebt-P1]: prepare a UC, add tests
    - AI[bgd]: `apply_ns_build_filter` заменить на СД-скоуп генерации: рендерить только нс из СД,
      file-replace-merge в закоммиченный инстанс. Тогда `NS_BUILD_FILTER` уходит в deprecate.
4. `set_cleaned_mark`
    - triggers:
      - `OPERATION_TYPE: CLEAN`
    - input:
      - env instance namespaces
      - `NAMESPACE_NAMES`
    - output:
      - namespaces with `cleaned: true`
    - actions:
      - set `cleaned: true` on `NAMESPACE_NAMES` namespaces (all if empty. error if a namespace is not found)
    - AI[techDebt-LOGS]: extract from `run_build_environment`

#### 1.15 step `generate_effective_set`

Triggers:

- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `GENERATE_EFFECTIVE_SET: true`))

Functions:

1. `validate_creds` + `validate_parameters`
    - input:
      - env instance credentials and parameters
    - output:
      - validation pass or fail (the job fails on invalid input)
    - actions:
      - validate credentials (reserved values, required overrides)
      - validate parameters
2. `sboms_retention_policy`
    - actions:
      - delete sboms beyond the retention policy
3. `get_sboms`
    - input:
      - appreg defs
      - `delta-deploy-plan.yml` if `OPERATION_TYPE: !BGD_WARMUP`
      - `deploy-plan.yml` if `OPERATION_TYPE: BGD_WARMUP`
      - `APP_ARTIFACTS_DIR`
    - output:
      - DD and zip at `${APP_ARTIFACTS_DIR}`, sboms
    - actions:
      - resolve DD per app with appreg defs
      - download DD+zip, unzip
      - generate SBOM from local DD + zip
    - AI[techDebt-PERF]: оптимизировать скачивание DD/zip + генерацию sbom. https://docs.gitlab.com/ci/caching/
      - (??) не скачивать zip для `generate_argocd_repo`
      - (??) кэшировать ДД.json по аналогии с sbom
4. `effective_set_entrypoint`
    - input:
      - env instance
      - `delta-deploy-plan.yml` if `OPERATION_TYPE: !BGD_WARMUP`
      - `deploy-plan.yml` if `OPERATION_TYPE: BGD_WARMUP`
      - sboms
      - `OPERATION_TYPE`
    - output:
      - Effective Set
    - actions:
      - runs the ES Calc CLI to generate ES
      - full or partial merge by `ctx.partial_merge_mode`
    - AI[phase1]: support DP
    - AI[phase1]: remove SD support
    - AI[phase1]: implement uniq app names
    - AI[bgd]: Поддержка бг кейса в ES структуре - `<namespace-folder-01>` включает peer|origin постфиксы
5. `external_credential_provisioning`
    - input:
      - Effective Set
    - output:
      - created credentials in external cred store
    - actions:
      - if the Effective Set includes external credential context, run the credential provisioning CLI, which creates or verifies the credentials in the external credential store
      - if it does not, no-op
    - AI[phase2]: merge external creds feature

#### 1.16 step `generate_argocd_repo` (`argo-cd dpg`)

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: BGD_WARMUP`) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `generate_argocd_repo` (`argo-cd dpg`)
    - input:
      - `deploy-plan.yml`
      - effective set
      - local DD (from `dd_downloading`)
      - `APP_ARTIFACTS_DIR`
      - params.environment_id -> `build.env.FULL_ENV_NAME`
      - TBD
    - output:
      - appset CR, app CR, TBD
      - encrypted by `ENVGENE_AGE_PUBLIC_KEY` dotenv ARGO_DPG_CONTEXT.env
    - actions:
      - TBD
    - AI[phase2]: move into the orchestrator as a PipelineStep
    - AI[phase3]: move to GitHub

#### 1.17 step `cmdb_import`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- `PIPELINE_TYPE: LEGACY` and
- `CMDB_IMPORT: true`

Functions:

1. `cmdb_import`
    - input:
      - `build.env.FULL_ENV_NAME`
    - AI[phase1]: do not call in the new flow, call in the old flow
    - AI[phase1!]: add the step into `env_prepare` job
    - AI[phase1]: remove envgene dot env file
    - AI[phase2]: move into the orchestrator as a PipelineStep

#### 1.18 step `postprocess`

Triggers:

- always when the job runs

Functions:

1. `crypt.encrypt`
    - AI[techDebt-P1]: Create as a step. Currently inside `env_build` and `generate_effective_set`

#### 1.19 step `git_commit`

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

#### 1.20 step `es_pusher`

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `es-pusher`
    - input:
      - if `OPERATION_TYPE: CLEAN` then set env var: `ESPUSHER_OVERWRITE: true` else `ESPUSHER_OVERWRITE: false`
      - instance files
        - effective set
        - appset
      - effective set
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
    - AI[phase3]: move to GitHub
    - AI[phase3]: unify with `git_commit`

### 2 job `sync`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: BGD_WARMUP`) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

#### 2.1 step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] Unify by cert config source with Envgene, currently - ca_bundle
2. `crypt.decrypt`
   - AI[phase2] Unify by key config source with Envgene, currently - `ENVGENE_AGE_PRIVATE_KEY`.

#### 2.2 step `sync`

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
    - AI[phase3]: move to GitHub
