# `generate_effective_set`

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

The `generate_effective_set` step writes the Effective Set under
`environments/<cluster-name>/<env-name>/effective-set/`.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `ENV_NAMES` | Pipeline | Yes | None | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/` |
| `PIPELINE_TYPE` | Pipeline | Yes | None | `GITLAB_DEPLOY` | Selects GitLab deploy Effective Set path |
| `OPERATION_TYPE` | Pipeline | Yes | None | `DEPLOY`, `CLEAN`, `BGD` | Selects deploy, clean, or BGD warmup generation path |
| `BGD_OPERATION` | Pipeline | Conditional | None | `warmup` | With `OPERATION_TYPE: BGD`, only `warmup` triggers this step under `GITLAB_DEPLOY` |
| `GENERATE_EFFECTIVE_SET` | Pipeline | No | `false` | `true`, `false` | When `true`, step runs even outside `GITLAB_DEPLOY` deploy/clean/warmup triggers |
| `EFFECTIVE_SET_CONFIG` | Pipeline | No | None | JSON config | Passes extra Calculator CLI arguments |
| `CUSTOM_PARAMS` | Pipeline | No | None | JSON-in-string | Injects session-scoped parameters into the Effective Set |
| `DEPLOYMENT_SESSION_ID` | Pipeline | No | generated UUID | string | Passed to Calculator CLI as extra parameter |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `GENERATE_EFFECTIVE_SET` is `true`.
   Otherwise the Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is
   `GITLAB_DEPLOY` and pipeline parameter `OPERATION_TYPE` is `DEPLOY` or `CLEAN`. Otherwise the
   Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`,
   pipeline parameter `OPERATION_TYPE` is `BGD`, and pipeline parameter `BGD_OPERATION` is
   `warmup`. Otherwise the Instance pipeline skips this step.

2. **Prepare credentials, parameters, and SBOM inputs**

   1. The step decrypts credential files under
      `environments/<cluster-name>/<env-name>/Credentials/`.

   2. The step validates credential files.

   3. The step validates Environment ParameterSet files.

   4. The step runs SBOM retention policy processing when configured.

   5. When SBOM download plugins are installed, the step downloads SBOM artifacts for deploy-plan
      delta entries on `OPERATION_TYPE: DEPLOY` and BGD warmup. On `OPERATION_TYPE: CLEAN` the step
      skips SBOM download.

3. **Select Effective Set input on GITLAB_DEPLOY**

   1. When pipeline parameter `OPERATION_TYPE` is `CLEAN`, the step selects Calculator CLI invocation
      without deploy-plan file path.

   2. When pipeline parameter `OPERATION_TYPE` is `DEPLOY`, the step reads deploy-plan delta from
      file `environments/<cluster-name>/<env-name>/Inventory/delta-deploy-plan.yml` loaded into
      pipeline context by step `process_deployment_plan`.

   3. When pipeline parameter `OPERATION_TYPE` is `BGD` and pipeline parameter `BGD_OPERATION` is
      `warmup`, the step reads deploy-plan delta from file
      `Inventory/delta-deploy-plan.yml` written by step `warmup`.

4. **Prepare Effective Set workspace on DEPLOY and warmup**

   1. The step reads deploy-plan delta entries.

   2. For each delta entry with generation type `UNIQ_FOR_RUN` or `UNIQ_FOR_VERSION`, the step
      temporarily moves matching application directories from `effective-set/deployment/` and
      `effective-set/runtime/` to a temporary save location.

   3. The step deletes directory `environments/<cluster-name>/<env-name>/effective-set/`.

   4. The step restores saved application directories from the temporary save location into the
      new empty `effective-set/` tree.

   5. For each delta entry with generation type `UNIQ_FOR_VERSION`, the step deletes version-scoped
      subdirectories under matching application paths before regeneration.

5. **Invoke Calculator CLI**

   1. On `OPERATION_TYPE: DEPLOY` or BGD warmup, the step invokes Calculator CLI with environment id
      `<cluster-name>/<env-name>`, output path `effective-set/`, registry file
      `configuration/registry.yml`, SBOM path `sboms/`, and deploy-plan path
      `Inventory/delta-deploy-plan.yml`.

   2. On `OPERATION_TYPE: CLEAN`, the step invokes Calculator CLI with environment id
      `<cluster-name>/<env-name>` and output path `effective-set/` without deploy-plan file path.

   3. When pipeline parameter `EFFECTIVE_SET_CONFIG` is set, the step appends configured extra CLI
      arguments.

   4. When pipeline parameter `DEPLOYMENT_SESSION_ID` is set, the step passes it as an extra CLI
      parameter.

   5. When pipeline parameter `CUSTOM_PARAMS` is set, the step passes it to Calculator CLI as
      custom parameters.

6. **Finalize credentials**

   1. The step deletes legacy file `Inventory/solution-descriptor/delta_sd.yaml` when present.

   2. The step re-encrypts credential files under
      `environments/<cluster-name>/<env-name>/Credentials/`.

## Result

1. On `OPERATION_TYPE: DEPLOY` or BGD warmup, directory
   `environments/<cluster-name>/<env-name>/effective-set/` is regenerated from deploy-plan delta
   entries. Previous Effective Set content is removed except temporarily saved
   `UNIQ_FOR_RUN` and `UNIQ_FOR_VERSION` application directories restored before CLI invocation.

2. On `OPERATION_TYPE: CLEAN`, directory
   `environments/<cluster-name>/<env-name>/effective-set/` is updated by Calculator CLI clean
   processing without a deploy-plan input file.

3. Subdirectories `effective-set/topology/`, `effective-set/pipeline/`,
   `effective-set/deployment/`, `effective-set/runtime/`, and `effective-set/cleanup/` contain
   generated artifacts for the processed operation.

## Error handling

**3a.** The step fails on `OPERATION_TYPE: DEPLOY` when file `Inventory/delta-deploy-plan.yml` is
missing. The Effective Set is not generated.

**3b.** The step fails on BGD warmup when file `Inventory/delta-deploy-plan.yml` is missing. The
Effective Set is not generated.

**4a.** The step fails when credential validation fails. The Effective Set is not generated.

**4b.** The step fails when parameter validation fails. The Effective Set is not generated.

**5a.** The step fails when Calculator CLI exits with an error. The Effective Set is not generated.

## Example

- [`deploy-plan.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/deploy-plan.yml)
- [`effective-set/runtime/mapping.yaml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/effective-set/runtime/mapping.yaml)
- [`deploy-descriptor.yaml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/effective-set/deployment/bss-origin/bssapp/values/deploy-descriptor.yaml)

## Related documentation

- [Effective Set Generation](/docs/features/effective-set-generation.md)
- [`process_deployment_plan`](/docs/technical-design/instance-pipeline/process-deployment-plan.md)
- [`warmup`](/docs/technical-design/instance-pipeline/warmup.md)
