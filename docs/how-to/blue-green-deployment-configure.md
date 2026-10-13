# Configure Blue-Green Deployment

- [Configure Blue-Green Deployment](#configure-blue-green-deployment)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Step 1: Plan the topology](#step-1-plan-the-topology)
  - [Step 2: Add the BG Domain template](#step-2-add-the-bg-domain-template)
  - [Step 3: Add the Composite Structure template](#step-3-add-the-composite-structure-template)
  - [Step 4: Create the Environment Template descriptor](#step-4-create-the-environment-template-descriptor)
  - [Step 5: Create the Environment Inventory](#step-5-create-the-environment-inventory)
  - [Step 6: Generate the Environment Instance](#step-6-generate-the-environment-instance)
  - [Step 7: Validate the result](#step-7-validate-the-result)
  - [Related documentation](#related-documentation)

## Description

Configure an Environment Template and Environment Inventory for
[Blue-Green Deployment (BGD)](/docs/features/blue-green-deployment.md). BGD adds two objects to the
Environment Template:

- a BG Domain that names the origin, peer, and controller namespaces
- a Composite Structure that groups the namespaces and references the BG Domain

These steps also convert an existing non-BG Environment: start from its current template and inventory. The
sample in [`/docs/samples/blue-green-deployment/`](/docs/samples/blue-green-deployment/) shows the result:
the `bgd.yaml` descriptor and the `env-01` environment.

Once configured, deploy the environment as described in
[Blue-Green Deployment deploy operations](/docs/how-to/blue-green-deployment-deploy-operations.md).

## Prerequisites

- An Environment Template and Environment Inventory that generate successfully in the Instance pipeline.
  To convert an existing non-BG Environment, start from its template and inventory.
- The [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) architecture. BGD runs only with
  `PIPELINE_TYPE: GITLAB_DEPLOY` and an Environment Inventory that sets `noCmdbVersion: v2`.

## Step 1: Plan the topology

BGD requires one BG Domain: an origin namespace, a peer namespace, and a controller namespace. You build
the domain across Steps 2 to 4.

The sample topology is illustrative, not a fixed shape. The BG Domain - origin, peer, and controller - is
required. The `oss` satellite and the standalone `supplementary` namespace are optional, added to show the
options. Keep the namespaces your solution already has and drop the rest.

## Step 2: Add the BG Domain template

Create `bg_domain.yml.j2`. It declares the namespace names for the origin, peer,
and controller roles, and the controller URL and credentials. This is a standalone object authored in the
template. EnvGene does not derive it from the Composite Structure.

```yaml
name: "{{ current_env.name }}-bss-domain"
type: bgdomain
originNamespace:
  name: "{{ current_env.name }}-bss-origin"
  type: namespace
peerNamespace:
  name: "{{ current_env.name }}-bss-peer"
  type: namespace
controllerNamespace:
  name: "{{ current_env.name }}-bg-controller"
  type: namespace
  credentials: bg-controller-cred
  url: ${CLOUD_PROTOCOL}://bluegreen-controller-{{ current_env.name }}-bg-controller.${CLOUD_PUBLIC_HOST}
```

Required fields are documented in [BG Domain](/docs/envgene-objects.md#bg-domain). See
[`bg_domain.yml.j2`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd/bg_domain.yml.j2).

## Step 3: Add the Composite Structure template

Create `composite_structure.yml.j2`. It groups the namespaces into a `baseline` and `satellites`. A member
is either a plain `namespace` or a `bgdomain`. The `bgdomain` member holds only a reference to the BG
Domain by name. The domain namespaces and the controller URL and credentials stay in `bg_domain.yml`.

```yaml
name: "{{ current_env.name }}-composite-structure"
baseline:
  name: "{{ current_env.name }}-core"
  type: namespace
satellites:
  - name: "{{ current_env.name }}-bss-domain"
    type: bgdomain
  - name: "{{ current_env.name }}-oss"
    type: namespace
```

The `bgdomain` member `name` matches the BG Domain `name` from Step 2. Namespaces outside the composite,
such as `supplementary`, are not listed here. They stay plain namespace entries in the descriptor. See
[`composite_structure.yml.j2`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd/composite_structure.yml.j2).

## Step 4: Create the Environment Template descriptor

The descriptor lists the templates that render the Environment. Assemble it from the tenant and cloud
templates, the namespace templates, and the two BGD objects from Steps 2 and 3.

1. Reference the tenant and cloud templates. These are standard EnvGene objects and carry no BG specifics.
2. Add the application namespace entry twice, for **origin** and **peer**, each with a distinct
   `template_override.name` matching the origin and peer names from Step 2.
3. Add namespace entries for the **controller**, the composite **baseline** and **satellite**, and any
   **standalone** namespace outside the composite.
4. Add the `composite_structure` key pointing to the Composite Structure template from Step 3.
5. Add the `bg_domain` key pointing to the BG Domain template from Step 2.

```yaml
tenant: "{{ templates_dir }}/env_templates/common/tenant.yml.j2"
cloud:
  template_path: "{{ templates_dir }}/env_templates/common/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/bss.yml.j2"
    template_override:
      name: "{{ current_env.name }}-bss-origin"
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/bss.yml.j2"
    template_override:
      name: "{{ current_env.name }}-bss-peer"
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/bg-controller.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/core.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/oss.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/namespaces/supplementary.yml.j2"
composite_structure: "{{ templates_dir }}/env_templates/bgd/composite_structure.yml.j2"
bg_domain: "{{ templates_dir }}/env_templates/bgd/bg_domain.yml.j2"
```

Full descriptor: [`bgd.yaml`](/docs/samples/blue-green-deployment/template-repository/templates/env_templates/bgd.yaml).

The origin and peer entries share `bss.yml.j2`, so any parameterset or resource profile bound in the
template applies to both sides.

## Step 5: Create the Environment Inventory

The inventory selects the template artifact and binds parameters to the environment. The `envTemplate.name`
and `envTemplate.artifact` fields are standard, with no BG specifics. BGD adds the `noCmdbVersion: v2`
requirement and the optional `bgNsArtifacts` and env-specific bindings.

1. Set `inventory.noCmdbVersion` to `v2`. BGD runs only on the No-CMDB v2 architecture.
2. Set `envTemplate.name` to the BGD template descriptor name, for example `bgd`.
3. Set `envTemplate.artifact`, the mandatory template artifact. It renders the controller, baseline,
   satellites, and standalone namespaces, plus the tenant, cloud, and other objects.
4. Add `envTemplate.bgNsArtifacts` to track the origin and peer template artifact versions separately.
5. Optionally bind env-specific parametersets to a side through `envTemplate.envSpecificParamsets`, keyed by
   the namespace deploy postfix (`bss-origin`, `bss-peer`). A parameterset listed under both keys applies to
   both sides. A parameterset listed under one key applies to that side only.
6. Optionally bind an env-specific resource profile per side through `envTemplate.envSpecificResourceProfiles`,
   keyed by the same postfix. A namespace resolves to a single profile, so binding one here replaces the
   template default (`bss-dev-override`) for that side. Override both sides for fully side-specific profiles,
   or override one side to diverge just that side while the other keeps the template default.

```yaml
inventory:
  noCmdbVersion: "v2"
envTemplate:
  name: "bgd"
  artifact: "my-env-templates:2.0.0"
  bgNsArtifacts:
    origin: "my-env-templates:2.0.0"
    peer: "my-env-templates:2.0.0"
  envSpecificParamsets:
    bss-origin:
      - "bg-shared-params"    # applies to both sides
      - "bg-origin-params"    # origin only
    bss-peer:
      - "bg-shared-params"    # applies to both sides
      - "bg-peer-params"      # peer only
  envSpecificResourceProfiles:
    bss-origin: "bg-origin-profile"
    bss-peer: "bg-peer-profile"
```

When `bgNsArtifacts` is omitted, `artifact` renders the origin and peer sides as well.

> [!NOTE]
> At setup time both sides hold the same version. The versions diverge later, when a
> [deploy operation](/docs/how-to/blue-green-deployment-deploy-operations.md#deploy-to-the-origin-or-peer-namespace)
> updates one side.

See [`env-01/Inventory/env_definition.yml`](/docs/samples/blue-green-deployment/instance-repository/environments/cluster-01/env-01/Inventory/env_definition.yml)
for the full BGD inventory with `bgNsArtifacts`, the shared `bg-shared-params` parameterset, the
side-specific `bg-origin-params` and `bg-peer-params`, and the per-side `bg-origin-profile` and
`bg-peer-profile`.

## Step 6: Generate the Environment Instance

Run the Instance pipeline over the full Environment and generate the Effective Set:

```yaml
ENV_NAMES: "<cluster-name>/<environment-name>"
OPERATION_TYPE: "DEPLOY"
PIPELINE_TYPE: "GITLAB_DEPLOY"
APPLICATION_VERSIONS: "<value>"
```

## Step 7: Validate the result

Confirm the generated output under `/environments/<cluster-name>/<environment-name>/`:

- `bg_domain.yml` and `composite_structure.yml`
- `Namespaces/bss-origin/` and `Namespaces/bss-peer/`
- `Namespaces/bg-controller/`, `Namespaces/core/`, `Namespaces/oss/`, and the standalone
  `Namespaces/supplementary/`
- `bg_domain.controllerNamespace.credentials` in the generated Credentials file. EnvGene creates it during
  generation.
- BG parameters in the Effective Set Topology Context. See
  [BG Domain parameters in Effective Set](/docs/features/calculator-cli.md#version-20topology-context-bg_domain-example).

For the BG lifecycle operations (initialize the domain, warmup, promote, rollback, commit), which run with
[`OPERATION_TYPE: BGD`](/docs/instance-pipeline-parameters.md#operation_type),
[`BGD_OPERATION`](/docs/instance-pipeline-parameters.md#bgd_operation), and
[`BG_STATE`](/docs/instance-pipeline-parameters.md#bg_state), see
[Blue-Green Deployment](/docs/features/blue-green-deployment.md).

## Related documentation

- [Blue-Green Deployment deploy operations](/docs/how-to/blue-green-deployment-deploy-operations.md)
- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)
