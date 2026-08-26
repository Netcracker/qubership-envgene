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
  - [Locations](#locations)
  - [Uniq names](#uniq-names)
    - [`generate_deployment_plan`](#generate_deployment_plan)
    - [ES Calc](#es-calc)
  - [DD for `generate_argocd_repo`](#dd-for-generate_argocd_repo)
  - [To deprecate](#to-deprecate)
  - [Flow](#flow)

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

The flow (jobs, steps, functions, and each step's trigger) is documented in
[flow](/docs/technical-design/instance-pipeline/flow.md).
