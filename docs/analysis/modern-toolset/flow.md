# Modern toolset flow

- [Modern toolset flow](#modern-toolset-flow)
  - [OQ](#oq)
  - [AI](#ai)
  - [Data exchange Rules](#data-exchange-rules)
  - [Defaults](#defaults)
  - [DD and zip layout](#dd-and-zip-layout)
  - [`deploy-plan.yml`](#deploy-planyml)
  - [`namespace-map.yml`](#namespace-mapyml)
  - [`APPLICATION_VERSIONS`](#application_versions)
  - [`OPERATION_TYPE`](#operation_type)
  - [`TARGET_BG_STATE`](#target_bg_state)
  - [`PIPELINE_TYPE`](#pipeline_type)
  - [`BG_NS_TARGET`](#bg_ns_target)
  - [state file](#state-file)
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
      - [1.2 step `trigger_passport`](#12-step-trigger_passport)
      - [1.3 step `get_cloud_passport`](#13-step-get_cloud_passport)
      - [1.4 step `credential_rotation`](#14-step-credential_rotation)
      - [1.5 step `bg_manage`](#15-step-bg_manage)
      - [1.6 step `env_inventory_generation`](#16-step-env_inventory_generation)
      - [1.7 step `registry_discovery`](#17-step-registry_discovery)
      - [1.8 step `process_env_template`](#18-step-process_env_template)
      - [1.9 step `app_reg_def_process`](#19-step-app_reg_def_process)
      - [1.10 step `process_sd`](#110-step-process_sd)
      - [1.11 step `generate_deployment_plan` (`dpg`)](#111-step-generate_deployment_plan-dpg)
      - [1.12 step `env_build`](#112-step-env_build)
      - [1.13 step `generate_effective_set`](#113-step-generate_effective_set)
      - [1.14 step `generate_argocd_repo` (`argo-cd dpg`)](#114-step-generate_argocd_repo-argo-cd-dpg)
      - [1.15 step `cmdb_import`](#115-step-cmdb_import)
      - [1.16 step `postprocess`](#116-step-postprocess)
      - [1.17 step `git_commit`](#117-step-git_commit)
      - [1.18 step `es_pusher`](#118-step-es_pusher)
    - [2 job `sync`](#2-job-sync)
      - [2.1 step `preprocess`](#21-step-preprocess)
      - [2.2 step `sync`](#22-step-sync)

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. Нужны ли `process_env_template` / `app_reg_def_process` / `process_sd` при `OPERATION_TYPE: CLEAN`, или их
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
8. Где будет валидация на корректность бг операции (разрешён ли переход состояний)
   1. только в оркестратор пайпе
   2. в оркестратор пайпе и в энвгене (сейчас она в энвгене есть и ее хочется выпилить)
   3. если не будет валидации то и `TARGET_BG_STATE` не нужен

## AI

1. [phase2] Consider create_if_not_exist | replace strategies for appregdef processing
2. [phase2] Design integration with the central appregdef storage
3. [phase2] Design SAVE_ARTIFACTS_STRATEGY
    1. save env_instance/ES/sd.yaml to a job artifact on SAVE_ALL
4. Design `git_commit`
    1. Depending on `PIPELINE_TYPE` and `SAVE_ARTIFACTS_STRATEGY`, commit env_instance/ES/sd.yaml or not
5. After the flow is finalized analyze the flow for optimization
6. [phase2] Согласовать с Леней `BG_MANAGE`, `TARGET_BG_STATE`
7. [phase2] Согласовать с Артемом `discovery_deployment_plan`. Узнать Кто и когда чекаутит ES репо?
8. Стейт файл из нью лука

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

## `APPLICATION_VERSIONS`

TBD

## `OPERATION_TYPE`

`OPERATION_TYPE`: enum[ `CLEAN`, `DEPLOY`, `BGD-INIT`, `BGD-WARMUP`, `BGD-PROMOTE`, `BGD-ROLLBACK`, `BGD-COMMIT` ]
default: `DEPLOY`

## `TARGET_BG_STATE`

```yaml
originNamespace:
  name: bss-origin
  state: active
  version: v2.1.0                    # не используем
peerNamespace:
  name: bss-peer
  state: candidate
  version: v2.2.0                    # не используем
controllerNamespace: bss-controller
updateTime: 2024-01-15T10:30:00Z     # не используем
```

## `PIPELINE_TYPE`

`PIPELINE_TYPE`: enum [ `GITLAB_DEPLOY`, `LEGACY` ]
default: `LEGACY`

## `BG_NS_TARGET`

`BG_NS_TARGET`: enum [ `ACTIVE`, `CANDIDATE` ]
default: None

1. Используется в связке с `ENV_TEMPLATE_VERSION`:
   1. На основе стейт файла и `BG_NS_TARGET` вычисляется для какого ns обновить версию темплейта `bgNsArtifacts.origin` / `bgNsArtifacts.peer`
2. ?

## state file

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
5. `registry_discovery`
6. `SD_SOURCE_TYPE: artifact`
7. `BG_MANAGE`
8. extended merge (removed)

## Flow

### 1 job `env_prepare`

Triggers:

- always

#### 1.1 step `preprocess`

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
2. `cert_apply`
    - [phase1] unchanged
    - AI[techDebt-P1]: move out of the before script
3. `git_fetch`
    - [phase1] unchanged
4. `crypt.decrypt`
    - [phase1] unchanged

#### 1.2 step `trigger_passport`

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
    - [phase1] unchanged

#### 1.3 step `get_cloud_passport`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
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

#### 1.4 step `credential_rotation`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- `CRED_ROTATION_PAYLOAD`

Functions:

TBD

- [phase1] unchanged
- AI[phase1]: check UC readiness of [credential-rotation](https://github.com/Netcracker/qubership-envgene/blob/docs/modern-toolset-dev/docs/use-cases/credential-rotation.md)
- AI[phase1]: check test coverage

#### 1.5 step `bg_manage`

Triggers:

- `OPERATION_TYPE: BGD-*` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `change_bg_state`
    - input:
      - `TARGET_BG_STATE`
    - output:
      - BG state files
    - actions:
      - validate state transition
      - create/update BG state files
    - AI[bgd]: support state change based on `OPERATION_TYPE` (design is not done)
    - AI[bgd]: remove `BG_STATE` and validation (design is not done)
    - AI[bgd]: after the validation decision
      - IF support validation in envgene
        - design `TARGET_BG_STATE` structure (Leonid)
        - support `TARGET_BG_STATE` instead of `BG_STATE` (design is not done)
    - AI[bgd]: support "target" state files (design is not done) (nice to have)
2. `warmup`
    - triggers:
      - `OPERATION_TYPE: BGD-WARMUP`
    - input:
      - env instance
    - output:
      - updated env instance
    - actions:
        - copy active -> candidate namespace/applications
    - AI[bgd]: no updates
    <!-- - AI[bgd]: support warmup on ES instead of env instance (design is not done) -->

#### 1.6 step `env_inventory_generation`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`ENV_INVENTORY_CONTENT` or `ENV_SPECIFIC_PARAMS`)

Functions:

TBD

- output:
  - env_definition
- [phase1] unchanged
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
- AI[phase1]: keep it off
- AI[techDebt-P2]: delete functionality

#### 1.8 step `process_env_template`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `set_template_version`
    - input:
      - `ENV_TEMPLATE_VERSION`
      - `BG_NS_TARGET`
      - `ENV_TEMPLATE_VERSION_UPDATE_MODE`
      - env definition
    - output:
      - updated env_definition
    - actions:
      - set template version
    - [phase1] unchanged
    - AI[bgd] поддержать изменение версий темплейта пира/ориджина на основе `BG_NS_TARGET` + `ENV_TEMPLATE_VERSION`,
                   с учетом `ENV_TEMPLATE_VERSION_UPDATE_MODE`. (design is not done)
    - AI[bgd] понять имплементировали ли `ENV_TEMPLATE_VERSION_PEER`/`ENV_TEMPLATE_VERSION_ORIGIN`. если да - удалить
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
    - AI[techDebt-LOGS]: move template downloading from `app_reg_def_process`

#### 1.9 step `app_reg_def_process`

Triggers:

- `OPERATION_TYPE: DEPLOY` and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `compute_template_macros` (`render_config_env.generate_config`)
    - input:
      - env_definition
      - cloud passport
      - deployer config
    - output:
      - template macros
    - actions:
      - generates the macro values above
    - AI[techDebt-LOGS]: rename `generate_config` -> `compute_template_macros`
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
    - AI[techDebt-PERF]: renders only required appregdef
    - AI[techDebt-PERF]: implement create_if_not_exist | replace strategies

#### 1.10 step `process_sd`

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
2. `sd_dp_adapter`
    - input:
      - `updated sd.yaml`
    - output:
      - `deploy-plan.yml`
    - actions:
      - generate dp based on sd
    - [phase1] add the function

#### 1.11 step `generate_deployment_plan` (`dpg`)

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: BGD-WARMUP`) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `generate_deployment_plan` (`dpg`)
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
      - `deploy-plan.yml`
    - actions:
      - process `APPLICATION_VERSION` (download SD, merge), calculate (APPLICATION_VERSION)
      - enrich DP, plan map (namespace_map)
      - filter DP, plan filter (filter vars)
    - AI[phase1]: do not call in the old flow, call in the new flow
    - AI[phase1]: move to GitHub
    - AI[phase1]: implement uniq app names (Artem)
    - AI[techDebt-P1]: use [`artifact-searcher`](https://github.com/Netcracker/qubership-envgene/tree/main/python/artifact-searcher) lib to download SD to support public registries (Artem)
    - AI[bgd]: desing BG cases
    - AI[bgd]: support BG cases (Artem)
2. `discovery_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: BGD-WARMUP`
    - input:
      - effective set (где его взять?)
        - argo url + cred - TBD
      - namespace - TBD
    - output:
      - `deploy-plan.yml`
    - actions:
      - TBD
    - AI[bgd]: design inputs
    - AI[bgd]: implement the function (Artem)

#### 1.12 step `env_build`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN`) and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `generate_solution_structure`
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
2. `run_build_environment`
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
    <!-- - AI[bgd]: переписать `apply_ns_build_filter` на использование `BG_NS_TARGET` нужно ли -->
3. `set_cleaned_mark`
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

#### 1.13 step `generate_effective_set`

Triggers:

- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `GENERATE_EFFECTIVE_SET: true`))

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
    - AI[phase1]: add `APP_ARTIFACTS_DIR`
    - AI[phase1]: support DP
    - AI[phase1]: remove SD support
    - AI[techDebt-PERF]: оптимизировать скачивание DD/zip. https://docs.gitlab.com/ci/caching/
      - (??) не скачивать zip для `generate_argocd_repo`
      - (??) кэшировать ДД.json по аналогии с sbom
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
    - AI[techDebt-PERF]: оптимизировать генерацию sbom https://docs.gitlab.com/ci/caching/
      - (??) не скачивать zip для `generate_argocd_repo`
      - (??) кэшировать ДД.json по аналогии с sbom
3. `null_validation`
    - AI[phase1]: check what exists
4. `ES Calc CLI`
    - input:
      - env instance
      - `sd.yaml` or `deploy-plan.yml`
      - sboms
      - `OPERATION_TYPE`
    - output:
      - Effective Set
    - actions:
      - generates ES
    - AI[phase1]: support DP
    - AI[phase1]: remove SD support
    - AI[phase1]: implement uniq app names
    - AI[bgd]: Поддержка бг кейса в ES структуре - `<namespace-folder-01>` включает peer|origin постфиксы
        - `deployPostfix` + включенность в бг домен определяет маппинг на нс фолдер в ES
        - `namespace` определяет имя фолдера в ES
    - AI[bgd]: add `state` to `bg_domain` in topology context
    - AI[bgd]: post-ES python patcher writes bg_domain.status (state-only ops), no full recalc. (nice to have)
5. `partial_es_processing`
    - triggers:
      - `PIPELINE_TYPE: LEGACY` and `GENERATE_EFFECTIVE_SET: true`
    - input:
      - Effective Set from previous function `ES Calc CLI`
      - Effective Set from previous operation, repository
    - output:
      - Effective Set
    - actions:
      - в ES мержится реплейсом application слайсы которые изменились в текущей операции генерации
    - AI[phase1!]: set `PIPELINE_TYPE: LEGACY` and `GENERATE_EFFECTIVE_SET: true` trigger
6. `external_credential_provisioning`
    - input:
      - Effective Set
    - output:
      - created credentials in external cred store
    - actions:
      - if the Effective Set includes external credential context, run the credential provisioning CLI, which creates or verifies the credentials in the external credential store
      - if it does not, no-op

#### 1.14 step `generate_argocd_repo` (`argo-cd dpg`)

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: BGD-WARMUP`) and
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
    - AI[phase1]: remove DP generation (Artem)
    - AI[phase1]: add local DD (Artem)
    - AI[phase1]: encrypt ARGO_DPG_CONTEXT.env (Artem)
    - AI[phase3]: move to GitHub

#### 1.15 step `cmdb_import`

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

#### 1.16 step `postprocess`

Triggers:

- always when the job runs

Functions:

1. `crypt.encrypt`

#### 1.17 step `git_commit`

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
    - AI[phase3]: unify with `es-pusher`

#### 1.18 step `es_pusher`

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

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: BGD-WARMUP`) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

#### 2.1 step `preprocess`

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] Unify by cert config source with Envgene, currently - ca_bundle
   - AI[phase2] Unify code (?)
2. `crypt.decrypt`
   - AI[phase2] Unify by key config source with Envgene, currently - `ENVGENE_AGE_PRIVATE_KEY`. Узнать у Темы нужно ли это
   - AI[phase2] Unify code (?)

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
    - AI[phase1]: do not call in the old flow, call in the new flow
    - AI[phase3]: move to GitHub
