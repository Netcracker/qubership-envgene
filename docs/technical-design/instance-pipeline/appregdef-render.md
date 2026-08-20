# `appregdef_render`

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

The `appregdef_render` step writes Application Definition and Registry Definition files to
`appdefs/` and `regdefs/` at the repository root and, when configured, to
`environments/<cluster-name>/<env-name>/AppDefs/` and `RegDefs/`. The step also unpacks Environment
Template artifacts into `tmp/templates/`, `tmp/origin/templates/`, and `tmp/peer/templates/`.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `ENV_NAMES` | Pipeline | Yes | None | `<cluster-name>/<env-name>` | Selects Environment Inventory and output paths |
| `PIPELINE_TYPE` | Pipeline | Yes | None | `GITLAB_DEPLOY` | Step runs on every `GITLAB_DEPLOY` pipeline run |
| `ENV_BUILDER` | Pipeline | No | `false` | `true`, `false` | When `true`, the step runs even when `PIPELINE_TYPE` is not `GITLAB_DEPLOY` |
| `ENV_TEMPLATE_VERSION` | Pipeline | No | None | artifact coordinates | When set, step `set_template_version` may update Inventory before this step runs |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`
   or pipeline parameter `ENV_BUILDER` is `true`. Otherwise the Instance pipeline skips this step.

2. **Download Environment Template artifacts**

   1. The step reads Environment Inventory `envTemplate.artifact` from
      `environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`.

   2. The step reads Environment Inventory `envTemplate.bgNsArtifacts.origin` and
      `envTemplate.bgNsArtifacts.peer` when present.

   3. The step downloads and unpacks the common template artifact into `tmp/templates/`.

   4. When `envTemplate.bgNsArtifacts.origin` is present, the step downloads and unpacks the
      origin-side artifact into `tmp/origin/templates/`.

   5. When `envTemplate.bgNsArtifacts.peer` is present, the step downloads and unpacks the
      peer-side artifact into `tmp/peer/templates/`.

3. **Copy Environment Inventory to render workspace**

   1. The step copies directory `Inventory/` to `tmp/render/<env-name>/Inventory/`.

   2. The step runs additional template-parameter processing on the copied Inventory tree.

   3. The step resolves Cloud Passport file path for the target Environment.

4. **Load render context and render App/Reg definitions**

   1. The step loads Environment Inventory, Cloud Passport, and rendered environment config into
      the render context.

   2. The step loads App Definition and Registry Definition Jinja templates from
      `tmp/templates/appdefs/` and `tmp/templates/regdefs/`.

   3. The step merges App Definition and Registry Definition overrides from
      `configuration/appdefs/` and `configuration/regdefs/`.

   4. The step renders App Definition templates to `tmp/render/<env-name>/AppDefs/`.

   5. The step renders Registry Definition templates to `tmp/render/<env-name>/RegDefs/`.

   6. The step validates rendered App Definition files against `schemas/appdef.schema.json`.

   7. The step validates rendered Registry Definition files against the Registry Definition schema
      rules.

5. **Publish App/Reg definitions**

   1. The step reads repository configuration field `app_reg_defs_placement`. Allowed values are
      `root` and `dual`. Default is `dual`.

   2. The step copies rendered `AppDefs/` and `RegDefs/` from `tmp/render/<env-name>/` to
      repository root directories `appdefs/` and `regdefs/`.

   3. When `app_reg_defs_placement` is `dual`, the step copies the same trees to
      `environments/<cluster-name>/<env-name>/AppDefs/` and `RegDefs/`.

   4. The step applies file overrides from `configuration/appdefs/` and `configuration/regdefs/` to
      the published locations according to `app_reg_defs_placement`.

6. **Update generated-version metadata**

   1. The step writes resolved common template artifact version metadata into the Environment
      Instance generated-version tracking files.

## Result

1. Directory `tmp/templates/` contains the unpacked common Environment Template artifact used by
   later steps.

2. Directories `tmp/origin/templates/` and `tmp/peer/templates/` exist when corresponding
   `envTemplate.bgNsArtifacts` entries are present in Environment Inventory.

3. Directories `appdefs/` and `regdefs/` at the repository root contain rendered Application and
   Registry Definitions.

4. When `app_reg_defs_placement` is `dual`, directories
   `environments/<cluster-name>/<env-name>/AppDefs/` and `RegDefs/` contain copies of the rendered
   definitions.

## Error handling

**2a.** The step fails when `envTemplate.artifact` is missing or cannot be resolved to a
downloadable template artifact. Template directories are not populated.

**2b.** The step fails when an App Definition file referenced by an artifact coordinate in
`envTemplate.artifact` or `envTemplate.bgNsArtifacts` is missing under `appdefs/`. Template
download does not complete.

**4a.** The step fails when a rendered App Definition or Registry Definition file fails schema
validation. Published definition files are not updated.

## Example

- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
- [`bgd.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd.yaml)

## Related documentation

- [Application and Registry Definition](/docs/features/app-reg-defs.md)
- [`deploy_postfix_namespace_map`](/docs/technical-design/instance-pipeline/deploy-postfix-namespace-map.md)
