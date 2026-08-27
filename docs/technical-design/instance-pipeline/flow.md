# Modern toolset flow

- [Modern toolset flow](#modern-toolset-flow)
  - [Flow](#flow)
    - [1 job `env_prepare`](#1-job-env_prepare)
      - [1.1 step `preprocess` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#11-step-preprocess-to-be-implemented-not-implemented-yet)
      - [1.2 step `get_passport`](#12-step-get_passport)
      - [1.3 step `credential_rotation`](#13-step-credential_rotation)
      - [1.4 step `change_bg_state`](#14-step-change_bg_state)
      - [1.5 step `warmup`](#15-step-warmup)
      - [1.6 step `env_inventory_generation`](#16-step-env_inventory_generation)
      - [1.8 step `set_template_version`](#18-step-set_template_version)
      - [1.9 step `process_env_template` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#19-step-process_env_template-to-be-implemented-not-implemented-yet)
      - [1.10 step `appregdef_render`](#110-step-appregdef_render)
      - [1.11 step `regdefv2_adapter`](#111-step-regdefv2_adapter)
      - [1.12 step `deploy_postfix_namespace_map`](#112-step-deploy_postfix_namespace_map)
      - [1.13 step `process_sd`](#113-step-process_sd)
      - [1.14 step `generate_deployment_plan`](#114-step-generate_deployment_plan)
      - [1.15 step `env_build`](#115-step-env_build)
      - [1.16 step `generate_effective_set`](#116-step-generate_effective_set)
      - [1.17 step `git_commit`](#117-step-git_commit)
      - [1.18 step `generate_argocd_repo` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#118-step-generate_argocd_repo-to-be-implemented-not-implemented-yet)
      - [1.19 step `es_pusher`](#119-step-es_pusher)
      - [1.20 step `cmdb_import`](#120-step-cmdb_import)
      - [1.21 step `postprocess`](#121-step-postprocess)
    - [2 job `sync`](#2-job-sync)
      - [2.1 step `preprocess` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#21-step-preprocess-to-be-implemented-not-implemented-yet)
      - [2.2 step `sync` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#22-step-sync-to-be-implemented-not-implemented-yet)

This document describes the Instance pipeline as jobs, steps, and functions, and defines each step's trigger
(the `should_run` gate). It is the source of truth for the triggers. Per-step behavior is documented under
[steps](/docs/technical-design/instance-pipeline/steps/), and per-scenario projections under
[sub-flows](/docs/technical-design/instance-pipeline/sub-flows/).

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

#### 1.1 step `preprocess` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

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

- `GET_PASSPORT: true`

Functions:

1. `get_passport`
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

- `CRED_ROTATION_PAYLOAD`

Functions:

TBD

#### 1.4 step `change_bg_state`

Design: [`change_bg_state`](/docs/technical-design/instance-pipeline/steps/change-bg-state.md)

Triggers:

- `OPERATION_TYPE: BGD` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `change_bg_state`
    - input:
      - `BG_STATE`
    - output:
      - BG state files
    - actions:
      - write the origin and peer `state` of the BG state files directly from `BG_STATE`. No validation and no
        computation from the current state or `BGD_OPERATION`
    - AI[bgd]: implement `change_bg_state` based on `BG_STATE` without any validation
    - AI[bgd-2]: implement validation
    - AI[bgd-2]: support fail states
    - AI[bgd-2]: support "target" state files

#### 1.5 step `warmup`

Design: [`warmup`](/docs/technical-design/instance-pipeline/steps/warmup.md)

Triggers:

- `OPERATION_TYPE: BGD` and
- `BGD_OPERATION: warmup` and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `warmup`
    - input:
      - env instance
      - `env_definition.yml`
      - state files
    - output:
      - updated env instance (candidate namespace replicated from active)
      - updated `env_definition.yml`
    - actions:
      - copy `active` -> `candidate` namespace content and `Application` objects, keep the candidate `name`
      - re-point the candidate template-version pin in `env_definition.yml`:
        `envTemplate.bgNsArtifacts.<candidate>` := `envTemplate.bgNsArtifacts.<active>`
      <!-- - copy the active side's per-side env-specific associations to the candidate in `env_definition.yml`:
        `envSpecificParamsets`, `envSpecificE2EParamsets`, `envSpecificTechnicalParamsets`,
        `envSpecificResourceProfiles` entries keyed `<postfix>-<active>` -> `<postfix>-<candidate>`
        (per-side keys `<postfix>-origin`/`<postfix>-peer` are already the match key, see `build_env.py`) -->

#### 1.6 step `env_inventory_generation`

Triggers:

- `ENV_INVENTORY_CONTENT` or `ENV_SPECIFIC_PARAMS`

Functions:

TBD

- output:
  - env_definition
- AI[techDebt-P2]: remove `ENV_INVENTORY_INIT: true` (with bwc)

#### 1.8 step `set_template_version`

Design: [`set_template_version`](/docs/technical-design/instance-pipeline/steps/set-template-version.md)

Triggers:

- `ENV_TEMPLATE_VERSION`

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

#### 1.9 step `process_env_template` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

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

Design: [`appregdef_render`](/docs/technical-design/instance-pipeline/steps/appregdef-render.md)

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
4. `generate_namespace_files_and_map`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered namespaces into env instance
    - actions:
      - render all namespaces into env instance
5. `run_appregdef_render`
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

#### 1.11 step `regdefv2_adapter`

Design: [`regdefv2_adapter`](/docs/technical-design/instance-pipeline/steps/regdefv2-adapter.md)

Triggers:

- `PIPELINE_TYPE: GITLAB_DEPLOY` and
  (`OPERATION_TYPE: DEPLOY` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`)), or
- `PIPELINE_TYPE: LEGACY` and `OPERATION_TYPE: DEPLOY` and
  (`SD_VERSION` or `SD_DATA` or `GENERATE_EFFECTIVE_SET: true`)

Functions:

1. `regdefv2_adapter`
    - input:
      - downloaded template files
      - credentials
      - `LOCAL_PUBREG_FILE`
      - RegDefs v1
    - output:
      - `pubreg_params.yaml`
      - RegDefs v2
      - credential the RegDef v2
    - actions:
      - render the Cloud object, fold paramsets into parameters, read the whole `e2eParameters`
        section, expand credential macros to resolve secret values
      - write the resolved registry auth parameters to `pubreg_params.yaml` for dpg
      - when `MAVEN_PROVIDER` is a public cloud provider create RegDefs v2 and corresponding credential

#### 1.12 step `deploy_postfix_namespace_map`

Design: [`deploy_postfix_namespace_map`](/docs/technical-design/instance-pipeline/steps/deploy-postfix-namespace-map.md)

Triggers:

- `OPERATION_TYPE: DEPLOY`

Functions:

1. `compute_namespace_map`
    - input:
      - `FULL_ENV_NAME`
      - rendered namespace in env instance
      - rendered bg domain in env instance
    - output:
      - `namespace-map.yml`
    - actions:
      - read rendered namespace name + deployPostfix + BG role for each env namespace (both BG sides)
      - build the map keyed by deployPostfix: non-BG postfix -> namespace name, BG postfix -> per-side entry with
        both `origin` and `peer` namespace names (side from the rendered BG domain)

#### 1.13 step `process_sd`

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
      - appreg defs v1 or the synthesized RegDef v2 from `regdefv2_adapter`
    - output:
      - updated `sd.yaml`
    - actions:
      - merge sd
    - [phase1] unchanged
    - AI[phase1]: do not call in the new flow, call in the old flow
    - AI[techDebt-P2]: remove `SD_SOURCE_TYPE`

2. `adapt_sd_to_deploy_plan`
    - input:
      - updated `sd.yaml`
      - `namespace-map.yml`
    - output:
      - `delta-deploy-plan.yml`
    - actions:
      - generate dp based on sd
      - resolve each entry namespace name from `namespace-map.yml` (deployPostfix -> namespace name)
      - fail if a deployPostfix has no matching namespace in `namespace-map.yml`
      - non-BG only
    - [phase1] add the function

#### 1.14 step `generate_deployment_plan`

Design: [`process_deployment_plan`](/docs/technical-design/instance-pipeline/steps/process-deployment-plan.md)

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`)) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `run_generate_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - `APPLICATION_VERSIONS`
      - `FULL_ENV_NAME`
      - app defs
      - `namespace-map.yml`
      - `BG_NS_TARGET`
      - (`pubreg_params.yaml`
      - filters:
        - `DEPLOY_POSTFIXES_FILTER`
        - `NAMESPACE_NAMES_FILTER`
        - `COMPONENT_NAMES_FILTER`
        - `WAVE_NAMES_FILTER`
    - output:
      - `delta-deploy-plan.yml`
    - actions:
      - process `APPLICATION_VERSIONS` (download SD, merge), calculate (APPLICATION_VERSIONS)
      - enrich DP, plan map (namespace_map):
        - bare `deployPostfix` entry: look up `namespace-map.yml[deployPostfix]`. A scalar value binds directly
          (non-BG). A per-side value (BG) binds `[BG_NS_TARGET]`, and if `BG_NS_TARGET` is not set fail asking for it.
          An absent key fails naming the `deployPostfix`
        - `namespace:name:version` entry: take the namespace as given, recover its `deployPostfix` as the key whose
          value names the namespace (scalar, or `origin`/`peer` of a per-side entry), `BG_NS_TARGET`-independent. No
          match fails naming the namespace
      - filter DP, plan filter (filter vars)
    - AI[techDebt-P1]: use [`artifact-searcher`](https://github.com/Netcracker/qubership-envgene/tree/main/python/artifact-searcher) lib to download SD to support public registries (Artem)
2. `resolve_warmup_delta`
    - triggers:
      - `OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`
    - input:
      - `deploy-plan.yml` from repository
      - state files
    - output:
      - `delta-deploy-plan.yml`
      - updated `deploy-plan.yml` (candidate slice replaced)
    - actions:
      - filter the full plan to the active side and rebind each entry `namespace` to the candidate
        namespace (keep `deployPostfix`, `version`, `generationId`, `wave`), write as `delta-deploy-plan.yml`
      - replace the candidate slice in the repository `deploy-plan.yml` (filter-exclude `!<candidate>` then merge
        the rebound active).
3. `merge_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - `deploy-plan.yml` from repository
      - `delta-deploy-plan.yml`
    - output:
      - updated `deploy-plan.yml`
    - actions:
      - merge the delta onto the repository full plan (add new entries, raise `wave`, never remove)
    - AI[bgd]: Add the functions
4. `reduce_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: CLEAN`
    - input:
      - `deploy-plan.yml` from repository
      - `NAMESPACE_NAMES`
    - output:
      - updated `deploy-plan.yml`
    - actions:
      - run the plan filter in exclude mode, passing each namespace in `NAMESPACE_NAMES` as a `!<namespace>` token
      - writes the repository plan minus the cleaned namespaces (no delta, no plan passed to the calculator)
    - AI[bgd]: Add the functions

#### 1.15 step `env_build`

Design: [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md)

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN`) and
- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `ENV_BUILDER: true`))

Functions:

1. `generate_composite_structure`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - downloaded template files
      - `ctx.current_env`
      - `ctx.current_env_template`
    - output:
      - rendered composite structure into env instance
    - actions:
      - render the composite structure template, validate (no-op if none)
2. `compute_composite_topology`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - rendered composite structure into env instance
      - rendered namespace objects into env instance
    - output:
      - `ctx.current_env.composite_topology`
    - actions:
      - resolve baseline + satellites, each member resolves its namespace template to the rendered namespace name
3. `generate_solution_structure`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - `deploy-plan.yml`
    - output:
      - `ctx.current_env.solution_structure`
    - actions:
      - join applications by deployPostfix with namespace_map
      - no-op if no `deploy-plan.yml`
    - AI[phase1]: support DP as well as SD
    - AI[phase1]: remove SD support
    - AI[techDebt-P1]: add `namespace-map.yml` as input to optimize execution time
4. `run_build_environment`
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
    - AI[bgd]: Replace `apply_ns_build_filter` with SD-scoped generation. Render only namespaces from the SD,
      then apply file-replace-merge to the committed instance. `NS_BUILD_FILTER` can then be deprecated.
5. `set_cleaned_mark`
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

#### 1.16 step `generate_effective_set`

Design: [`generate_effective_set`](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md)

Triggers:

- (`PIPELINE_TYPE: GITLAB_DEPLOY` or (`PIPELINE_TYPE: LEGACY` and `GENERATE_EFFECTIVE_SET: true`)) and
- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`))

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
      - appreg defs v1 or the synthesized RegDef v2 from `regdefv2_adapter`
      - `delta-deploy-plan.yml` for `DEPLOY` and warmup (produced in 1.14); no plan for `CLEAN` (marker-driven)
      - `APP_ARTIFACTS_DIR`
    - output:
      - DD and ZIP at `${APP_ARTIFACTS_DIR}`, sboms
    - actions:
      - resolve DD per app with appreg defs
      - download DD+ZIP, unzip
      - generate SBOM from local DD + ZIP
    - AI[techDebt-PERF]: Optimize DD and ZIP downloads and SBOM generation.
      <https://docs.gitlab.com/ci/caching/>
      - (??) Do not download ZIP for `generate_argocd_repo`.
      - (??) Cache DD.json in the same way as SBOM.
4. `effective_set_entrypoint`
    - input:
      - env instance
      - `delta-deploy-plan.yml` for `DEPLOY` and warmup (produced in 1.14); no plan for `CLEAN` (marker-driven)
      - sboms
      - `OPERATION_TYPE`
      - `BGD_OPERATION`
    - output:
      - Effective Set
    - actions:
      - runs the ES Calc CLI to generate ES
      - full or partial merge by `ctx.partial_merge_mode`
    - AI[phase1]: support DP
    - AI[phase1]: remove SD support
    - AI[phase1]: implement uniq app names
    - AI[bgd]: Support the BG case in the ES structure. `<namespace-folder-01>` includes peer and origin postfixes.
5. `external_credential_provisioning`
    - input:
      - Effective Set
    - output:
      - created credentials in external cred store
    - actions:
      - if the Effective Set includes external credential context, run the credential provisioning CLI, which creates or verifies the credentials in the external credential store
      - if it does not, no-op
    - AI[phase2]: merge external creds feature

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
    - AI[phase2]: depending on `SAVE_ARTIFACTS_STRATEGY`, save env_instance/ES/deploy-plan.yaml to artifacts or not
    - AI[phase2]: unify with `es-pusher`

#### 1.18 step `generate_argocd_repo` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

Triggers:

- (`OPERATION_TYPE: DEPLOY` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`)) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `generate_argocd_repo` argo dpg generate structure
    - input:
      - `delta-deploy-plan.yml`
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

#### 1.19 step `es_pusher`

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
        - ...
      - COMMIT_FILTER
      - params.environment_id -> `build.env.FULL_ENV_NAME`
      - params.commit_message -> `DEPLOYMENT_TICKET_ID`
      - params.rootdir -> x
      - path filter
    - output:
      - instance repository commit
    - actions:
      - push effective set and appsets to the deploy target repository
    - AI[phase3]: move to GitHub
    - AI[phase3]: unify with `git_commit`

#### 1.20 step `cmdb_import`

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

#### 1.21 step `postprocess`

Triggers:

- always when the job runs

Functions:

1. `crypt.encrypt`
    - AI[techDebt-P1]: Create as a step. Currently inside `env_build` and `generate_effective_set`

### 2 job `sync`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`)) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

#### 2.1 step `preprocess` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

Triggers:

- always when the job runs

Functions:

1. `cert_apply`
   - AI[phase2] Unify by cert config source with Envgene, currently - ca_bundle
2. `crypt.decrypt`
   - AI[phase2] Unify by key config source with Envgene, currently - `ENVGENE_AGE_PRIVATE_KEY`.

#### 2.2 step `sync` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

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
