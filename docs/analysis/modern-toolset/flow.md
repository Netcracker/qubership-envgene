# Modern toolset flow

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. ...

## AI

1. Договорится с Леней про использование динамического пайпа
2. Договорится с Леней/Темой про `process_dp` функцию
3. Поговорить с Темой про шифровние ARGO_DPG_CONTEXT.env не DPG а crypt
4. Получить OK от Вани на move to GitHub `es-pusher`, `sync`
5. [phase2] Подумать о create_if_not_exist | replace стратегиях процессинга appregdef
6. [phase2] Дизайн интеграции с centrall appregdef storage
7. Дизайн `setup_rendering_context`
8. Дизайн `process_dp`
9. [phase2] Дизайн раcпиливания `env_build`
10. [phase2] Дизайн SAVE_ARTIFACTS_STRATEGY
    1. сохранять env_instance/ES/sd.yaml в job-артефакт при SAVE_ALL
11. Дизайн `git_commit`
    1. Учитывая `PIPELINE_TYPE` и `SAVE_ARTIFACTS_STRATEGY` комитить или нет env_instance/ES/sd.yaml
12. Решить про `registry_discovery`
13. Описать критерии вызова функций
14. [после финализации флоу] проанализировать флоу на оптимизацию чтения файлов
    (убрать избыточные чтения/записи, кэш в пределах одного процесса)

## Data exchange Rules

1. Functions and sub-functions in one job exchange data through the filesystem.
2. Jobs exchange through files published as job artifacts, or through dotenv files.
3. A step depends on the artifact, not on another step's execution.

## Artifacts

Producers and consumers are Target Flow step numbers.

| Artifact                  | Path                                        | Producers      | Consumers              |
|---------------------------|---------------------------------------------|----------------|------------------------|
| env_definition            | Inventory/env_definition.yml                | 7, 9           | 8, 9, 10, 11, 22       |
| cloud_passport            | cloud-passport/                             | 2              | 10                     |
| artdef                    | configuration/artifact_definitions/         | 8              | 9                      |
| downloaded template files | templates/ (+ tmp/peer, tmp/origin)         | 9              | 11, 12, 13, 15, 17, 22 |
| current-env-context.yml   | current-env-context.yml                     | 10             | 11, 12, 13, 15, 22     |
| current-env-template.yml  | current-env-template.yml                    | 11             | 12, 13, 15, 22         |
| bg_domain                 | env instance bg_domain.yml                  | 12             | 14, 16                 |
| rendered namespaces       | env instance Namespaces/                    | 13             | 14, 16                 |
| namespace-map.yml         | namespace-map.yml (not committed)           | 14             | 19, 21, 22, external   |
| composite_structure.yml   | env instance composite_structure.yml        | 15             | 16                     |
| composite-topology.yml    | composite-topology.yml                      | 16             | 22                     |
| appreg defs               | env instance appregdef files                | 17             | 18, 19, 23             |
| sd.yaml                   | Inventory/solution-descriptor/sd.yaml       | 18, 20         | 21, 23, 26             |
| delta_sd.yaml             | Inventory/solution-descriptor/delta_sd.yaml | 18             | 26                     |
| deploy-plan.yml           | deploy-plan.yml                             | 19             | 20, 27                 |
| solution-structure.yml    | solution-structure.yml                      | 21             | 22                     |
| env instance              | environments/<cluster>/<env>/               | 12, 13, 15, 22 | 26, 29, 30, 4          |
| DD and zip                | deploy descriptors dir                      | 23             | 24, 27                 |
| sboms                     | sboms/                                      | 24             | committed              |
| effective set             | env instance effective-set/                 | 26             | 27, 30                 |
| appset/app CR             | appsets                                     | 27             | 30                     |
| ARGO_DPG_CONTEXT.env      | dotenv (reports)                            | 27             | 5                      |
| control flags/scalars     | build.env / CI vars                         | 1              | many                   |

## deploy-plan

- version: app-1:version-1
  deployPostfix: core
  namespace: ''
  wave: 0
- version: app-2:version-2
  deployPostfix: core
  namespace: ''
  wave: 1

