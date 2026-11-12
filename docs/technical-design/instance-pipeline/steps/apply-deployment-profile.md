# `apply_deployment_profile`

- [`apply_deployment_profile`](#apply_deployment_profile)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Repository inputs](#repository-inputs)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
    - [Single application, no override](#single-application-no-override)
    - [Several applications and Namespaces](#several-applications-and-namespaces)
    - [Blue-Green Namespace](#blue-green-namespace)
  - [Related documentation](#related-documentation)

## Description

The `apply_deployment_profile` step writes the `PROFILE` baseline for each deployed application into the
environment-specific Resource Profile Override of its Namespace, under
`environments/<cluster-name>/<env-name>/Inventory/`.

- **Runs when**: `OPERATION_TYPE` is `DEPLOY`, `PROFILE` is set and not empty, and, at `PIPELINE_TYPE: LEGACY`,
  `SD_VERSION` or `SD_DATA` is set. Otherwise the Instance pipeline skips the step and no override changes.
- **Used by**:
  - [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md) combines the updated overrides into
    the Resource Profile Override of each Namespace.
  - [`generate_effective_set`](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md) applies
    the application-level baseline to the services of each application.

  At `PIPELINE_TYPE: LEGACY`, `env_build` runs only with `ENV_BUILDER: true` and `generate_effective_set` only with
  `GENERATE_EFFECTIVE_SET: true`. Without them, the Effective Set gets the stored baseline in the first later run
  that sets them.

## Input parameters

| Parameter                                                                | Source   | Required | Default  | Values / format                                | Effect                                                                                    |
| ------------------------------------------------------------------------ | -------- | -------- | -------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)           | Pipeline | Yes      | None     | `<cluster-name>/<env-name>`                    | Selects `environments/<cluster-name>/<env-name>/`                                         |
| [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type)   | Pipeline | No       | `LEGACY` | `GITLAB_DEPLOY`, `LEGACY`                      | Selects the file the step reads the deployed applications from                            |
| [`OPERATION_TYPE`](/docs/instance-pipeline-parameters.md#operation_type) | Pipeline | No       | `DEPLOY` | `DEPLOY`                                       | The step runs only when value is `DEPLOY`                                                 |
| [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)               | Pipeline | No       | None     | `dev`, `prod`, `dev-ha`, `prod-nonha`, `reset` | The step runs only when set and not empty. Another value fails the step                   |
| [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version)         | Pipeline | No       | None     | `<application>:<version>`                      | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_DATA` are both not set    |
| [`SD_DATA`](/docs/instance-pipeline-parameters.md#sd_data)               | Pipeline | No       | None     | SD content in JSON                             | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_VERSION` are both not set |

## Repository inputs

| File                                                                                                                                                                        | Object                                                                                                                    | What the step uses                                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`                                                                                                    | Deployment plan delta of the run                                                                                          | `version`, `deployPostfix`, `namespace` of each entry. Written earlier in the same run and not committed |
| `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`                                                                                                          | Full deployment plan                                                                                                      | The same fields. Only at `PIPELINE_TYPE: LEGACY` when the delta has no entries                           |
| `environments/<cluster-name>/<env-name>/bg_domain.yml`                                                                                                                      | [BG Domain](/docs/envgene-objects.md#bg-domain)                                                                           | `originNamespace.name`, `peerNamespace.name`. Only when the file exists                                  |
| `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`                                                                                                       | [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)                                                       | `envTemplate.envSpecificResourceProfiles`                                                                |
| `resource_profiles/`, `rp_override/`, `Profiles/`, `parameters/` under `environments/<cluster-name>/<env-name>/Inventory/`, `environments/<cluster-name>/`, `environments/` | [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override) | The file each referenced name resolves to. `name`, `applications[].name`, `applications[].baseline`      |

## Processing flow

1. **Read the selected profile**

   1. The step reads `PROFILE` without leading and trailing spaces as **selected baseline**.

   2. When **selected baseline** is not one of `dev`, `prod`, `dev-ha`, `prod-nonha`, `reset`, the step fails.
      Otherwise the step goes on. Value `reset` removes the application-level baseline.

2. **Collect the deployed applications**

   1. The step reads the entries of `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`.

   2. When `PIPELINE_TYPE` is `LEGACY` and `delta-deploy-plan.yml` has no entries, the step reads the entries of
      `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml` instead. Otherwise the step keeps the
      entries of `delta-deploy-plan.yml`. The delta is empty when the run replaces the Solution Descriptor or creates
      the first one.

   3. For each entry, the step takes the application name from `version`, the part before `:`, and takes
      `deployPostfix` and `namespace`.

3. **Determine `<namespace-folder-name>` of each application**

   1. The step takes entry `deployPostfix` as `<namespace-folder-name>`, the key of the Namespace in
      `envTemplate.envSpecificResourceProfiles`.

   2. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists and entry `namespace` equals
      `originNamespace.name`, the step adds suffix `-origin` to `<namespace-folder-name>`. When entry `namespace` equals
      `peerNamespace.name`, the step adds suffix `-peer`. When `<namespace-folder-name>` already ends with the suffix,
      the step does not add it again.

   3. The step groups the application names by `<namespace-folder-name>` as **deployed applications**.

4. **Find the override of each `<namespace-folder-name>`**

   For each `<namespace-folder-name>` in **deployed applications**:

   1. The step reads Environment Inventory `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>`.
      When it is not set, the Namespace has no override, and the step goes to block 5 or 6.

   2. The step searches for a file `<value>.yml` or `<value>.yaml` in directories `resource_profiles`,
      `rp_override`, `Profiles`, and `parameters`, including their subdirectories, first under
      `environments/<cluster-name>/<env-name>/Inventory/`, then under `environments/<cluster-name>/`, then under
      `environments/`. The step takes the first match as the found file. When no file matches, the step fails.

   3. When the found file is under `environments/<cluster-name>/<env-name>/Inventory/`, the override is in the
      environment. Otherwise the override is outside the environment.

5. **Set the baseline**

   The step runs this block when **selected baseline** is not `reset`. For each `<namespace-folder-name>`:

   1. When the Namespace has no override, the step creates file
      `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<namespace-folder-name>-resource-profile-override.yml`
      with `name` `<namespace-folder-name>-resource-profile-override`.

   2. When the override is outside the environment, the step creates the same file with the content of the found
      file and `name` `<namespace-folder-name>-resource-profile-override`. The found file stays unchanged.

   3. When the step created a file, it sets `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>` to
      `<namespace-folder-name>-resource-profile-override` in `env_definition.yml`. The rest of the file, including
      comments, stays unchanged.

   4. The step writes to the created file, or to the found file when the override is in the environment. For each
      application of `<namespace-folder-name>`, when the file has an `applications[]` entry with the same `name`, the
      step sets its `baseline` to **selected baseline**. Otherwise the step adds an entry with `name` and
      `baseline`.

   | Override                | Action                                                   |
   | ----------------------- | -------------------------------------------------------- |
   | None                    | Create a file and reference it                           |
   | In the environment      | Update the found file                                    |
   | Outside the environment | Copy the found file, reference the copy, update the copy |

6. **Reset the baseline**

   The step runs this block when **selected baseline** is `reset`. For each `<namespace-folder-name>`:

   1. When the Namespace has no override, or the override is outside the environment, the step logs it and changes
      nothing.

   2. When the override is in the environment, the step deletes `baseline` from the `applications[]` entry of each
      application of `<namespace-folder-name>`. The step deletes an entry that has no `services` left.

   3. The file and its reference in `env_definition.yml` stay, even when `applications` is empty.

   In blocks 5 and 6, the other `applications[]` entries, `services`, and the top-level `baseline` stay unchanged.

## Result

1. When `PROFILE` is a baseline, each Namespace the run deploys to references an environment-specific Resource
   Profile Override under `environments/<cluster-name>/<env-name>/Inventory/`. The override sets
   `applications[].baseline` to the value of `PROFILE` for every deployed application of the Namespace.

2. A created or copied override is named `<namespace-folder-name>-resource-profile-override`, and
   `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` references it.

3. When `PROFILE` is `reset`, the overrides in the environment set no `baseline` for the deployed applications.

4. Overrides of Namespaces the run does not deploy to, and overrides outside the environment, are unchanged.

5. A created override carries only application-level baselines. It does not change which side, Namespace or Cloud,
   the other applications of the Namespace resolve their profile from. See
   [Side selection](/docs/features/resource-profile.md#side-selection).

A repeated run with the same `PROFILE` and the same deployed applications produces no change.

## Error handling

The step writes to the repository only in blocks 5 and 6. A failure in blocks 1 to 4 leaves the repository unchanged.
The [`git_commit`](/docs/technical-design/instance-pipeline/flow.md) step does not run after a failure, so no change
from this run is committed.

**1a.** The step fails when `PROFILE` is not one of `dev`, `prod`, `dev-ha`, `prod-nonha`, `reset`. The step writes
nothing.

**4a.** The step fails when no file matches the name in
`envTemplate.envSpecificResourceProfiles.<namespace-folder-name>`.

The step logs a warning and continues in this case:

- Block 5, override outside the environment: the Namespace stops using the override from the cluster or global
  scope, so later changes to that file do not reach it. The warning names `<namespace-folder-name>`, the found file,
  and the new file.

## Example

The examples are illustrative. No sample set under `/docs/samples/` exercises this step. All examples use
environment `cluster-01/env-01` and `PROFILE: prod`.

### Single application, no override

Input:

```yaml
# environments/cluster-01/env-01/Inventory/delta-deploy-plan.yml
- wave: 0
  version: app-a:1.0.0
  deployPostfix: bss
  namespace: env-01-bss
  generationType: UniqForApp
  generationId: ""
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
```

Run:

1. **selected baseline** is `prod`.
2. The step takes `app-a`, `deployPostfix: bss`, `namespace: env-01-bss`.
3. `bg_domain.yml` does not exist, so `<namespace-folder-name>` is `bss`. **deployed applications** is `bss: [app-a]`.
4. `envTemplate.envSpecificResourceProfiles.bss` is not set, so the Namespace has no override.
5. The step creates the override and adds the reference.

Output:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-resource-profile-override.yml
name: bss-resource-profile-override
applications:
  - name: app-a
    baseline: prod
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
  envSpecificResourceProfiles:
    bss: bss-resource-profile-override
```

### Several applications and Namespaces

Input:

```yaml
# environments/cluster-01/env-01/Inventory/delta-deploy-plan.yml
- wave: 0
  version: app-a:1.0.0
  deployPostfix: bss
  namespace: env-01-bss
  generationType: UniqForApp
  generationId: ""
- wave: 0
  version: app-b:2.0.0
  deployPostfix: bss
  namespace: env-01-bss
  generationType: UniqForApp
  generationId: ""
- wave: 1
  version: app-c:3.0.0
  deployPostfix: core
  namespace: env-01-core
  generationType: UniqForApp
  generationId: ""
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
  envSpecificResourceProfiles:
    bss: env-01-bss-overrides
    core: core-common
```

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/env-01-bss-overrides.yml
name: env-01-bss-overrides
baseline: dev
applications:
  - name: app-a
    baseline: dev
  - name: app-d
    services:
      - name: app-d-service
        parameters:
          - name: MEMORY_LIMIT
            value: 2500Mi
```

```yaml
# environments/cluster-01/resource_profiles/core-common.yml
name: core-common
applications:
  - name: app-c
    services:
      - name: app-c-service
        parameters:
          - name: CPU_LIMIT
            value: "2"
```

Run:

1. **selected baseline** is `prod`.
2. The step takes three entries.
3. `bg_domain.yml` does not exist. **deployed applications** is `bss: [app-a, app-b]`, `core: [app-c]`.
4. `bss`: the found file is under `environments/cluster-01/env-01/Inventory/`, so the override is in the
   environment. `core`: the found file is under `environments/cluster-01/`, so the override is outside the
   environment.
5. The step updates `env-01-bss-overrides.yml`, creates `core-resource-profile-override.yml` from `core-common.yml`,
   and changes the reference for `core`. The step logs a warning for `core`.

Output:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/env-01-bss-overrides.yml
name: env-01-bss-overrides
baseline: dev
applications:
  - name: app-a
    baseline: prod
  - name: app-d
    services:
      - name: app-d-service
        parameters:
          - name: MEMORY_LIMIT
            value: 2500Mi
  - name: app-b
    baseline: prod
```

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/core-resource-profile-override.yml
name: core-resource-profile-override
applications:
  - name: app-c
    baseline: prod
    services:
      - name: app-c-service
        parameters:
          - name: CPU_LIMIT
            value: "2"
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
  envSpecificResourceProfiles:
    bss: env-01-bss-overrides
    core: core-resource-profile-override
```

`environments/cluster-01/resource_profiles/core-common.yml` stays unchanged.

### Blue-Green Namespace

The environment has Namespace folders `bss-origin` and `bss-peer`. The run deploys to the peer Namespace.

Input:

```yaml
# environments/cluster-01/env-01/Inventory/delta-deploy-plan.yml
- wave: 0
  version: app-a:1.1.0
  deployPostfix: bss
  namespace: env-01-bss-peer
  generationType: UniqForApp
  generationId: ""
```

```yaml
# environments/cluster-01/env-01/bg_domain.yml
name: env-01-bss-domain
type: bgdomain
originNamespace:
  name: env-01-bss-origin
  type: namespace
peerNamespace:
  name: env-01-bss-peer
  type: namespace
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
  envSpecificResourceProfiles:
    bss-origin: bss-origin-overrides
```

Run:

1. **selected baseline** is `prod`.
2. The step takes `app-a`, `deployPostfix: bss`, `namespace: env-01-bss-peer`.
3. `namespace` equals `peerNamespace.name`, so `<namespace-folder-name>` is `bss-peer`. **deployed applications** is
   `bss-peer: [app-a]`.
4. `envTemplate.envSpecificResourceProfiles.bss-peer` is not set, so the Namespace has no override.
5. The step creates the override and adds the reference. The override of `bss-origin` stays unchanged.

Output:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-peer-resource-profile-override.yml
name: bss-peer-resource-profile-override
applications:
  - name: app-a
    baseline: prod
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  environmentName: env-01
envTemplate:
  name: composite-prod
  artifact: project-env-template:1.0.0
  envSpecificResourceProfiles:
    bss-origin: bss-origin-overrides
    bss-peer: bss-peer-resource-profile-override
```

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md#selecting-a-profile-at-deployment)
- [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)
- [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)
- [ADR-0012](/docs/adr/0012-select-resource-profile-baseline-per-application-at-deployment.md)
- [Modern toolset flow](/docs/technical-design/instance-pipeline/flow.md#1141-step-apply_deployment_profile-to-be-implemented-not-implemented-yet)
