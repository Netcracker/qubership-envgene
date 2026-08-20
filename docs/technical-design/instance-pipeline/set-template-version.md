# `set_template_version`

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

The `set_template_version` step updates Environment Inventory field `envTemplate.artifact`,
`envTemplate.templateArtifact.artifact.version`, or `envTemplate.bgNsArtifacts` in file
`environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `ENV_NAMES` | Pipeline | Yes | None | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/` |
| `ENV_TEMPLATE_VERSION` | Pipeline | Yes | None | artifact coordinates | Step runs only when set; supplies the version value to write |
| `ENV_TEMPLATE_VERSION_UPDATE_MODE` | Pipeline | No | `PERSISTENT` | `PERSISTENT`, `TEMPORARY` | `PERSISTENT` writes the version to Inventory; `TEMPORARY` skips Inventory update |
| `BG_NS_TARGET` | Pipeline | No | None | `origin`, `peer` | Selects which `envTemplate` field receives the version |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `ENV_TEMPLATE_VERSION` is set.
   Otherwise the Instance pipeline skips this step.

2. **Read Environment Inventory**

   1. The step reads file `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`.

   2. The step validates that field `envTemplate` is present.

3. **Select update mode**

   1. The step reads pipeline parameter `ENV_TEMPLATE_VERSION_UPDATE_MODE`. When absent, the step
      defaults to `PERSISTENT`.

   2. When `ENV_TEMPLATE_VERSION_UPDATE_MODE` is `TEMPORARY`, the step writes field
      `generatedVersions.generateEnvironmentLatestVersion` with the applied version value. The
      step does not modify `envTemplate.artifact`, `envTemplate.templateArtifact`, or
      `envTemplate.bgNsArtifacts`. The step returns.

4. **Select target field by `BG_NS_TARGET`**

   1. The step reads pipeline parameter `BG_NS_TARGET`.

   2. When `BG_NS_TARGET` is absent or empty, the step selects the common artifact field as the
      write target. When `ENV_TEMPLATE_VERSION` contains `:`, the step writes field
      `envTemplate.artifact` and removes field `envTemplate.templateArtifact` when present.
      When `ENV_TEMPLATE_VERSION` does not contain `:`, the step writes field
      `envTemplate.templateArtifact.artifact.version`.

   3. When `BG_NS_TARGET` is `origin`, the step selects field
      `envTemplate.bgNsArtifacts.origin` as the write target. The step does not modify
      `envTemplate.artifact` or `envTemplate.templateArtifact`.

   4. When `BG_NS_TARGET` is `peer`, the step selects field
      `envTemplate.bgNsArtifacts.peer` as the write target. The step does not modify
      `envTemplate.artifact` or `envTemplate.templateArtifact`.

   5. When `BG_NS_TARGET` is set to a value other than `origin` or `peer`, the step fails (4a).

   6. When `envTemplate.bgNsArtifacts` is absent and `BG_NS_TARGET` is `origin` or `peer`, the
      step creates `envTemplate.bgNsArtifacts` and writes the selected key.

5. **Write Environment Inventory**

   1. The step writes the updated `envTemplate` to file
      `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`.

   2. The step replaces the previous file content.

## Result

1. On `ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT` without `BG_NS_TARGET`, file
   `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` contains the updated
   `envTemplate.artifact` or `envTemplate.templateArtifact.artifact.version`.

2. On `ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT` with `BG_NS_TARGET`, file
   `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` contains the updated
   `envTemplate.bgNsArtifacts.origin` or `envTemplate.bgNsArtifacts.peer`. Fields
   `envTemplate.artifact` and `envTemplate.templateArtifact` are unchanged.

3. On `ENV_TEMPLATE_VERSION_UPDATE_MODE: TEMPORARY`, file
   `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` contains updated field
   `generatedVersions.generateEnvironmentLatestVersion`. Fields `envTemplate.artifact`,
   `envTemplate.templateArtifact`, and `envTemplate.bgNsArtifacts` are unchanged.

## Error handling

**2a.** The step fails when field `envTemplate` is missing from
`environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`. The Inventory file is not
updated.

**4a.** The step fails when pipeline parameter `BG_NS_TARGET` is set to a value other than
`origin` or `peer`. The error names `BG_NS_TARGET` and the allowed values `origin` and `peer`.
The Inventory file is not updated.

**4b.** The step fails when `BG_NS_TARGET` is absent,
`ENV_TEMPLATE_VERSION` does not contain `:`, and field
`envTemplate.templateArtifact.artifact` is missing. The Inventory file is not updated.

## Example

- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)

## Related documentation

- [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- [`appregdef_render`](/docs/technical-design/instance-pipeline/appregdef-render.md)
