# `env_build`

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

The `env_build` step renders and writes the Environment Instance tree under
`environments/<cluster-name>/<env-name>/`, including Namespaces, Applications, Cloud, Tenant, BG
Domain, Profiles, and credential files.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `ENV_NAMES` | Pipeline | Yes | None | `<cluster-name>/<env-name>` | Selects `environments/<cluster-name>/<env-name>/` |
| `PIPELINE_TYPE` | Pipeline | Yes | None | `GITLAB_DEPLOY` | Step runs when value is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY` or `CLEAN`, unless `ENV_BUILDER: true` |
| `OPERATION_TYPE` | Pipeline | Yes | None | `DEPLOY`, `CLEAN` | On `CLEAN`, marks cleaned Namespaces in rendered objects |
| `ENV_BUILDER` | Pipeline | No | `false` | `true`, `false` | When `true`, step runs regardless of `PIPELINE_TYPE` |
| `BG_NS_TARGET` | Pipeline | Conditional | None | `origin`, `peer` | Selects origin or peer Namespace from per-side `namespace-map.yml` entries when deploy plan contains a BG `deployPostfix` |

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `ENV_BUILDER` is `true`, or when
   pipeline parameter `PIPELINE_TYPE` is `GITLAB_DEPLOY` and pipeline parameter `OPERATION_TYPE` is
   `DEPLOY` or `CLEAN`. Otherwise the Instance pipeline skips this step.

2. **Validate environment and decrypt credentials**

   1. The step validates Environment Inventory against `schemas/env-definition.schema.json`.

   2. The step validates ParameterSet files from Template Repository and Instance Repository paths
      against `schemas/paramset.schema.json`.

   3. The step decrypts credential files under
      `environments/<cluster-name>/<env-name>/Credentials/`.

3. **Prepare render workspace**

   1. The step deletes directory `tmp/render/` and recreates `tmp/render/<env-name>/`.

   2. The step copies directory `Inventory/` from the Environment Instance to
      `tmp/render/<env-name>/Inventory/`.

   3. The step copies ParameterSet trees from `tmp/templates/parameters/`,
      `tmp/origin/templates/parameters/`, `tmp/peer/templates/parameters/`, cluster-level
      `environments/<cluster-name>/parameters/`, global `environments/parameters/`, and Environment
      Inventory `Inventory/parameters/` into `tmp/parameters_templates/`.

   4. The step copies Template Repository `resource_profiles/` into `tmp/resource_profiles/`.

   5. The step removes selected targets under the Environment Instance output path:
      `Applications/`, `Namespaces/`, `Profiles/`, `cloud.yml`, `tenant.yml`, `bg_domain.yml`, and
      `composite_structure.yml`.

4. **Pre-process copied Inventory**

   1. The step runs additional template-parameter processing on `tmp/render/<env-name>/`.

   2. The step updates Cloud name fields in copied Inventory from Cloud Passport data when
      applicable.

   3. The step copies directory `Credentials/` from the Environment Instance into
      `tmp/render/<env-name>/Credentials/`.

5. **Render configuration objects**

   1. The step loads Template Descriptor from unpacked template directories the same way as step
      `deploy_postfix_namespace_map`, including optional origin-side and peer-side descriptors.

   2. The step renders Template Descriptor `bg_domain` to `tmp/render/<env-name>/bg_domain.yml`
      when present.

   3. The step reads file `Inventory/namespace-map.yml` written by step
      `deploy_postfix_namespace_map`.

   4. The step reads file `Inventory/deploy-plan.yml` when present and resolves the set of
      Namespace names to render. For each deploy-plan entry, the step looks up the
      `deployPostfix` in `namespace-map.yml`. When the map value is a scalar, the step adds
      that Namespace name. When the map value is a per-side object, the step reads pipeline
      parameter `BG_NS_TARGET` and adds the Namespace name from the matching key. When
      `BG_NS_TARGET` is absent and the map value is a per-side object, the step fails (5c).

   5. When file `Inventory/deploy-plan.yml` is absent, the step renders all Template Descriptor
      `namespaces[]` entries.

   6. The step builds field `solution_structure` on the render context from deploy-plan entries
      and the resolved Namespace names.

   7. The step renders only the selected Namespace entries from Template Descriptor
      `namespaces[]` to `tmp/render/<env-name>/Namespaces/<folder-name>/namespace.yml`.
      Namespace entries not present in the resolved set are not rendered.

   8. The step renders Tenant template to `tmp/render/<env-name>/tenant.yml`.

   9. The step renders Cloud template to `tmp/render/<env-name>/cloud.yml`.

   10. When Template Descriptor `composite_structure` is present, the step renders it to
       `tmp/render/<env-name>/composite_structure.yml` and validates against
       `schemas/composite-structure.schema.json`.

   11. When Template Descriptor `external_credential_template` is present, the step renders
       external credentials into the Environment credential files.

   12. The step renders ParameterSet Jinja templates from `tmp/parameters_templates/` into
       `tmp/render/<env-name>/`.

   13. The step validates that every Namespace name referenced in `bg_domain.yml` exists among
       rendered Namespaces.

6. **Process Tenant, Cloud, Namespaces, and Applications**

   1. The step builds role-specific ParameterSet maps from `tmp/parameters_templates/`. Origin-side
       Namespaces use origin-side ParameterSets when `tmp/origin/templates/` exists. Peer-side
       Namespaces use peer-side ParameterSets when `tmp/peer/templates/` exists. Other Namespaces use
       common ParameterSets.

   2. The step resolves ParameterSets into Tenant, Cloud, and Namespace parameter structures and
       writes processed YAML under `tmp/render/<env-name>/`.

   3. The step processes Cloud Passport merge into Cloud objects.

   4. For each rendered Namespace, the step resolves ParameterSets into Namespace and Application
       parameter structures and renders Application objects under
       `tmp/render/<env-name>/Namespaces/<folder-name>/Applications/`.

   5. When pipeline parameter `OPERATION_TYPE` is `CLEAN`, the step marks cleaned Namespaces in
       rendered Namespace objects.

   6. The step collects and copies Resource Profiles into `tmp/render/<env-name>/Profiles/`,
       applying Environment Inventory `envTemplate.envSpecificResourceProfiles` overrides.

   7. The step merges `*_override` files into rendered Cloud and Namespace YAML and deletes the
       override files.

7. **Write credentials and publish Environment Instance**

   1. The step scans rendered Tenant, Cloud, and Namespace parameters for credential references and
      writes or updates `Credentials/credentials.yml`.

   2. The step copies rendered content from `tmp/render/<env-name>/` to
      `environments/<cluster-name>/<env-name>/`, restoring committed `env_definition.yml` from the
      pre-copy Inventory source before overwrite.

   3. The step encrypts credential files under
      `environments/<cluster-name>/<env-name>/Credentials/`.

## Result

1. Directory `environments/<cluster-name>/<env-name>/` contains rendered Environment Instance
   objects: `bg_domain.yml`, `tenant.yml`, `cloud.yml`, optional `composite_structure.yml`,
   `Namespaces/` with `Applications/`, and `Profiles/`.

2. File `environments/<cluster-name>/<env-name>/Credentials/credentials.yml` contains credential
   definitions discovered during render.

3. Namespace directories not selected from the deploy plan keep their pre-run content. When no
   deploy plan is present, all Namespaces are rendered.

4. Directories `tmp/render/`, `tmp/parameters_templates/`, and `tmp/resource_profiles/` exist
   only during the pipeline run.

5. The step does not rewrite `Inventory/namespace-map.yml`. That file remains as written by step
   `deploy_postfix_namespace_map`.

## Error handling

**2a.** The step fails when Environment Inventory or a ParameterSet file fails schema validation.
The Environment Instance is not rebuilt.

**5a.** The step fails when Template Descriptor file
`tmp/templates/env_templates/<envTemplate.name>.*` is missing. The Environment Instance is not
rebuilt.

**5b.** The step fails when Template Descriptor fails validation against
`schemas/template-descriptor.schema.json`. The Environment Instance is not rebuilt.

**5c.** The step fails when a Namespace template fails to render. The Environment Instance is not
rebuilt.

**5c.** The step fails when `namespace-map.yml` value for a `deployPostfix` is a per-side object
and pipeline parameter `BG_NS_TARGET` is absent or empty. The error names `BG_NS_TARGET` and the
`deployPostfix`. The Environment Instance is not rebuilt.

**5d.** The step fails when rendered BG Domain references a Namespace name that was not rendered.
The Environment Instance is not rebuilt.

## Example

- [`bgd.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd.yaml)
- [`env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
- [`bss-origin/namespace.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Namespaces/bss-origin/namespace.yml)

## Related documentation

- [`deploy_postfix_namespace_map`](/docs/technical-design/instance-pipeline/deploy-postfix-namespace-map.md)
- [`process_deployment_plan`](/docs/technical-design/instance-pipeline/process-deployment-plan.md)
