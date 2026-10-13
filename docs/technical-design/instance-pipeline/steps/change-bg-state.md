# `change_bg_state`

- [`change_bg_state`](#change_bg_state)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `change_bg_state` step writes BG state marker files
`environments/<cluster-name>/<env-name>/.origin-<state>` and
`environments/<cluster-name>/<env-name>/.peer-<state>`.

## Input parameters

| Parameter        | Source   | Required | Default | Values / format              | Effect                                                                     |
| ---------------- | -------- | -------- | ------- | ---------------------------- | -------------------------------------------------------------------------- |
| `ENV_NAMES`      | Pipeline | Yes      | None    | `<cluster-name>/<env-name>`  | Selects `environments/<cluster-name>/<env-name>/`                          |
| `PIPELINE_TYPE`  | Pipeline | Yes      | None    | `GITLAB_DEPLOY`              | Step runs only when value is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `BGD` |
| `OPERATION_TYPE` | Pipeline | Yes      | None    | `BGD`                        | Step runs only when value is `BGD`                                         |
| `BG_STATE`       | Pipeline | Yes      | None    | JSON with root key `BGState` | Supplies `originNamespace.state` and `peerNamespace.state`                 |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`
   and pipeline parameter `OPERATION_TYPE` is `BGD`. Otherwise the Instance pipeline skips this
   step.

2. **Parse target state**

   1. The step reads pipeline parameter `BG_STATE` as JSON.

   2. The step reads `BGState.originNamespace.state` and `BGState.peerNamespace.state` from the
      parsed JSON.

   3. The step ignores all other fields in `BG_STATE`, including `controllerNamespace`,
      `originNamespace.name`, `peerNamespace.name`, `version`, and `updateTime`.

3. **Remove previous marker files**

   1. The step deletes every file in `environments/<cluster-name>/<env-name>/` whose name matches
      pattern `.origin-*`.

   2. The step deletes every file in `environments/<cluster-name>/<env-name>/` whose name matches
      pattern `.peer-*`.

4. **Write new marker files**

   1. The step writes empty file
      `environments/<cluster-name>/<env-name>/.origin-<state>` where `<state>` is
      `BGState.originNamespace.state`.

   2. The step writes empty file
      `environments/<cluster-name>/<env-name>/.peer-<state>` where `<state>` is
      `BGState.peerNamespace.state`.

## Result

1. File `environments/<cluster-name>/<env-name>/.origin-<state>` exists and is empty.

2. File `environments/<cluster-name>/<env-name>/.peer-<state>` exists and is empty.

3. Previous `.origin-*` and `.peer-*` marker files in the same directory are removed.

## Error handling

**2a.** The step fails when pipeline parameter `BG_STATE` is absent or is not valid JSON. BG state
marker files are not written.

**2b.** The step fails when parsed JSON has no root key `BGState`. BG state marker files are not
written.

**2c.** The step fails when `BGState.originNamespace.state` or `BGState.peerNamespace.state` is
absent. BG state marker files are not written.

## Example

- [`.origin-active`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/.origin-active)
- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
- [`bg_domain.yml.j2`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd/bg_domain.yml.j2)

## Related documentation

- [BG State Files](/docs/envgene-objects.md#bg-state-files)
- [`warmup`](/docs/technical-design/instance-pipeline/steps/warmup.md)
