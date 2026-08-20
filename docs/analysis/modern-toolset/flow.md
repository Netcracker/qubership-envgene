# Modern toolset flow

- [Modern toolset flow](#modern-toolset-flow)
  - [OQ](#oq)
  - [AI](#ai)
  - [Data exchange Rules](#data-exchange-rules)
  - [Defaults](#defaults)
  - [DD and ZIP layout](#dd-and-zip-layout)
  - [Deploy plan](#deploy-plan)
    - [Merge algorithm](#merge-algorithm)
    - [Removal on clean](#removal-on-clean)
  - [`namespace-map.yml`](#namespace-mapyml)
  - [Instance pipeline parameters](#instance-pipeline-parameters)
    - [`APPLICATION_VERSIONS`](#application_versions)
    - [CLUSTER\_NAME](#cluster_name)
    - [ENVIRONMENT\_NAME](#environment_name)
    - [DELTA\_DEPLOY](#delta_deploy)
    - [`OPERATION_TYPE`](#operation_type)
    - [`BGD_OPERATION`](#bgd_operation)
    - [`PIPELINE_TYPE`](#pipeline_type)
    - [`BG_NS_TARGET`](#bg_ns_target)
    - [`BG_STATE`](#bg_state)
  - [Locations](#locations)
  - [Uniq names](#uniq-names)
    - [`generate_deployment_plan`](#generate_deployment_plan)
    - [ES Calc](#es-calc)
  - [DD for `generate_argocd_repo`](#dd-for-generate_argocd_repo)
  - [To deprecate](#to-deprecate)
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
      - [1.11 step `deploy_postfix_namespace_map`](#111-step-deploy_postfix_namespace_map)
      - [1.12 step `process_sd`](#112-step-process_sd)
      - [1.13 step `generate_deployment_plan`](#113-step-generate_deployment_plan)
      - [1.14 step `env_build`](#114-step-env_build)
      - [1.15 step `generate_effective_set`](#115-step-generate_effective_set)
      - [1.16 step `git_commit`](#116-step-git_commit)
      - [1.17 step `generate_argocd_repo` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#117-step-generate_argocd_repo-to-be-implemented-not-implemented-yet)
      - [1.18 step `es_pusher`](#118-step-es_pusher)
      - [1.19 step `cmdb_import`](#119-step-cmdb_import)
      - [1.20 step `postprocess`](#120-step-postprocess)
    - [2 job `sync`](#2-job-sync)
      - [2.1 step `preprocess` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#21-step-preprocess-to-be-implemented-not-implemented-yet)
      - [2.2 step `sync` TO BE IMPLEMENTED. NOT IMPLEMENTED YET](#22-step-sync-to-be-implemented-not-implemented-yet)

Working design document for the modern-toolset instance pipeline consolidation. This is the source of truth
for the target flow. The per-component docs in this directory elaborate individual steps.

## OQ

1. Are `process_env_template` / `appregdef_render` / `process_sd` needed for `OPERATION_TYPE: CLEAN`, or can
   they be skipped? The proof of concept runs all of them.
2. [Done]`generate_deployment_plan`
   1. Does it always require `APPLICATION_VERSIONS`?
      1. A: Yes
   2. Does it use `deploy-plan.yml` from the previous operation (from the repository) as input?
      1. A: No, it is discovered from Argo.
3. `APPLICATION_VERSIONS` ?
   1. Without it, only topology and pipeline are generated.
   2. With it, all contexts are generated.
      1. If `OPERATION_TYPE: !CLEAN`, `APPLICATION_VERSIONS` is mandatory.
   3. Only in NoCMDB.
4. Who checks out the ES repository, and when?
   1. argo dpg
5. How do we change the BG state in the ES?
   1. **The state is not stored in the ES yet.** The plan is to move to a unified topology outside the ES.
      Therefore, state operations do not call the calculator (see 1.15).
6. How do we process a `COMMIT` BG operation? Do we clean up legacy namespaces?
   1. No, a commit only changes the state.
7. Do we add BG-specific filters based on `BG_NS_TARGET` and state files to `generate_deployment_plan`?
   1. No.

## AI

1. [phase2] Consider create_if_not_exist | replace strategies for appregdef processing
2. [phase2] Design integration with the central appregdef storage
3. [phase2] Design SAVE_ARTIFACTS_STRATEGY
    1. save env_instance/ES to a job artifact on SAVE_ALL
4. Design `git_commit`
    1. Depending on `PIPELINE_TYPE` and `SAVE_ARTIFACTS_STRATEGY`, commit env_instance/ES or not
5. After the flow is finalized analyze the flow for optimization
6. State file from New Look

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

## DD and ZIP layout

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

On `DEPLOY`: `generate_deployment_plan` builds the delta from the `APPLICATION_VERSIONS` input, then
`merge_deployment_plan` merges the delta onto the repository full plan and commits the result. On `CLEAN` there is
no delta and no merge (see Removal on clean below).

### Merge algorithm

Each operation merges its delta plan with the repository full plan to produce the next full plan.

**Entry identity.** Two entries are the same deployment when they share `<app-name>` (from `version`) and
`namespace`. `generationType: UniqForVersion` adds `version` to the identity and `UniqForRun` adds `generationId`,
so under those modes a new version or run is a distinct entry rather than a replacement of the previous one.

**Merge rule.** A delta entry with no counterpart in the full plan is added. A delta entry that matches an existing
one is collapsed into a single entry whose `wave` is the higher of the two.

**Invariant.** The merge only adds entries and raises `wave`, it never removes. An entry present in the full plan
but absent from the delta is retained. This is the stale-app corner case.

### Removal on clean

`CLEAN` produces no delta and does not merge. Its inputs are the repository full plan and `NAMESPACE_NAMES`, the
namespaces being cleaned. Removal reuses the plan filter (#1682), which excludes entries via a `!`-prefixed token
over `namespace`. Each namespace in `NAMESPACE_NAMES` is passed as a `!<namespace>` token (whole namespace).
The filter is applied to the repository full plan and writes the reduced plan, which is committed. In short,
`filter(full plan, exclude NAMESPACE_NAMES)` produces the reduced full plan, rather than a merge. The filter also accepts
`!<component>` tokens for dropping specific applications, though `CLEAN` currently passes whole namespaces only.

## `namespace-map.yml`

Map keyed by `deployPostfix`, covering all `deployPostfix`es of the environment. A non-BG `deployPostfix` maps to its
single namespace name. A BG `deployPostfix` maps to a per-side entry holding both the `origin` and `peer` namespace
names. The side is set at build from the rendered BG domain, so the map holds both sides and is built independently of
`BG_NS_TARGET`. Selecting the side for a bare BG `deployPostfix` happens at bind by `BG_NS_TARGET` (see
`generate_deployment_plan`, step 1.13).

```yaml
<deployPostfix>: <namespace-name>          # non-BG
<deployPostfix>:                           # BG
  origin: <namespace-name>
  peer: <namespace-name>
```

Example:

```yaml
# composite
core: env-1-core
oss: env-1-oss
bss:                       # BG domain member
  origin: env-1-bss-origin
  peer: env-1-bss-peer
```

## Instance pipeline parameters

### `APPLICATION_VERSIONS`

### CLUSTER_NAME

Cluster name of the target environment.

### ENVIRONMENT_NAME

Environment name of the target environment.

`CLUSTER_NAME` and `ENVIRONMENT_NAME` are the component parts of an `ENV_NAMES` entry. They are used,
alongside `ENV_NAMES`, for single-environment processing, and take precedence over it: when both are
passed, `ENV_NAMES` is ignored.

### DELTA_DEPLOY

### `OPERATION_TYPE`

`OPERATION_TYPE`: enum[ `CLEAN`, `DEPLOY`, `BGD` ]
default: `DEPLOY`

`BGD` marks any Blue-Green operation. The specific operation is carried by `BGD_OPERATION`.

### `BGD_OPERATION`

`BGD_OPERATION`: enum[ `warmup`, `commit`, `promote`, `rollback`, `init-domain` ]
default: None

Processed only when `OPERATION_TYPE: BGD`. Selects the Blue-Green operation.

### `PIPELINE_TYPE`

`PIPELINE_TYPE`: enum [ `GITLAB_DEPLOY`, `LEGACY` ]
default: `LEGACY`

### `BG_NS_TARGET`

`BG_NS_TARGET`: enum [ `ORIGIN`, `PEER` ]
default: None

1. Used with `ENV_TEMPLATE_VERSION`:
   1. `BG_NS_TARGET` determines which namespace receives the updated `bgNsArtifacts.origin` / `bgNsArtifacts.peer`
      template version.
2. Used at bind in `generate_deployment_plan` (step 1.13) to select the origin or peer namespace for a bare BG
   `deployPostfix`. `compute_namespace_map` does not consult it.
3. Required only when binding a bare BG `deployPostfix` (a `name:version` entry whose postfix is a BG member). Not
   needed for non-BG deploys, controller-only deploys, or entries given as `namespace:name:version`.

### `BG_STATE`

`BG_STATE`: the declarative target Blue-Green state, a full BGState object.
default: None

Processed only when `OPERATION_TYPE: BGD`. Only `BGState.originNamespace.state` and
`BGState.peerNamespace.state` are read. All other fields (`name`, `version`, `updateTime`,
`controllerNamespace`) are ignored. Consumed by `change_bg_state` to set the BG state files directly,
without validation.

```yaml
# full content, read surface is BGState.originNamespace.state and BGState.peerNamespace.state
BGState:
  controllerNamespace: dev-14-datahub
  originNamespace:
    name: dev-14-bss-origin
    state: active
    version: v1
  peerNamespace:
    name: dev-14-bss-peer
    state: idle
    version: null
  updateTime: 2026-08-17T11:14:31Z
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

- The App Def path becomes one of the inputs to `generate_deployment_plan`.
- It sets `generationType` from the `metadata.netcracker.com/argo-app-generation-type` attribute of the
  corresponding App Def. If the attribute is absent, it uses `UniqForApp`.
- It sets `generationId` to a value based on `generationType`: `""`, `<version>`, or UUID7.
- When needed, `generate_deployment_plan` generates a UUID7.

### ES Calc

- Reads `delta-deploy-plan.yml`. For `generationType != UniqForApp`, it inserts a subdirectory named
  `generationId` between `<application-name>` and `values`:

  ```text
  /environments/<cluster>/<env>/effective-set/deployment/<deployPostfix>/<application-name>/<generationId>/values/...
  ```

- For `UniqForApp`, no subdirectory is added. This matches the current behavior.
- `UniqForVersion`: the next operation replaces the previous directory. This matches the current behavior.
- `UniqForRun`: directories accumulate. Each run adds a new directory, and previous directories remain.
- The system makes the decision independently for each application.
- ES Calc does not define a retention policy.

## DD for `generate_argocd_repo`

**Option 1:**

Always download DD. Download ZIP only when SBOM is missing. The current flow downloads DD and ZIP when SBOM is missing.

(-) DD is downloaded unnecessarily in some cases.

**Option 2:**

In GOPA cases, `generate_argocd_repo` uses SBOM instead of DD.

(-) Requires a one-time change to `sbom_generation` (the `application/vnd.qubership.app.chart` extension).
(-) Future changes to `generate_argocd_repo` that require new DD fields may require changes to `sbom_generation`.
(-) Requires an SBOM regeneration procedure for a new SBOM specification version. If the specification version
    changes, regenerate the SBOM even when a cache exists.

**Option 3:**

Cache DD and SBOMs using GitLab features.

(-) A cache miss is highly likely because the cache is per runner node and has a retention policy.

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

#### 1.11 step `deploy_postfix_namespace_map`

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

#### 1.13 step `generate_deployment_plan`

Triggers:

- (`OPERATION_TYPE: DEPLOY` or `OPERATION_TYPE: CLEAN` or (`OPERATION_TYPE: BGD` and `BGD_OPERATION: warmup`)) and
- `PIPELINE_TYPE: GITLAB_DEPLOY`

Functions:

1. `run_generate_deployment_plan`
    - triggers:
      - `OPERATION_TYPE: DEPLOY`
    - input:
      - `APPLICATION_VERSIONS`
      - params.environment_id -> `build.env.FULL_ENV_NAME`
      - app defs
      - `namespace-map.yml`
      - `BG_NS_TARGET`
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

#### 1.14 step `env_build`

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

#### 1.15 step `generate_effective_set`

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
      - appreg defs
      - `delta-deploy-plan.yml` for `DEPLOY` and warmup (produced in 1.13); no plan for `CLEAN` (marker-driven)
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
      - `delta-deploy-plan.yml` for `DEPLOY` and warmup (produced in 1.13); no plan for `CLEAN` (marker-driven)
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

#### 1.16 step `git_commit`

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

#### 1.17 step `generate_argocd_repo` TO BE IMPLEMENTED. NOT IMPLEMENTED YET

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

#### 1.19 step `cmdb_import`

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

#### 1.20 step `postprocess`

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
