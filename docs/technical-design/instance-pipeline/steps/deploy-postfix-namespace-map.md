# `deploy_postfix_namespace_map`

- [`deploy_postfix_namespace_map`](#deploy_postfix_namespace_map)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `deploy_postfix_namespace_map` step writes file
`environments/<cluster-name>/<env-name>/Inventory/namespace-map.yml`.

## Input parameters

| Parameter        | Source   | Required | Default  | Values / format             | Effect                                                                        |
| ---------------- | -------- | -------- | -------- | --------------------------- | ----------------------------------------------------------------------------- |
| `ENV_NAMES`      | Pipeline | Yes      | None     | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/`                             |
| `PIPELINE_TYPE`  | Pipeline | Yes      | None     | `GITLAB_DEPLOY`             | Step runs only when value is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY` |
| `OPERATION_TYPE` | Pipeline | No       | `DEPLOY` | `DEPLOY`                    | Step runs only when value is `DEPLOY`                                         |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY`
   and pipeline parameter `OPERATION_TYPE` is `DEPLOY`. Otherwise the Instance pipeline skips this
   step.

2. **Copy Environment Inventory and prepare render workspace**

   1. The step copies directory `Inventory/` from
      `environments/<cluster-name>/<env-name>/Inventory/` to `tmp/render/<env-name>/Inventory/`.

   2. The step runs additional template-parameter processing on the copied Inventory tree.

   3. The step resolves Cloud Passport file path for the target Environment.

3. **Load render context documents**

   1. The step reads Environment Inventory from `tmp/render/<env-name>/Inventory/env_definition.yml`
      and ensures field `inventory.environmentName` is present.

   2. When a Cloud Passport file path is resolved, the step loads the Cloud Passport document into
      the render context.

   3. The step renders internal environment config from `env_config.yml.j2` and reads field
      `environment.env_template` from the rendered config.

4. **Load Template Descriptor**

   1. The step loads common Template Descriptor file
      `tmp/templates/env_templates/<envTemplate.name>.{yml,yaml,yml.j2,yaml.j2}`.

   2. When the matched file ends with `.j2`, the step renders it to a non-`.j2` path before load.

   3. The step validates Template Descriptor against `schemas/template-descriptor.schema.json`.

   4. When directories `tmp/origin/templates/` or `tmp/peer/templates/` exist, the step loads
      matching origin-side and peer-side Template Descriptors with the same
      `<envTemplate.name>` basename.

5. **Render BG Domain**

   1. When Template Descriptor `bg_domain` is present, the step renders it and writes file
      `tmp/render/<env-name>/bg_domain.yml`.

   2. When Template Descriptor `bg_domain` is absent, the step skips BG Domain rendering.

6. **Collect map rows and render Namespace templates**

   For each element in Template Descriptor `namespaces[]`:

   1. The step renders Template Descriptor `namespaces[].template_path` against the render context.

   2. The step sets map key from Template Descriptor `namespaces[].deploy_postfix`. When absent,
      the step sets map key from the basename of the rendered template path without `.yml.j2` or
      `.yaml.j2`.

   3. The step sets Namespace folder name to map key plus suffix `-origin` or `-peer` when the
      Namespace name matches `bg_domain.yml` field `originNamespace.name` or
      `peerNamespace.name`.

   4. The step resolves Namespace name from Template Descriptor `namespaces[].template_override.name`.
      When absent, the step renders the Namespace template file and reads field `name`.

   5. The step assigns row role by comparing the Namespace name with `bg_domain.yml` fields
      `originNamespace.name` and `peerNamespace.name`.

   6. When row role is `origin` or `peer` and a role-specific Template Descriptor was loaded in
      step 4, the step replaces the namespace config and template path with the matching entry from
      the role-specific Template Descriptor.

   7. The step renders Namespace template file to
      `tmp/render/<env-name>/Namespaces/<folder-name>/namespace.yml`.

   8. When Template Descriptor `namespaces[].template_override` is present, the step writes
      `namespace.yml_override` beside the rendered Namespace file.

7. **Resolve map entries and write output**

   1. When row role is neither `origin` nor `peer`, the step adds map entry
      `<map-key>: <namespace-name>`.

   2. When row role is `origin` or `peer`, the step adds the Namespace name under the
      corresponding side key of the map entry for that `deployPostfix`. The map entry holds both
      sides:

      ```yaml
      <map-key>:
        origin: <origin-namespace-name>
        peer: <peer-namespace-name>
      ```

      The step builds the per-side entry from the rendered BG Domain. `BG_NS_TARGET` does not
      affect the map.

   3. The step writes file `environments/<cluster-name>/<env-name>/Inventory/namespace-map.yml`
      and replaces any previous file.

## Result

1. File `environments/<cluster-name>/<env-name>/Inventory/namespace-map.yml` contains entries
   keyed by `deployPostfix`. A non-BG `deployPostfix` maps to a scalar Namespace name. A BG
   `deployPostfix` maps to an object with `origin` and `peer` keys holding both Namespace names.

2. Files `tmp/render/<env-name>/Namespaces/<folder-name>/namespace.yml` and optional
   `namespace.yml_override` exist only during the pipeline run. The step does not copy them to
   `environments/<cluster-name>/<env-name>/Namespaces/`.

3. File `tmp/render/<env-name>/bg_domain.yml` exists only during the pipeline run when Template
   Descriptor `bg_domain` is present.

## Error handling

**4a.** The step fails when Template Descriptor file
`tmp/templates/env_templates/<envTemplate.name>.*` is missing. File `namespace-map.yml` is not
written.

**4b.** The step fails when Template Descriptor fails validation against
`schemas/template-descriptor.schema.json`. File `namespace-map.yml` is not written.

**5a.** The step fails when Template Descriptor `bg_domain` fails to render. File
`namespace-map.yml` is not written.

**6a.** The step fails when Template Descriptor `namespaces[].template_path` fails to render. File
`namespace-map.yml` is not written.

## Example

- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
- [`bgd.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd.yaml)
- [`bg_domain.yml.j2`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd/bg_domain.yml.j2)
- [`namespace-map.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/namespace-map.yml)

## Related documentation

- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- [`appregdef_render`](/docs/technical-design/instance-pipeline/steps/appregdef-render.md)
- [`process_deployment_plan`](/docs/technical-design/instance-pipeline/steps/process-deployment-plan.md)
