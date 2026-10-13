# `warmup`

- [`warmup`](#warmup)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `warmup` step copies the active BG Namespace into the candidate Namespace, updates
`Inventory/env_definition.yml` field `envTemplate.bgNsArtifacts`, and writes
`Inventory/delta-deploy-plan.yml` plus an updated `Inventory/deploy-plan.yml`.

## Input parameters

| Parameter        | Source   | Required | Default | Values / format             | Effect                                                                                                   |
| ---------------- | -------- | -------- | ------- | --------------------------- | -------------------------------------------------------------------------------------------------------- |
| `ENV_NAMES`      | Pipeline | Yes      | None    | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/`                                                        |
| `PIPELINE_TYPE`  | Pipeline | Yes      | None    | `GITLAB_DEPLOY`             | Step runs only when value is `GITLAB_DEPLOY`, `OPERATION_TYPE` is `BGD`, and `BGD_OPERATION` is `warmup` |
| `OPERATION_TYPE` | Pipeline | Yes      | None    | `BGD`                       | Step runs only when value is `BGD`                                                                       |
| `BGD_OPERATION`  | Pipeline | Yes      | None    | `warmup`                    | Step runs only when value is `warmup`                                                                    |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`,
   pipeline parameter `OPERATION_TYPE` is `BGD`, and pipeline parameter `BGD_OPERATION` is
   `warmup`. Otherwise the Instance pipeline skips this step.

2. **Resolve active side from state marker files**

   1. The step reads BG state marker files in `environments/<cluster-name>/<env-name>/`.

   2. When no `.origin-*` and no `.peer-*` marker files exist, the step treats origin role state as
      `active` and peer role state as none.

   3. When multiple marker files exist for the same role, the step fails (2a).

   4. The step selects active Namespace role as `origin` when origin role state is `active`,
      otherwise `peer`.

   5. The step selects candidate Namespace role as the other BG side.

3. **Resolve active and candidate Namespaces**

   1. The step reads file `environments/<cluster-name>/<env-name>/bg_domain.yml`.

   2. The step lists Namespace directories under
      `environments/<cluster-name>/<env-name>/Namespaces/` and assigns each Namespace role by
      comparing `namespace.yml` field `name` with `bg_domain.yml` fields
      `originNamespace.name` and `peerNamespace.name`.

   3. The step selects the Namespace whose role matches the active role as the active Namespace.

   4. The step selects the Namespace whose role matches the candidate role as the candidate
      Namespace.

   5. When either Namespace is missing, the step fails (3a).

4. **Copy candidate Namespace content**

   1. The step deletes directory `environments/<cluster-name>/<env-name>/Namespaces/<candidate-folder>/`.

   2. The step copies directory
      `environments/<cluster-name>/<env-name>/Namespaces/<active-folder>/` recursively to the
      candidate Namespace directory, including nested `Applications/` content.

   3. The step reads copied file
      `environments/<cluster-name>/<env-name>/Namespaces/<candidate-folder>/namespace.yml`.

   4. The step sets field `name` in the copied `namespace.yml` to the candidate Namespace name
      from `bg_domain.yml`.

   5. The step writes updated `namespace.yml` back to the candidate Namespace directory.

5. **Sync template artifact versions**

   1. The step reads Environment Inventory `envTemplate.bgNsArtifacts` from file
      `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`.

   2. When `envTemplate.bgNsArtifacts` is absent, the step skips artifact sync.

   3. When the active-side key is absent from `envTemplate.bgNsArtifacts`, the step skips artifact
      sync.

   4. When `envTemplate.bgNsArtifacts` is present and contains the active-side key, the step copies
      the active-side artifact value to the candidate-side key.

   5. The step writes updated `env_definition.yml`.

6. **Build warmup deploy-plan delta**

   Delegates to [`process_deployment_plan` - `create_dp_for_warmup`](/docs/technical-design/instance-pipeline/steps/process-deployment-plan.md#warmup-deploy-plan-delta-create_dp_for_warmup).

## Result

1. Directory `environments/<cluster-name>/<env-name>/Namespaces/<candidate-folder>/` contains a copy
   of the active Namespace content. File `namespace.yml` field `name` names the candidate
   Namespace.

2. File `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` field
   `envTemplate.bgNsArtifacts` reflects the active-side artifact on the candidate side when sync
   ran in step 5.

3. Deploy-plan results are described in
   [`process_deployment_plan` - `create_dp_for_warmup`](/docs/technical-design/instance-pipeline/steps/process-deployment-plan.md#warmup-deploy-plan-delta-create_dp_for_warmup).

## Error handling

**2a.** The step fails when multiple `.origin-*` or multiple `.peer-*` marker files exist in
`environments/<cluster-name>/<env-name>/`. Warmup outputs are not written.

**3a.** The step fails when the active or candidate Namespace directory is missing, or when
`namespace.yml` is missing under either Namespace. Warmup outputs are not written.

## Example

- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
- [`deploy-plan.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/deploy-plan.yml)
- [`bss-origin/namespace.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Namespaces/bss-origin/namespace.yml)
- [`bss-peer/namespace.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Namespaces/bss-peer/namespace.yml)

## Related documentation

- [`change_bg_state`](/docs/technical-design/instance-pipeline/steps/change-bg-state.md)
- [`process_deployment_plan`](/docs/technical-design/instance-pipeline/steps/process-deployment-plan.md)
- [`generate_effective_set`](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md)
