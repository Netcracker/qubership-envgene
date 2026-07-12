# Blue-Green Deployment Configuration

- [Blue-Green Deployment Configuration](#blue-green-deployment-configuration)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Concepts](#concepts)
  - [Migrate a non-BG template and environment to BGD](#migrate-a-non-bg-template-and-environment-to-bgd)
    - [Step 1: Capture the non-BG baseline](#step-1-capture-the-non-bg-baseline)
    - [Step 2: Extend the Environment Template descriptor](#step-2-extend-the-environment-template-descriptor)
    - [Step 3: Add the BG Domain template](#step-3-add-the-bg-domain-template)
    - [Step 4: Update Environment Inventory](#step-4-update-environment-inventory)
    - [Step 5: Generate and validate](#step-5-generate-and-validate)
  - [Deploy modes](#deploy-modes)
    - [Deploy in peer namespace](#deploy-in-peer-namespace)
    - [Deploy in origin namespace](#deploy-in-origin-namespace)
    - [Deploy non-BG namespace](#deploy-non-bg-namespace)
    - [Deploy in controller namespace](#deploy-in-controller-namespace)
  - [Deploy mode summary](#deploy-mode-summary)
  - [Pipeline parameters by deploy mode](#pipeline-parameters-by-deploy-mode)
  - [Related documentation](#related-documentation)
  - [Samples](#samples)

## Description

This guide explains how to prepare an Environment Template and Environment Inventory for [Blue-Green Deployment (BGD)](/docs/features/blue-green-deployment.md) in EnvGene.

It covers four deployment configurations used by the Instance pipeline and deploy orchestrator:

- **Deploy in peer namespace** - update the standby (green) namespace in the BG Domain
- **Deploy in origin namespace** - update the active (blue) namespace in the BG Domain
- **Deploy non-BG namespace** - deploy namespaces that are not part of the BG Domain lifecycle
- **Deploy in controller namespace** - update the BG controller namespace (operator, plugin)

Working examples are in [`/docs/samples/bgd/`](/docs/samples/bgd/).

## Prerequisites

- Familiarity with [Environment Template](/docs/envgene-objects.md#template-descriptor) and [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) structure
- A running Instance pipeline (see [Pipeline Configuration](/docs/envgene-pipelines.md))
- For BG lifecycle operations: BG Operator endpoint reachable from the pipeline and credentials for the controller (see [BG Domain](/docs/envgene-objects.md#bg-domain))

## Concepts

EnvGene separates **what to render** (template artifacts and descriptor) from **which namespaces to process** (pipeline parameters).

| Layer | Responsibility |
|-------|----------------|
| **Environment Template descriptor** | Declares tenant, cloud, namespaces, and `bg_domain` template path |
| **BG Domain object** | Maps `originNamespace`, `peerNamespace`, and `controllerNamespace` names |
| **`envTemplate.artifact`** | Renders all objects except origin/peer when `bgNsArtifacts` is set |
| **`envTemplate.bgNsArtifacts`** | Optional separate artifacts for origin and peer namespaces only |
| **`NS_BUILD_FILTER`** | Selects which namespaces are regenerated during a pipeline run |

Namespace folder names for origin and peer follow [Environment Instance Generation](/docs/features/environment-instance-generation.md#namespace-in-bg-domain-origin-or-peer) rules (`<deploy_postfix>-origin` / `<deploy_postfix>-peer` when `deploy_postfix` is set).

BG Domain role aliases for [`NS_BUILD_FILTER`](/docs/features/namespace-render-filtering.md):

- `@origin` - origin namespace
- `@peer` - peer namespace
- `@controller` - controller namespace

## Migrate a non-BG template and environment to BGD

Use the samples in [`/docs/samples/bgd/`](/docs/samples/bgd/) as the target state. The `non-bgd/` and `bgd/` folders show before and after layouts.

### Step 1: Capture the non-BG baseline

A typical non-BG setup has a single application namespace in the template descriptor:

```yaml
# non-bgd/simple.yaml (excerpt)
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/non-bgd/bss.yml.j2"
```

And inventory with only `envTemplate.artifact`:

```yaml
# inventory/env_definition-non-bgd-baseline.yml (excerpt)
envTemplate:
  name: "simple-bss"
  artifact: "my-env-templates:1.0.0"
```

See [`/docs/samples/bgd/template/non-bgd/`](/docs/samples/bgd/template/non-bgd/) and [`/docs/samples/bgd/inventory/env_definition-non-bgd-baseline.yml`](/docs/samples/bgd/inventory/env_definition-non-bgd-baseline.yml).

### Step 2: Extend the Environment Template descriptor

1. Duplicate the application namespace template entry for **origin** and **peer**, each with a distinct `template_override.name` matching the names you will declare in the BG Domain template.
2. Set `deploy_postfix` on origin/peer entries so Solution Descriptor `deployPostfix` values map to the correct namespace folders (for example `origin-bss` and `peer-bss`).
3. Add namespace templates for **bg-controller** and **bg-plugin** (controller-side components).
4. Keep non-BG namespaces (for example data management) as a single entry without origin/peer duplication.
5. Add the `bg_domain` key pointing to the BG Domain Jinja template.

```yaml
# bgd/bgd.yaml (excerpt) - see full file in samples
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/bgd/bss.yml.j2"
    deploy_postfix: "peer-bss"
    template_override:
      name: "{{ current_env.name }}-peer-bss"
  - template_path: "{{ templates_dir }}/env_templates/bgd/bss.yml.j2"
    deploy_postfix: "origin-bss"
    template_override:
      name: "{{ current_env.name }}-origin-bss"
  - template_path: "{{ templates_dir }}/env_templates/bgd/bg-plugin.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/bg-controller.yml.j2"
  - template_path: "{{ templates_dir }}/env_templates/bgd/data-management.yml.j2"
bg_domain: "{{ templates_dir }}/env_templates/bgd/bg_domain.yml.j2"
```

Full descriptor: [`/docs/samples/bgd/template/bgd/bgd.yaml`](/docs/samples/bgd/template/bgd/bgd.yaml).

### Step 3: Add the BG Domain template

Create `bg_domain.yml.j2` with `type: bgdomain` and namespace names that **exactly match** the `template_override.name` values for origin, peer, and controller entries.

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

See [`/docs/samples/bgd/template/bgd/bg_domain.yml.j2`](/docs/samples/bgd/template/bgd/bg_domain.yml.j2).

> [!IMPORTANT]
> During Environment Instance generation, EnvGene validates that every namespace referenced in `bg_domain.yml` exists in the generated Environment. A mismatch between `template_override.name` and BG Domain names causes generation to fail.

### Step 4: Update Environment Inventory

1. Set `envTemplate.name` to the BGD template descriptor name (for example `bgd`).
2. Keep `envTemplate.artifact` mandatory - it renders controller, plugin, non-BG namespaces, tenant, cloud, and other objects.
3. Optionally add `envTemplate.bgNsArtifacts` when origin and peer must use **different** template artifact versions:

```yaml
envTemplate:
  name: "bgd"
  artifact: "my-env-templates:2.0.0"
  bgNsArtifacts:
    origin: "my-env-templates:2.0.0-origin"
    peer: "my-env-templates:2.0.0-peer"
```

When `bgNsArtifacts` is omitted, `artifact` renders origin and peer as well.

See [`/docs/samples/bgd/inventory/env_definition-bgd.yml`](/docs/samples/bgd/inventory/env_definition-bgd.yml) (single artifact) and [`/docs/samples/bgd/inventory/env_definition-bgd-with-bg-ns-artifacts.yml`](/docs/samples/bgd/inventory/env_definition-bgd-with-bg-ns-artifacts.yml) (split artifacts).

### Step 5: Generate and validate

1. Run the Instance pipeline with `ENV_NAMES` set to your environment.
2. Confirm generated output under `/environments/<cluster>/<env>/`:
   - `bg_domain.yml`
   - `Namespaces/<deploy_postfix>-origin/` and `Namespaces/<deploy_postfix>-peer/`
   - `Namespaces/bg-controller/` (controller namespace folder uses template name when `deploy_postfix` is absent)
   - Non-BG namespace folders unchanged in role (for example `data-management/`)
3. For BG lifecycle, trigger with `BG_MANAGE=true` and `BG_STATE` as described in [Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md).

## Deploy modes

Each deploy mode combines **inventory artifact selection** (what template version renders which namespace role) with **`NS_BUILD_FILTER`** (which namespaces are regenerated in this pipeline run).

### Deploy in peer namespace

Use when deploying application changes to the **standby** namespace before promotion (typical green path).

**Template / inventory:**

- Origin and peer entries in the template descriptor reference the same namespace Jinja file with different `template_override.name` values.
- Point `envTemplate.bgNsArtifacts.peer` to the artifact version that should render the peer namespace, or rely on `envTemplate.artifact` for both.

**Pipeline (regenerate peer only):**

```yaml
NS_BUILD_FILTER: "@peer"
```

Or by namespace name:

```yaml
NS_BUILD_FILTER: "<env-name>-peer-bss"
```

**Update peer artifact version without changing origin:**

```yaml
ENV_TEMPLATE_VERSION_PEER: "my-env-templates:2.1.0-peer"
```

### Deploy in origin namespace

Use when updating the **active** namespace (for example hotfix on blue while peer stays idle).

**Template / inventory:**

- Same descriptor layout as peer; active namespace is `originNamespace` in `bg_domain.yml`.
- Use `envTemplate.bgNsArtifacts.origin` when origin needs a different artifact than peer.

**Pipeline (regenerate origin only):**

```yaml
NS_BUILD_FILTER: "@origin"
```

**Update origin artifact version:**

```yaml
ENV_TEMPLATE_VERSION_ORIGIN: "my-env-templates:2.1.0-origin"
```

### Deploy non-BG namespace

Use for namespaces **outside** the BG Domain (no origin/peer pair, no BG state files).

**Template / inventory:**

- List the namespace once in the descriptor (for example `data-management.yml.j2`) without origin/peer duplication.
- Do **not** reference it in `bg_domain.yml`.
- Always rendered from `envTemplate.artifact`.

**Pipeline:**

Select by namespace folder or template name:

```yaml
NS_BUILD_FILTER: "<env-name>-data-management"
```

Or regenerate everything except BG roles:

```yaml
NS_BUILD_FILTER: "! @peer,@origin,@controller"
```

> [!NOTE]
> Mixed alias and direct name selectors in one `NS_BUILD_FILTER` expression are not allowed. See [Namespace Render Filter](/docs/features/namespace-render-filtering.md#error-handling).

### Deploy in controller namespace

Use for BG Operator plugin, controller workloads, or other components in the dedicated controller namespace.

**Template / inventory:**

- Declare `bg-controller` (and optionally `bg-plugin`) in the template descriptor.
- Map `controllerNamespace.name` in `bg_domain.yml` to the controller namespace template `name`.
- Controller is always rendered from `envTemplate.artifact`, not from `bgNsArtifacts`.

**Pipeline (regenerate controller only):**

```yaml
NS_BUILD_FILTER: "@controller"
```

Ensure `bg_domain.controllerNamespace.credentials` exists in the generated Credentials file (EnvGene creates it during generation when the BG Domain template specifies `credentials`).

## Deploy mode summary

| Deploy mode | Namespace role | Rendered from | Typical `NS_BUILD_FILTER` |
|-------------|----------------|---------------|---------------------------|
| Deploy in peer | `peerNamespace` | `bgNsArtifacts.peer` or `artifact` | `@peer` |
| Deploy in origin | `originNamespace` | `bgNsArtifacts.origin` or `artifact` | `@origin` |
| Deploy non-BG | Not in BG Domain | `artifact` | `<namespace-name>` or `! @peer,@origin,@controller` |
| Deploy in controller | `controllerNamespace` | `artifact` | `@controller` |

## Pipeline parameters by deploy mode

| Parameter | Used for |
|-----------|----------|
| [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#ns_build_filter) | Limit which namespaces are regenerated |
| [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version) | Override `envTemplate.artifact` for this run |
| [`ENV_TEMPLATE_VERSION_ORIGIN`](/docs/instance-pipeline-parameters.md#env_template_version_origin) | Override `envTemplate.bgNsArtifacts.origin` |
| [`ENV_TEMPLATE_VERSION_PEER`](/docs/instance-pipeline-parameters.md#env_template_version_peer) | Override `envTemplate.bgNsArtifacts.peer` |
| [`BG_MANAGE`](/docs/instance-pipeline-parameters.md#bg_manage) | Run BG lifecycle job (not used for ordinary deploy-only runs) |
| [`BG_STATE`](/docs/instance-pipeline-parameters.md#bg_state) | Target BG states for `bg_manage` |

For BG lifecycle operations (warmup, promote, commit), see [Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md).

## Related documentation

- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [Namespace Render Filter](/docs/features/namespace-render-filtering.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)

## Samples

| Path | Purpose |
|------|---------|
| [`/docs/samples/bgd/README.md`](/docs/samples/bgd/README.md) | Sample layout and packaging notes |
| [`/docs/samples/bgd/template/non-bgd/`](/docs/samples/bgd/template/non-bgd/) | Pre-migration template |
| [`/docs/samples/bgd/template/bgd/`](/docs/samples/bgd/template/bgd/) | Post-migration BGD template |
| [`/docs/samples/bgd/inventory/`](/docs/samples/bgd/inventory/) | Environment Inventory before and after migration |
