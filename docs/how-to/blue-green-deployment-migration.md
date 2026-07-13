# Migrate to Blue-Green Deployment

- [Migrate to Blue-Green Deployment](#migrate-to-blue-green-deployment)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Step 1: Verify the non-BG baseline](#step-1-verify-the-non-bg-baseline)
  - [Step 2: Add the BG Domain template](#step-2-add-the-bg-domain-template)
  - [Step 3: Extend the Environment Template descriptor](#step-3-extend-the-environment-template-descriptor)
  - [Step 4: Update Environment Inventory](#step-4-update-environment-inventory)
  - [Step 5: Generate the Environment Instance](#step-5-generate-the-environment-instance)
  - [Step 6: Validate the result](#step-6-validate-the-result)
  - [Related documentation](#related-documentation)

## Description

Convert a non-BG Environment Template and Environment Inventory to
[Blue-Green Deployment (BGD)](/docs/features/blue-green-deployment.md). The migration touches three
entities:

- Environment Template descriptor
- BG Domain template
- Environment Inventory

Use the samples in [`/docs/samples/blue-green-deployment/`](/docs/samples/blue-green-deployment/) as
the target state. The before and after descriptors (`simple-bss.yaml`, `bgd.yaml`) sit side by side in
the template-repository tree and share one namespace template.

After migration, deploy the environment as described in
[Blue-Green Deployment deploy operations](/docs/how-to/blue-green-deployment-deploy-operations.md).

## Prerequisites

- A working non-BG Environment: its template and inventory generate successfully in the Instance
  pipeline

## Step 1: Verify the non-BG baseline

Compare your starting point with the sample baseline: a descriptor with a single application
namespace:

```yaml
# simple-bss.yaml (excerpt)
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/bss/bss.yml.j2"
```

And inventory with only `envTemplate.artifact`:

```yaml
# env-01/Inventory/env_definition.yml (excerpt)
envTemplate:
  name: "simple-bss"
  artifact: "my-env-templates:1.0.0"
```

See [`simple-bss.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/simple-bss.yaml)
and [`env-01/Inventory/env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml).

Your environment may hold more namespaces. The BG Domain covers exactly one origin/peer pair - the
remaining namespaces stay non-BG.

## Step 2: Add the BG Domain template

Create `bg_domain.yml.j2` with `type: bgdomain`. The template declares the namespace names for the
origin, peer, and controller roles.

Required fields are documented in [BG Domain](/docs/envgene-objects.md#bg-domain). Example:

```yaml
name: "{{ current_env.name }}-bg-domain"
type: bgdomain
originNamespace:
  name: "{{ current_env.name }}-origin-bss"
  type: namespace
peerNamespace:
  name: "{{ current_env.name }}-peer-bss"
  type: namespace
controllerNamespace:
  name: "{{ current_env.name }}-bg-controller"
  type: namespace
  credentials: bgdomain-cred
  url: https://controller.example.local
```

See [`bg_domain.yml.j2`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd/bg_domain.yml.j2).

## Step 3: Extend the Environment Template descriptor

1. Duplicate the application namespace template entry for **origin** and **peer**, each with a distinct
   `template_override.name` matching the names declared in the BG Domain template.
2. Check the generated folder names: EnvGene derives them from the namespace template filename plus
   the role, so `bss.yml.j2` yields `bss-origin` and `bss-peer`. Solution Descriptor `deployPostfix`
   values reference these suffixed names. Set `deploy_postfix` on an entry only when the folder base
   must differ from the template filename. See
   [Environment Instance Generation](/docs/features/environment-instance-generation.md#namespace-in-bg-domain-origin-or-peer)
   for the folder naming rules.
3. Add namespace templates for **bg-controller** and **bg-plugin**. The `bg-controller` template's
   `name` must match `controllerNamespace.name` from Step 2. `bg-plugin` is a regular namespace
   outside the BG Domain lifecycle.
4. Keep non-BG namespaces (for example data management) as a single entry without origin/peer duplication.
5. Add the `bg_domain` key pointing to the BG Domain Jinja template from Step 2.

```yaml
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/bss/bss.yml.j2"
    template_override:
      name: "{{ current_env.name }}-peer-bss"
  - template_path: "{{ templates_dir }}/env_templates/bss/bss.yml.j2"
    template_override:
      name: "{{ current_env.name }}-origin-bss"
  - template_path: "{{ templates_dir }}/env_templates/bgd/bg-plugin.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/bg-controller.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/data-management.yml.j2"
bg_domain: "{{ templates_dir }}/env_templates/bgd/bg_domain.yml.j2"
```

Full descriptor: [`bgd.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd.yaml).

> [!IMPORTANT]
> During Environment Instance generation, EnvGene validates that every namespace referenced in
> `bg_domain.yml` exists in the generated Environment. A mismatch between `template_override.name` and
> BG Domain names causes generation to fail.

## Step 4: Update Environment Inventory

1. Set `envTemplate.name` to the BGD template descriptor name (for example `bgd`).
2. Keep `envTemplate.artifact` mandatory - it renders controller, plugin, non-BG namespaces, tenant,
   cloud, and other objects.
3. Optionally add `envTemplate.bgNsArtifacts` to track the origin and peer template artifact versions
   separately:

```yaml
envTemplate:
  name: "bgd"
  artifact: "my-env-templates:2.0.0"
  bgNsArtifacts:
    origin: "my-env-templates:2.0.0"
    peer: "my-env-templates:2.0.0"
```

When `bgNsArtifacts` is omitted, `artifact` renders origin and peer as well.

> [!NOTE]
> At migration time both roles hold the same version. The versions diverge later, when a
> [deploy operation](/docs/how-to/blue-green-deployment-deploy-operations.md#deploy-in-origin-or-peer-namespace)
> updates one role's version.

See [`env-02/Inventory/env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-02/Inventory/env_definition.yml)
(single artifact) and
[`env-03/Inventory/env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-03/Inventory/env_definition.yml)
(with `bgNsArtifacts`).

## Step 5: Generate the Environment Instance

Run the Instance pipeline over the full Environment and generate the Effective Set:

```yaml
ENV_NAMES: "<cluster-name>/<environment-name>"
ENV_BUILDER: "true"
GENERATE_EFFECTIVE_SET: "true"
```

Add [`CMDB_IMPORT: "true"`](/docs/instance-pipeline-parameters.md#cmdb_import) to validate the CMDB
import as well.

## Step 6: Validate the result

Confirm the generated output under `/environments/<cluster-name>/<environment-name>/`:

- `bg_domain.yml`
- `Namespaces/bss-origin/` and `Namespaces/bss-peer/` (the folder base is the namespace template
  filename, or `deploy_postfix` when set)
- `Namespaces/bg-controller/`
- non-BG namespace folders unchanged in role (for example `data-management/`)
- `bg_domain` parameters in the Effective Set Topology Context (see
  [BG-related parameters in Effective Set](/docs/features/blue-green-deployment.md#bg-related-parameters-in-effective-set))

Optionally, run BG lifecycle operations (`BG_MANAGE=true` with `BG_STATE`) as described in
[Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md). External components
reach the controller through the `url` and `credentials` that the
[BG Domain](/docs/envgene-objects.md#bg-domain) carries into the Effective Set.

## Related documentation

- [Blue-Green Deployment deploy operations](/docs/how-to/blue-green-deployment-deploy-operations.md)
- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)