## APPLICATION_VERSIONS

TBD

## Pipe generation

- Single `ENV_NAMES` -> direct include `static-api.yaml`, multiple -> run generator.
- OOB launches `static-api.yaml` directly.
- Thin generator: per env emit `trigger: include static-api.yaml`, forward vars, set `ENV_NAME=<cluster>/<env>`.
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
    ENV_NAME: "cluster-01/env-1"
  ...

env-prepare-cluster-01-env-2:
  trigger:
    include:
      - local: static-api.yaml
    ...
  variables:
    ENV_NAME: "cluster-01/env-2"
  ...
```

AI:

- Write a new `/module/scripts/main.py generate_pipeline` on the `build_pipegene` image (or the common `envgene` one)
- Prepare `gitlab_ci.yaml`
- Add a passport generation job for the per-env flow
- Verify `orchestrator.py` needs no changes
- Verify `static-api.yaml` needs no changes
- Verify `$ENV_NAMES =~ /[,; \n]/` works correctly
- Update the gsf package
- Update the gsf-related documentation
- Do the same on GitHub

## Target Flow

1. job `trigger_passport`
   - не изменяем
2. job `get_passport`
   - не изменяем
   - AI[phase1]: протестить руками
   - AI[phase2]: подготовить UC, покрыть тестами
3. job `generate_effective_set/env_prepare`
   1. `set_defaults`
   2. `cert_apply`
       - не изменяем
       - AI[phase2]: перенести из before script
   3. `git_fetch`
       - не изменяем
   4. `crypt` to decrypt
       - не изменяем
   5. `credential_rotation`
       - не изменяем
       - AI[phase2]: проверить готовность UC, покрытие тестами
   6. `bg_manage`
       - не изменяем
       - AI[phase2]: проверить готовность UC, покрытие тестами
   7. `env_inventory_generation`
       - не изменяем
       - AI[phase2]: проверить готовность UC, покрытие тестам
   8. `registry_discovery`
       - trigger:
         - always
       - input:
         - system config
         - env_definition
       - output:
         - artdef
       - actions:
         - generate artdef base from CMDB/central appreg storage
       - выпилить или расширить (запилить интеграцию с central appregdef storage)?
       - AI[phase1]: оставляем выключенным
       - AI[phase2]: включаем (?)
       - AI[phase3]: add integration with central appregdef storage
   9. `process_env_template` (.set_version -> .download)
       - trigger:
         - always
       - input:
         - ENV_TEMPLATE_VERSION
         - ENV_TEMPLATE_VERSION_PEER
         - ENV_TEMPLATE_VERSION_ORIGIN
         - ENV_TEMPLATE_VERSION_UPDATE_MODE
         - env definition
         - artifact definition
       - output:
         - downloaded template files (3 templates in case of bgd)
         - updated env_definition
       - actions:
         - validate env definition, artifact definition
         - set template version
         - download env template
       - не изменяем
       - AI[phase1]: пофиксить багу c установкой версии темплейта
   10. `setup_rendering_context.compute_template_macros`
       - trigger:
         - always
       - input:
         - env_definition
         - cloud_passport
         - deployer config
       - output:
         - `current-env-context.yml` file with `current_env.*` macros: `name`, `environmentName`, `tenant`, `cloud`, `cloudNameWithCluster`, `cmdb_name`, `cmdb_url`, `description`, `owners`, `env_template`, `additionalTemplateVariables`, `cluster.*`, `cloud_passport`; `solution_structure` initialized to {}
       - actions:
         - генерирует значения макросов выше
       - AI[phase1]: extract generate_config into a standalone step (currently the first line of env_build)
   11. `setup_rendering_context.load_template_descriptor`
       - trigger:
         - always
       - input:
         - env_definition (`envTemplate.name`)
         - downloaded template dirs for common/peer/origin
         - `current-env-context.yml`
       - output:
         - `current-env-template.yml` for common/peer/origin - the rendered and validated descriptor(s)
       - actions:
         - render the descriptor if .j2
         - validate against schema
         - load into current_env_template; repeat for the PEER and ORIGIN dirs
       - AI[phase1]: extract set_env_templates into this sub-function
   12. `env_build.render_bgd`
       - trigger:
         - always
       - input:
         - downloaded template dir
         - `current-env-context.yml`
         - `current-env-template.yml`
       - output:
         - rendered bg domain into env instance
       - actions:
         - renders the bg_domain object into the env instance (render_config_env.generate_bgd_file)
         - no-op if no bg_domain
   13. `env_build.render_namespaces`
       - trigger:
         - always
       - input:
         - downloaded template dirs for common/peer/origin
         - `current-env-context.yml`
         - `current-env-template.yml`
       - output:
         - rendered namespace objects into env instance
       - actions:
         - render all namespace templates for the template name (light render, the name is independent of solution_structure)
   14. `setup_rendering_context.compute_namespace_map` to calculate the deployPostfix to namespace mapping for the current env
       - trigger:
         - always
       - input:
         - `ENV_NAME`
         - rendered namespace objects in env instance
         - rendered bg domain in env instance
       - output:
         - `namespace-map.yml` file with `current_env.namespace_map` (`{deployPostfix: {namespace: <name>}}`), for current env only
           - loaded into the Jinja context as a macro for template/external consumers
       - actions:
         - read rendered namespace name + deployPostfix for each env namespace
         - calculate deployPostfix to namespace mapping (incl. BG suffix)
       - AI[phase1]: create the function
   15. `env_build.render_composite_structure`
       - trigger:
         - always
       - input:
         - downloaded template dirs for common
         - `current-env-context.yml`
         - `current-env-template.yml`
       - output:
         - composite_structure.yml into env instance
       - actions:
         - render the composite structure template, validate (no-op if none)
   16. `setup_rendering_context.compute_composite_topology`
       - trigger:
         - always
       - input:
         - composite_structure.yml (rendered)
         - bg domain in env instance
         - rendered namespace objects (env instance namespace dirs)
       - output:
         - `composite-topology.yml` file with `current_env.composite_topology` (`{baseline: {originNamespace, peerNamespace?, controllerNamespace?}, satellites: [...]}`)
       - actions:
         - resolve baseline + satellites, each member resolves its namespace template to the rendered namespace name
       - AI[phase2]: adopt the macro computation from master
   17. `app_reg_def_process` for list of appregdef
       - trigger:
         - always
       - input:
         - env template files
         - env instance files
         - system config
         - `APPREG_DEF_STRATEGY`
       - output:
         - appreg def files
       - actions:
         - render appreg defs, validate
         - skip which is present in env instance files if `APPREG_DEF_STRATEGY` == `create_if_not_exist``APPREG_DEF_STRATEGY` == `replace`
       - [phase1]: не изменяем
       - AI[phase2]: renders only required appregdef
       - AI[phase2]: implement create_if_not_exist | replace strategies
   18. `process_sd`
       - trigger:
         - (`SD_VERSION` or `SD_DATA`) and `PIPELINE_TYPE` !== `GITAB_DEPLOY`
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
       - [phase1]: не изменяем
       - AI[phase1]: в новом флоу не вызывается, в старом вызывается
       - AI[phase2]: удалить `SD_SOURCE_TYPE`
   19. `generate_deployment_plan`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY`
       - input:
         - `APPLICATION_VERSION`
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
       - AI[phase1]: в старом флоу не вызывается, в новом вызывается
       - AI[phase1]: create the function
       - AI[phase1]: move to GitHub
   20. `dp_sd_adapter`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY`
       - inputs:
         - `deploy-plan.yml`
       - outputs:
         - `sd.yaml`
       - actions:
         - generates `sd.yaml` from `deploy-plan.yml`
       - AI[phase1]: create the function to simplify migration (do not touch `compute_solution_structure` ES calc, Colly)
       - AI[phase2]: remove the function
   21. `setup_rendering_context.compute_solution_structure`
       - trigger:
         - always
       - input:
         - `sd.yaml`
         - `namespace-map.yml`
       - output:
         - `solution-structure.yml` file with `current_env.solution_structure`
       - actions:
         - join applications by deployPostfix with namespace_map
         - no-op if no `sd.yaml`
       - AI[phase1]: create the function (split from render_config_env.generate_solution_structure lines 286-305)
       - note: `composite_topology` is produced earlier (step 16); `environments` (site Environments Structure) is NOT produced here
         - environments = per-env upsert of namespace_map into environment-structure.yml at run end (phase2), respects 5s NFR (no cross-env template download)
       - AI[phase2]: support DP as well as SD
   22. `env_build`
       - input:
         - downloaded template dirs for common/peer/origin
         - env_definition
         - `current-env-context.yml`
         - `current-env-template.yml`
         - `namespace-map.yml`
         - `composite-topology.yml`
         - `solution-structure.yml`
       - renders the remaining env instance artifacts (explicit list):
         - `.render_tenant`
         - `.render_cloud`
         - `.create_external_credentials`
         - `.render_paramsets`
         - `.create_credentials`
       - `apply_ns_build_filter`
         - желательно оставить as is
       - [phase1]: не изменяем
   23. `dd_downloading`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - appreg defs
         - `sd.yaml` or `deploy-plan.yml`
       - output:
         - DD and zip
       - actions:
         - downloads DD and zip
       - AI[phase1]: separate from sbom generation (to prepare input for sbom generation and argocd-dpg)
       - AI[phase2]: support DP as well as SD
   24. `sbom_generation`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - DD and zip
       - output:
         - sboms
       - actions:
         - generate sbom
         - sbom retention
       - AI[phase1]: support local DD and zip
   25. `null_validation`
       - AI[phase1]: проверить, что есть
   26. ES Calc CLI
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY` or
         - `GENERATE_EFFECTIVE_SET: true`
       - input:
         - env instance
         - SD or DP
       - output:
         - Effective Set
       - actions:
         - generates ES
       - AI[phase2]: support DP as well as SD
   27. `argocd_repo_generator`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY`
       - input:
         - DP
         - TBD
       - output:
         - appset CR, app CR, TBD
         - dotenv ARGO_DPG_CONTEXT.env
       - actions:
         - TBD
       - AI[Тема]: убрать генерацию DP
       - AI[Тема]: добавить локальные DD
       - AI[Тема]: шифровать ARGO_DPG_CONTEXT.env
       - AI[phase2]: move to GitHub
         - или это сделает `crypt`?
         - или объеденить build.env ?
   28. `crypt` to encrypt
   29. `git_commit`
       - AI[phase1]: в зависимости от `PIPELINE_TYPE` комитить или нет env_instance/ES/sd.yaml
       - AI[phase2]: в зависимости от `SAVE_ARTIFACTS_STRATEGY` сохранять или нет env_instance/ES/sd.yaml в артифакты
       - AI[phase2]: объеденить с es-pusher?
   30. `es-pusher`
       - trigger:
         - `PIPELINE_TYPE: GITAB_DEPLOY`
       - input:
         - instance files
           - effective set
           - appset
         - `DCL_GIT_URL`
         - `DCL_GIT_BRANCH` дефолты на стороне оркестратора
         - `DCL_CONFIG_GITLAB_USER`
         - `DCL_CONFIG_GITLAB_TOKEN`
         - `GITLAB_USER_NAME`
         - `GITLAB_USER_EMAIL`
         - COMMIT_FILTER
         - params.environment_id -> `ENV_NAME`
         - params.commit_message -> `DEPLOYMENT_TICKET_ID`
         - params.rootdir -> x
         - path filter
       - output:
         - instance repo commit
       - actions:
         - push effective set and appsets to the deploy target repo
       - AI[phase1]: move to GitHub
   31. удаление лишнего
4. job `cmdb_import`
   - AI[phase1]: в новом флоу не вызывается, в старом вызывается
5. job `sync`
   - trigger:
     - `PIPELINE_TYPE: GITAB_DEPLOY`
   - input:
     - dotenv ARGO_DPG_CONTEXT.env
   - output:
     - TBD
   - actions:
     - TBD
   - AI[phase1]: в старом флоу не вызывается, в новом вызывается
   - AI[phase2]: move to GitHub
