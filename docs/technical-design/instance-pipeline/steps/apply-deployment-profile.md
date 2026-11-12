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

The `apply_deployment_profile` step sets or deletes the baseline of each deployed application in the
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
| [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import)       | Pipeline | No       | `false`  | `true`, `false`                                | When `true`, the step fails                                                               |
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

   3. When `CMDB_IMPORT` is `true`, the step fails.

2. **Collect the deployed applications**

   1. The step reads the entries of `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml`.

   2. When `PIPELINE_TYPE` is `LEGACY` and `delta-deploy-plan.yml` has no entries, the step reads the entries of
      `environments/<cluster-name>/<env-name>/Inventory/deploy-plan.yml` instead. The delta is empty when the run
      replaces the Solution Descriptor or creates the first one.

   3. For each entry, the step takes the application name from `version`, the part before `:`.

   4. For each entry, the step takes `deployPostfix` and `namespace`.

3. **Determine `<namespace-folder-name>` of each application**

   1. The step takes entry `deployPostfix` as `<namespace-folder-name>`, the key of the Namespace in
      `envTemplate.envSpecificResourceProfiles`.

   2. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists, entry `namespace` equals
      `originNamespace.name`, and `<namespace-folder-name>` does not end with `-origin`, the step adds `-origin`.

   3. When `environments/<cluster-name>/<env-name>/bg_domain.yml` exists, entry `namespace` equals
      `peerNamespace.name`, and `<namespace-folder-name>` does not end with `-peer`, the step adds `-peer`.

   4. The step groups the application names by `<namespace-folder-name>` as **deployed applications**.

4. **Find the override of each `<namespace-folder-name>`**

   For each `<namespace-folder-name>` in **deployed applications**:

   1. The step reads Environment Inventory `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>`.

   2. When the key is not set, the Namespace has no override. The step skips substeps 3 to 7 for this
      `<namespace-folder-name>`.

   3. The step takes the value of the key as **override name**.

   4. The step searches for file `<override name>.yml` or `<override name>.yaml` in this order and takes the first
      match as **override file**:
      1. `environments/<cluster-name>/<env-name>/Inventory/`
      2. `environments/<cluster-name>/`
      3. `environments/`

   5. When no **override file** is found, the step fails.

   6. When **override file** is in `environments/<cluster-name>/` or `environments/`, the step fails (the file is
      shared with other environments).

   7. When another key of `envTemplate.envSpecificResourceProfiles` has the value **override name**, the step fails
      (the file is shared with another Namespace).

5. **Check the deployed Namespaces**

   The step runs this block when **selected baseline** is not `reset`. For each `<namespace-folder-name>`:

   1. When the Namespace has no override and a key of `envTemplate.envSpecificResourceProfiles` has the value
      `<namespace-folder-name>-resource-profile-override`, the step fails. Another Namespace uses this file.

6. **Set the baseline**

   The step runs this block when **selected baseline** is not `reset`. For each `<namespace-folder-name>`:

   1. When the Namespace has no override, the step creates file
      `environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<namespace-folder-name>-resource-profile-override.yml`.
      When a file with this name exists, the step replaces it.

   2. When the step created the file, it sets `name` in the file to
      `<namespace-folder-name>-resource-profile-override`.

   3. When the step created the file, it sets `envTemplate.envSpecificResourceProfiles.<namespace-folder-name>` to
      `<namespace-folder-name>-resource-profile-override` in `env_definition.yml`.

   4. The step writes to the created file or to **override file**.

   5. For each application of `<namespace-folder-name>`, when the file has an `applications[]` entry with the same
      `name`, the step sets its `baseline` to **selected baseline**.

   6. For each application of `<namespace-folder-name>`, when the file has no such entry, the step adds an entry
      with `name` and `baseline`.

7. **Reset the baseline**

   The step runs this block when **selected baseline** is `reset`. For each `<namespace-folder-name>`:

   1. When the Namespace has no override, the step skips it and logs it.

   2. For each application of `<namespace-folder-name>`, the step deletes `baseline` from its `applications[]`
      entry in **override file**.

   3. When the entry has no `services` left, the step deletes the entry.

In blocks 6 and 7, the other `applications[]` entries, `services`, and the top-level `baseline` stay unchanged.

## Result

1. When **selected baseline** is not `reset`, each Namespace the run deploys to references an override in
   `environments/<cluster-name>/<env-name>/Inventory/`. The override sets `applications[].baseline` to
   **selected baseline** for every deployed application of the Namespace.

2. A created override is named `<namespace-folder-name>-resource-profile-override`, and
   `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` references it.

3. When `inventory.config.mergeEnvSpecificResourceProfiles` is `false`, a created override replaces the template
   override of the Namespace during [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md).

4. When **selected baseline** is `reset`, the overrides set no `baseline` for the deployed applications.

5. Overrides of Namespaces the run does not deploy to are unchanged.

A repeated run with the same `PROFILE` and the same deployed applications produces no change.

## Error handling

The step writes to the repository only in blocks 6 and 7. A failure in blocks 1 to 5 leaves the repository
unchanged. The [`git_commit`](/docs/technical-design/instance-pipeline/flow.md) step does not run after a failure,
so no change from this run is committed. When `ENV_NAMES` lists several environments, the step runs for each
environment separately. An environment where the step fails commits nothing.

**1a.** The step fails when `PROFILE` is not one of `dev`, `prod`, `dev-ha`, `prod-nonha`, `reset`.

**1b.** The step fails when `CMDB_IMPORT` is `true`. CMDB import rejects an application-level baseline.

**4a.** The step fails when no file matches the name in
`envTemplate.envSpecificResourceProfiles.<namespace-folder-name>`.

**4b.** The step fails when **override file** is in `environments/<cluster-name>/` or `environments/`. The error
names the file and asks to reference an override in `environments/<cluster-name>/<env-name>/Inventory/` for
`<namespace-folder-name>`.

**4c.** The step fails when several keys of `envTemplate.envSpecificResourceProfiles` have the value
**override name**. The error names the file and the keys.

**5a.** The step fails when it must create an override and another key of
`envTemplate.envSpecificResourceProfiles` references `<namespace-folder-name>-resource-profile-override`. The error
names the file and the key.

The name `<namespace-folder-name>-resource-profile-override` is reserved for the step. Do not create files with this
name.

The step logs no warnings.

## Example

Override of Namespace `bss` after a run with `PROFILE: prod` that deploys `app-a` and `app-b`:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-resource-profile-override.yml
name: bss-resource-profile-override
applications:
  - name: app-a
    baseline: prod
  - name: app-b
    baseline: prod
```

Override of Blue-Green Namespace `bss-peer` after a run with `PROFILE: prod` that deploys `app-a`:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/bss-peer-resource-profile-override.yml
name: bss-peer-resource-profile-override
applications:
  - name: app-a
    baseline: prod
```

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md#selecting-a-profile-at-deployment)
- [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)
- [`PROFILE`](/docs/instance-pipeline-parameters.md#profile)
- [ADR-0012](/docs/adr/0012-select-resource-profile-baseline-per-application-at-deployment.md)
- [Modern toolset flow](/docs/technical-design/instance-pipeline/flow.md#1141-step-apply_deployment_profile-to-be-implemented-not-implemented-yet)
