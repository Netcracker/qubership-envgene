# `apply_deployment_profile` (version 2: deployment override)

- [`apply_deployment_profile` (version 2: deployment override)](#apply_deployment_profile-version-2-deployment-override)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Repository inputs](#repository-inputs)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `apply_deployment_profile` step sets the baseline of each deployed application in the deployment override of its
Namespace:
`environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<namespace-folder-name>-deployment-override.yml`.
The deployment override is a Resource Profile Override that only the step writes.

- **Runs when**: `OPERATION_TYPE` is `DEPLOY`, `PROFILE` is set and not empty, and, at `PIPELINE_TYPE: LEGACY`,
  `SD_VERSION` or `SD_DATA` is set. Otherwise the Instance pipeline skips the step. When `PROFILE` is set and the
  step is skipped, the Instance pipeline logs a warning that `PROFILE` has no effect.
- **Used by**:
  - [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md) combines the template and the
    environment-specific overrides of each Namespace, then applies the deployment override on top. For a Namespace
    with a deployment override, `env_build` writes the result to
    `Profiles/<namespace-folder-name>-deployment-override.yml` and sets it in `profile.name` of the Namespace.
  - [`generate_effective_set`](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md) applies
    the application-level baseline to the services of each application.

## Input parameters

| Parameter                                                                | Source   | Required | Default  | Values / format             | Effect                                                                                    |
| ------------------------------------------------------------------------ | -------- | -------- | -------- | --------------------------- | ----------------------------------------------------------------------------------------- |
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)           | Pipeline | Yes      | None     | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/`                                         |
| [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type)   | Pipeline | No       | `LEGACY` | `GITLAB_DEPLOY`, `LEGACY`   | Selects the file the step reads the deployed applications from                            |
| [`OPERATION_TYPE`](/docs/instance-pipeline-parameters.md#operation_type) | Pipeline | No       | `DEPLOY` | `DEPLOY`                    | The step runs only when value is `DEPLOY`                                                 |
| [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)               | Pipeline | No       | None     | Baseline name               | The step runs only when set and not empty                                                 |
| [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version)         | Pipeline | No       | None     | `<application>:<version>`   | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_DATA` are both not set    |
| [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import)       | Pipeline | No       | `false`  | `true`, `false`             | When `true`, the step fails                                                               |
| [`SD_DATA`](/docs/instance-pipeline-parameters.md#sd_data)               | Pipeline | No       | None     | SD content in JSON          | At `PIPELINE_TYPE: LEGACY`, the step is skipped when it and `SD_VERSION` are both not set |

## Repository inputs

| File                                                                                                                 | Object                                          | What the step uses                                                                                       |
| -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`                                             | Deployment plan delta of the run                | `version`, `deployPostfix`, `namespace` of each entry. Written earlier in the same run and not committed |
| `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`                                                   | Full deployment plan                            | The same fields. Only at `PIPELINE_TYPE: LEGACY` when the delta has no entries                           |
| `environments/<cluster-name>/<env-name>/bg_domain.yml`                                                               | [BG Domain](/docs/envgene-objects.md#bg-domain) | `originNamespace.name`, `peerNamespace.name`. Only when the file exists                                  |
| `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<namespace-folder-name>-deployment-override.yml` | Deployment override                             | `applications[].name`, `applications[].baseline`. Only when the file exists                              |

## Processing flow

1. **Read the selected profile**

   1. The step reads `PROFILE` without leading and trailing spaces as **selected baseline**.

   2. When `CMDB_IMPORT` is `true`, the step fails.

2. **Collect the deployed applications**

   1. The step reads the entries of `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`.

   2. When `PIPELINE_TYPE` is `LEGACY` and `delta-deploy-plan.yml` has no entries, the step reads the entries of
      the full deployment plan `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml`.

   3. For each entry, the step takes the application name from `version`, the part before `:`.

   4. For each entry, the step takes `deployPostfix` and `namespace`.

3. **Determine `<namespace-folder-name>` of each application**

   1. The step takes entry `deployPostfix` as `<namespace-folder-name>`, the name of the Namespace folder.

   2. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists, entry `namespace` equals
      `originNamespace.name`, and `<namespace-folder-name>` does not end with `-origin`, the step adds `-origin`.

   3. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists, entry `namespace` equals
      `peerNamespace.name`, and `<namespace-folder-name>` does not end with `-peer`, the step adds `-peer`.

   4. The step groups the application names by `<namespace-folder-name>` as **deployed applications**.

4. **Write the deployment override**

   For each `<namespace-folder-name>` in **deployed applications**:

   1. When the file
      `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<namespace-folder-name>-deployment-override.yml`
      does not exist:
      1. The step creates the file.
      2. The step sets `name` in the file to `<namespace-folder-name>-deployment-override`.

   2. When the file exists, the step changes it in place.

   3. For each application of `<namespace-folder-name>`, when the file has an `applications[]` entry with the same
      `name`, the step sets its `baseline` to **selected baseline**.

   4. For each application of `<namespace-folder-name>`, when the file has no such entry, the step adds an entry
      with `name` and `baseline`.

   The other `applications[]` entries stay unchanged.

## Result

1. Each Namespace the run deploys to has a deployment override that sets `applications[].baseline` to
   **selected baseline** for every deployed application of the Namespace.

2. `env_definition.yml`, template overrides, and environment-specific overrides are unchanged.

A repeated run with the same `PROFILE` and the same deployed applications produces no change.

## Error handling

The step writes to the repository only in block 4. A failure in blocks 1 to 3 leaves the repository unchanged. The
[`git_commit`](/docs/technical-design/instance-pipeline/flow.md) step does not run after a failure, so no change
from this run is committed. At `PIPELINE_TYPE: LEGACY`, when `ENV_NAMES` lists several environments, the step runs
for each environment separately. An environment where the step fails commits nothing.

**1a.** The step fails when `CMDB_IMPORT` is `true`. The error is `PROFILE and CMDB_IMPORT cannot be used
together`.

The name `<namespace-folder-name>-deployment-override` is reserved for the step. Do not create files with this name.

The step logs no warnings.

## Example

Deployment override of Namespace `bss` after a run with `PROFILE: prod` that deploys `app-a` and `app-b`:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-deployment-override.yml
name: bss-deployment-override
applications:
  - name: app-a
    baseline: prod
  - name: app-b
    baseline: prod
```

Result of `env_build` when `bss` references the shared override `bss-override` with baseline `dev`:

```yaml
# environments/cluster-01/env-01/Profiles/bss-deployment-override.yml
name: bss-deployment-override
baseline: dev
applications:
  - name: app-d
    services:
      - name: app-d-service
        parameters:
          - name: PROBE_STARTUP_TIMEOUT_SECONDS
            value: 5
  - name: app-a
    baseline: prod
  - name: app-b
    baseline: prod
```

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md#selecting-a-profile-at-deployment)
- [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)
- [ADR-0012](/docs/adr/0012-select-resource-profile-baseline-per-application-at-deployment.md)
- [Version 1: write into the environment-specific override](/docs/technical-design/instance-pipeline/steps/apply-deployment-profile.md)
