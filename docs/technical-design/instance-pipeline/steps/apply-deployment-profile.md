# `apply_deployment_profile`

- [`apply_deployment_profile`](#apply_deployment_profile)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Repository inputs](#repository-inputs)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `apply_deployment_profile` step creates or updates
`environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<deploy-postfix>-profile-override.yml`
with the `PROFILE` baseline of each deployed application, and references it in
`envTemplate.envSpecificResourceProfiles`. For the concept, see
[Selecting a profile at deployment](/docs/features/resource-profile.md#selecting-a-profile-at-deployment).

- **Runs when**: `OPERATION_TYPE` is `DEPLOY`, `PROFILE` is set and not empty, and, at `PIPELINE_TYPE: LEGACY`,
  `SD_VERSION` or `SD_DATA` is set, `ENV_BUILDER` is `true`, and `GENERATE_EFFECTIVE_SET` is `true`. Otherwise the
  Instance pipeline skips the step and logs a warning when `PROFILE` is set.
- **Used by**: [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md).

## Input parameters

| Parameter                                                                                | Source   | Required | Default  | Values / format             | Effect                                                                                    |
| ---------------------------------------------------------------------------------------- | -------- | -------- | -------- | --------------------------- | ----------------------------------------------------------------------------------------- |
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)                           | Pipeline | Yes      | None     | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/`                                         |
| [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type)                   | Pipeline | No       | `LEGACY` | `GITLAB_DEPLOY`, `LEGACY`   | Selects the file the step reads the deployed applications from                            |
| [`OPERATION_TYPE`](/docs/instance-pipeline-parameters.md#operation_type)                 | Pipeline | No       | `DEPLOY` | `DEPLOY`                    | The step runs only when value is `DEPLOY`                                                 |
| [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)                               | Pipeline | No       | None     | Baseline name               | The step runs only when set and not empty                                                 |
| [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version)                         | Pipeline | No       | None     | `<application>:<version>`   | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_DATA` are both not set    |
| [`SD_DATA`](/docs/instance-pipeline-parameters.md#sd_data)                               | Pipeline | No       | None     | SD content in JSON          | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_VERSION` are both not set |
| [`ENV_BUILDER`](/docs/instance-pipeline-parameters.md#env_builder)                       | Pipeline | No       | `false`  | `true`, `false`             | At `PIPELINE_TYPE: LEGACY`, the step is skipped when not `true`                           |
| [`GENERATE_EFFECTIVE_SET`](/docs/instance-pipeline-parameters.md#generate_effective_set) | Pipeline | No       | `false`  | `true`, `false`             | At `PIPELINE_TYPE: LEGACY`, the step is skipped when not `true`                           |

## Repository inputs

| File                                                                                                              | Object                                                              | What the step uses                                                                                       |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`                                          | Deployment plan delta of the run                                    | `version`, `deployPostfix`, `namespace` of each entry. Written earlier in the same run and not committed |
| `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`                                                | Full deployment plan                                                | The same fields. Only at `PIPELINE_TYPE: LEGACY` when the delta has no entries                           |
| `environments/<cluster-name>/<env-name>/bg_domain.yml`                                                            | [BG Domain](/docs/envgene-objects.md#bg-domain)                     | `originNamespace.name`, `peerNamespace.name`. Only when the file exists                                  |
| `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`                                             | [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) | `envTemplate.envSpecificResourceProfiles`                                                                |
| `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<deploy-postfix>-profile-override.yml`        | PROFILE override                                                    | `applications[].name`, `applications[].baseline`. Only when the file exists                              |

## Processing flow

1. **Read the selected profile**

   1. The step reads `PROFILE` without leading and trailing spaces as **selected baseline**.

2. **Collect the deployed applications**

   1. The step reads the entries of `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`.

   2. When `PIPELINE_TYPE` is `LEGACY` and `delta-deploy-plan.yml` has no entries, the step reads the entries of
      the full deployment plan `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`.

   3. For each entry, the step takes the application name from `version`, the part before `:`.

   4. For each entry, the step takes `deployPostfix` and `namespace`.

3. **Determine `<deploy-postfix>` and `<namespace-folder-name>` of each application**

   1. The step takes entry `deployPostfix` without a trailing `-origin` or `-peer` as `<deploy-postfix>`, the
      name part of the PROFILE override.

   2. The step takes `<deploy-postfix>` as `<namespace-folder-name>`, the key of the Namespace in
      `envTemplate.envSpecificResourceProfiles`.

   3. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists and entry `namespace` equals
      `originNamespace.name`, the step adds `-origin` to `<namespace-folder-name>`.

   4. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists and entry `namespace` equals
      `peerNamespace.name`, the step adds `-peer` to `<namespace-folder-name>`.

   5. The step groups the application names by `<deploy-postfix>` and `<namespace-folder-name>` as
      **deployed applications**.

4. **Write the PROFILE override**

   For each `<deploy-postfix>` in **deployed applications**:

   1. When the file
      `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<deploy-postfix>-profile-override.yml`
      does not exist:
      1. The step creates the file with a header comment: the file is generated by EnvGene from `PROFILE`, with a
         link to [Selecting a profile at deployment](/docs/features/resource-profile.md#selecting-a-profile-at-deployment).
      2. The step sets `name` in the file to `<deploy-postfix>-profile-override`.

   2. When the file exists, the step changes it in place.

   3. For each application of `<deploy-postfix>`, when the file has an `applications[]` entry with the same
      `name`, the step sets its `baseline` to **selected baseline**.

   4. For each application of `<deploy-postfix>`, when the file has no such entry, the step adds an entry with
      `name` and `baseline`.

   The other `applications[]` entries stay unchanged.

5. **Reference the PROFILE override**

   For each `<namespace-folder-name>` in **deployed applications**, the step reads Environment Inventory
   `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>`:

   1. When the key is not set, the step sets it to `<deploy-postfix>-profile-override`.

   2. When the key is a string other than `<deploy-postfix>-profile-override`, the step replaces it with a list:
      the string, then `<deploy-postfix>-profile-override`.

   3. When the key is a list without `<deploy-postfix>-profile-override`, the step adds
      `<deploy-postfix>-profile-override` to the end of the list.

   4. When the key is a list with `<deploy-postfix>-profile-override` not as the last item, the step moves it to
      the end of the list.

   5. When the key already references `<deploy-postfix>-profile-override` as its only value or last item, the step
      changes nothing.

   The other keys of `envTemplate.envSpecificResourceProfiles` and the files they reference stay unchanged.

## Result

1. Each `<deploy-postfix>` the run deploys to has a PROFILE override that sets `applications[].baseline` to
   **selected baseline** for every deployed application. The origin and peer Namespaces of a Blue-Green pair share
   one PROFILE override.

2. `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>` references the PROFILE override as its last
   item.

3. Other Resource Profile Overrides are unchanged.

A repeated run with the same `PROFILE` and the same deployed applications produces no change.

## Error handling

The step writes to the repository only in blocks 4 and 5. The
[`git_commit`](/docs/technical-design/instance-pipeline/flow.md) step does not run after a failure, so no change
from this run is committed. At `PIPELINE_TYPE: LEGACY`, when `ENV_NAMES` lists several environments, the step runs
for each environment separately. An environment where the step fails commits nothing.

The name `<deploy-postfix>-profile-override` is reserved for the step. Do not create files with this name.

The step logs no warnings.

## Example

PROFILE override of Namespace `bss` after a run with `PROFILE: prod` that deploys `app-a` and `app-b`:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-profile-override.yml
# Generated by EnvGene from the PROFILE pipeline parameter.
# See /docs/features/resource-profile.md#selecting-a-profile-at-deployment
name: bss-profile-override
applications:
  - name: app-a
    baseline: prod
  - name: app-b
    baseline: prod
```

Reference of `bss` before and after the run, when `bss` references the shared override `bss-override`:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml, before
envTemplate:
  envSpecificResourceProfiles:
    bss: bss-override
```

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml, after
envTemplate:
  envSpecificResourceProfiles:
    bss:
      - bss-override
      - bss-profile-override
```

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md#selecting-a-profile-at-deployment)
- [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)
- [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)
- [ADR-0012](/docs/adr/0012-select-resource-profile-baseline-per-application-at-deployment.md)
- [Modern toolset flow](/docs/technical-design/instance-pipeline/flow.md#1141-step-apply_deployment_profile-to-be-implemented-not-implemented-yet)
