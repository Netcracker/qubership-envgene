# Tutorial: Understanding the Effective Set

- [Tutorial: Understanding the Effective Set](#tutorial-understanding-the-effective-set)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Scenario](#scenario)
  - [Step 1: Understand What the Effective Set Is](#step-1-understand-what-the-effective-set-is)
  - [Step 2: Generate the Effective Set](#step-2-generate-the-effective-set)
  - [Step 3: Read the Deployment Context](#step-3-read-the-deployment-context)
  - [Step 4: Trace How Parameters Flow Into the Effective Set](#step-4-trace-how-parameters-flow-into-the-effective-set)
    - [4.1 Resource sizing in per-service-parameters](#41-resource-sizing-in-per-service-parameters)
  - [Step 5: Read the Topology Context](#step-5-read-the-topology-context)
  - [Step 6: Read the Pipeline Context](#step-6-read-the-pipeline-context)
  - [Step 7: Understand Parameter Priority](#step-7-understand-parameter-priority)
    - [7.1 Verify priority with traceability comments](#71-verify-priority-with-traceability-comments)
  - [Step 8: Understand What Triggers a Regeneration](#step-8-understand-what-triggers-a-regeneration)
  - [Summary](#summary)

## What You Will Learn

By the end of this tutorial you will know how to:

- Explain what the Effective Set is, why it exists, and what its contexts are
- Generate the Effective Set with traceability enabled
- Read the deployment context: understand the values files, their priority order, and traceability comments
- Trace how parameters from Tenant, Cloud, Namespace, Application, SBOM, and Resource Profile sources end up in the Effective Set
- Read the topology and pipeline contexts and understand what each one is for
- Use the parameter priority order and traceability comments to debug a wrong value
- Identify what changes require a regeneration

## Prerequisites

- A working Instance Repository with at least one environment that has been through `env_build`
- A Solution Descriptor present at `environments/<cluster>/<env>/Inventory/solution-descriptor/sd.yaml`
- Basic familiarity with EnvGene Environment Instance structure (Tenant, Cloud, Namespace objects)

## Scenario

You manage a solution called BSS deployed to `prod-cluster/prod-01`. The solution has two namespaces:

- `bss` - hosts the `Cloud-BSS` application with two services: `bss-processor` and `bss-api`
- `oss` - hosts the `cloud-oss` application with one service: `oss-api`

You want to understand how the Effective Set is calculated for `prod-cluster/prod-01`, where each value comes from, and how to read the output files to debug a deployment issue.

## Step 1: Understand What the Effective Set Is

The Effective Set is the **final, merged parameter file tree** that EnvGene calculates for one environment. It is not something you write manually - EnvGene generates it by merging many input sources in a defined priority order.

To understand why it exists, consider the problem it solves. Configuration for one environment is spread across many sources:

- **Template Repository** - Namespace templates, Cloud templates, Template ParameterSets, Resource Profile Overrides.

- **Instance Repository** - Cloud and Namespace objects with environment-specific parameters, Environment Specific ParameterSets, Resource Profile Overrides, Credentials, Cloud Passport. The Instance stores configuration for the environment itself but does not specify which applications are deployed to which namespaces or at which versions - that is the job of the Solution Descriptor.

- **Solution Descriptor (SD)** - maps applications to namespaces and defines which version of each application to deploy. Each entry pairs an application version with a `deployPostfix` that identifies the target namespace. For `prod-01` this looks like:

  ```yaml
  applications:
    - version: "Cloud-BSS:1.2.3"
      deployPostfix: "bss"
    - version: "cloud-oss:2.0.1"
      deployPostfix: "oss"
  ```

  This tells EnvGene that `Cloud-BSS v1.2.3` deploys to the `bss` namespace and `cloud-oss v2.0.1` to the `oss` namespace. Without an SD, EnvGene does not know what applications exist and cannot generate the `deployment`, `cleanup`, or `runtime` contexts.

- **Application SBOMs** - for each application version listed in the SD, EnvGene reads the corresponding SBOM from `sboms/<application-name>/` (filename: `<application-name>-<application-version>.sbom.json`). The SBOM is an EnvGene-internal artifact generated automatically per application version. Examples of what it includes:
  - The list of microservices the application consists of (determines the structure of `per-service-parameters/`)
  - Docker image coordinates for each microservice (written to `deploy-descriptor.yaml`)
  - Resource Profile Baselines - named sets of CPU/memory/replica values that serve as the starting point before any overrides are applied.

No single downstream tool can read all of these sources, understand their merge rules, and resolve Jinja expressions by itself. Instead, EnvGene acts as a pre-processor: it reads all sources, applies all merge rules, and writes a single output - the Effective Set - that contains only final, resolved values with no templates, no references, no indirection.

The Effective Set for `prod-cluster/prod-01` lives at:

```text
environments/prod-cluster/prod-01/effective-set/
```

It is divided into five **contexts**. Each context has a format specific to its consumer - a tool reads only its own context and must not access other contexts. This means a change to any input that has **not been followed by a regeneration** is invisible to all consumers.

> [!NOTE]
> The SD is optional inputs. Without an SD, the `deployment`, `cleanup`, and `runtime` contexts are not generated - only `topology` and `pipeline` are produced.

| Context      | Path                        | Source in Instance objects           | Consumer                      |
|--------------|-----------------------------|--------------------------------------|-------------------------------|
| `deployment` | `effective-set/deployment/` | `deployParameters`, Application SBOM | ArgoCD, Helm                  |
| `pipeline`   | `effective-set/pipeline/`   | `e2eParameters`                      | Orchestration pipelines       |
| `runtime`    | `effective-set/runtime/`    | `technicalConfigurationParameters`   | Runtime configuration tooling |
| `cleanup`    | `effective-set/cleanup/`    | `deployParameters`                   | Uninstall tooling             |
| `topology`   | `effective-set/topology/`   | Aggregated environment data          | All consumers                 |

**deployment** - Helm values applied at deploy time: infrastructure service URLs (Consul, DBaaS, MaaS), platform flags, monitoring settings, application-specific configuration, image tags, resource profile baselines (CPU, memory, replicas).

**pipeline** - Parameters that configure how the orchestration pipeline operates for this environment: deployment tool URLs, per-namespace deployment policies, notification channels, test system settings, pipeline job references.

**runtime** - Parameters that configure application behavior while it is already running. Applied via Consul without redeployment, allowing live configuration changes without a new Helm release.

**cleanup** - Parameters needed during uninstall and teardown operations.

**topology** - A structural description of the environment: which namespaces exist, how they relate (composite structure, BG domain), and cluster connection details. Unlike the other contexts, `topology` is not tied to a single consumer - any tool that needs to understand the environment layout may read it.

Each context that contains sensitive parameters includes a `credentials.yaml` alongside the main values file. `credentials.yaml` holds parameters whose values are defined using credential macros in the Environment Instance - those values are resolved and SOPS-encrypted in the output. The unencrypted values are never written to disk.

In this tutorial you will focus on the `deployment`, `topology`, and `pipeline` contexts, which are the most commonly used.

## Step 2: Generate the Effective Set

Trigger the Instance pipeline with the following variables:

```text
ENV_NAMES:                prod-cluster/prod-01
GENERATE_EFFECTIVE_SET:   true
EFFECTIVE_SET_CONFIG:     {"enable_traceability":true}
```

`EFFECTIVE_SET_CONFIG` is a JSON object. In the pipeline UI you enter it as-is: `{"enable_traceability":true}`. In a YAML file (e.g. `.gitlab-ci.yml`) the value must be quoted and the inner quotes escaped: `"{\"enable_traceability\":true}"`. All fields are optional:

| Field                           | Default  | Description                                                     |
|---------------------------------|----------|-----------------------------------------------------------------|
| `version`                       | `v2.0`   | Effective Set version. `v1.0` is legacy                         |
| `enable_traceability`           | `false`  | Add source comments showing each parameter's origin object type |
| `app_chart_validation`          | `true`   | Fail if any application is not an app chart application         |
| `effective_set_expiry`          | `1 hour` | CI artifact retention time                                      |
| `contexts.pipeline.consumers[]` | none     | Consumer-specific pipeline context schemas                      |

`contexts.pipeline.consumers` adds consumer-specific pipeline sub context files alongside the generic `pipeline/parameters.yaml`. For example, adding `{"name":"dcl","version":"v1.0"}` produces `pipeline/dcl-parameters.yaml` and `pipeline/dcl-credentials.yaml`. See [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md#effective_set_config) for the full schema.

With `GENERATE_EFFECTIVE_SET: true` set, the pipeline runs:

```text
generate_effective_set → git_commit
```

`generate_effective_set` reads the Environment Instance files that are already in the repository (produced by a previous `env_build` run) and writes the Effective Set on top of them. It does not rebuild the Environment Instance itself.

After the pipeline completes, pull the latest changes from the repository:

```bash
git pull origin main
```

The generated files are now committed at `environments/prod-cluster/prod-01/effective-set/`. The directory structure for our scenario looks like this:

```text
effective-set/
├── deployment/
│   ├── mapping.yaml
│   ├── bss/
│   │   └── Cloud-BSS/
│   │       └── values/
│   │           ├── collision-credentials.yaml
│   │           ├── collision-deployment-parameters.yaml
│   │           ├── credentials.yaml
│   │           ├── custom-params.yaml
│   │           ├── deploy-descriptor.yaml
│   │           ├── deployment-parameters.yaml
│   │           └── per-service-parameters/
│   │               └── cloud-bss-7b/
│   │                   └── deployment-parameters.yaml
│   └── oss/
│       └── cloud-oss/
│           └── values/
│               ├── collision-credentials.yaml
│               ├── collision-deployment-parameters.yaml
│               ├── credentials.yaml
│               ├── custom-params.yaml
│               ├── deploy-descriptor.yaml
│               ├── deployment-parameters.yaml
│               └── per-service-parameters/
│                   └── cloud-oss/
│                       └── deployment-parameters.yaml
├── topology/
│   ├── credentials.yaml
│   └── parameters.yaml
├── pipeline/
│   ├── credentials.yaml
│   └── parameters.yaml
├── runtime/
│   ├── mapping.yaml
│   ├── bss/
│   │   └── Cloud-BSS/
│   │       ├── credentials.yaml
│   │       └── parameters.yaml
│   └── oss/
│       └── cloud-oss/
│           ├── credentials.yaml
│           └── parameters.yaml
└── cleanup/
    ├── mapping.yaml
    ├── bss/
    │   ├── credentials.yaml
    │   └── parameters.yaml
    └── oss/
        ├── credentials.yaml
        └── parameters.yaml
```

`mapping.yaml` appears in the `deployment/`, `runtime/`, and `cleanup/` contexts. It maps each namespace name to its folder path within the context, so consumers can locate the right directory without inferring naming conventions. For example, a consumer looking up parameters for the `prod-01-bss` namespace reads `mapping.yaml` to find the folder `bss/`.

The `per-service-parameters/` subfolder name is application name normalized to comply with Kubernetes naming rules. `Cloud-BSS` becomes `cloud-bss-7b`; `cloud-oss` is already lowercase and stays unchanged. [Section 4.1](#41-resource-sizing-in-per-service-parameters) explains this in detail.

> [!NOTE]
> This tutorial simplifies two things compared to real usage:
>
> - The SD is already committed to the repository, so no SD parameters are needed.
> - Only `generate_effective_set` is triggered; `env_build` does not run.
>
> In practice, Effective Set generation is a pre-step before deployment.
> A deployment typically means a new application version or a new application being added - the SD carries exactly this information: which applications to deploy and at which versions.
> At the same time, `env_build` ensures the Environment Instance reflects the latest template version before the Effective Set is calculated.
> These steps therefore go together in a single run:
>
> ```text
> ENV_NAMES:                prod-cluster/prod-01
> ENV_BUILDER:              true
> ENV_TEMPLATE_VERSION:     env-template:2.5.0
> GENERATE_EFFECTIVE_SET:   true
> EFFECTIVE_SET_CONFIG:     {"enable_traceability":true}
> SD_SOURCE_TYPE:           artifact
> SD_VERSION:               sd:1.2.3
> ```

## Step 3: Read the Deployment Context

The deployment context is organized by namespace and application - each folder name corresponds to the `deployPostfix` value from the SD:

```text
effective-set/deployment/
└── <deployPostfix>/        ← namespace folder, e.g. bss
    └── <application>/      ← application name, e.g. Cloud-BSS
        └── values/         ← Helm values files applied in priority order
```

Navigate to the `Cloud-BSS` application folder:

```text
environments/prod-cluster/prod-01/effective-set/deployment/bss/Cloud-BSS/values/
```

For each application the deployer receives a set of values files applied in this priority order (last file wins):

```text
deploy-descriptor.yaml                                       ← SBOM-derived artifact metadata (image names, tags, chart coordinates)
credentials.yaml                                             ← sensitive user defined params; SOPS-encrypted if configured
deployment-parameters.yaml                                   ← user defined params
collision-deployment-parameters.yaml                         ← params whose key matches a service name (moved to avoid Helm structure conflicts)
collision-credentials.yaml                                   ← sensitive collision params; SOPS-encrypted if configured
per-service-parameters/<app-name>/deployment-parameters.yaml ← per-microservice resource sizing (all services as keys)
custom-params.yaml                                           ← CUSTOM_PARAMS pipeline variable; highest priority
```

`deploy-descriptor.yaml` is generated entirely from the Application SBOM. It contains artifact metadata - Docker image names and tags, Helm chart coordinates, Git revision. It is read-only; users cannot override its values.

With `enable_traceability: true`, every parameter in `deployment-parameters.yaml` carries an inline comment identifying its source object type. [Step 4](#step-4-trace-how-parameters-flow-into-the-effective-set) traces these in detail.

## Step 4: Trace How Parameters Flow Into the Effective Set

With traceability enabled, every parameter in `deployment-parameters.yaml` carries a comment that identifies its source object type. This is the primary tool for debugging a wrong value: find the parameter, read the comment, go to that object.

Open `environments/prod-cluster/prod-01/effective-set/deployment/bss/Cloud-BSS/values/deployment-parameters.yaml`:

```yaml
ARGOCD_URL: "https://argocd.prod-cluster.example.com" #cloud
PAAS_PLATFORM: "KUBERNETES" #cloud
BSS_NAMESPACE: "prod-01-bss" #namespace
CUSTOM_HOST: "bss.prod-cluster.example.com" #namespace
SERVICE_TYPE: "ClusterIP" #application
HEALTH_CHECK_PATH: "/api/health" #application
MANAGED_BY: "argocd" #envgene default
```

Each comment tells you where to look:

| Comment                | Source object           | Where to look in the Instance                               |
|------------------------|-------------------------|-------------------------------------------------------------|
| `#tenant`              | Tenant object           | `tenant.yml` or its ParameterSets                           |
| `#cloud`               | Cloud object            | `cloud.yml` or its ParameterSets                            |
| `#namespace`           | Namespace object        | `Namespaces/<namespace>/namespace.yml` or its ParameterSets |
| `#application`         | Application object      | `Namespaces/<namespace>/Applications/<application>.yml`     |
| `#sbom`                | Application SBOM        | SBOM in `sboms/` - not directly editable                    |
| `#composite-structure` | Composite Structure obj | `composite_structure.yml`                                   |
| `#bg-domain`           | BG Domain object        | `bg_domain.yml`                                             |
| `#envgene calculated`  | Computed by EnvGene     | Not editable - derived value                                |
| `#envgene default`     | EnvGene built-in        | Internal default - not configurable                         |
| `#custom params`       | `CUSTOM_PARAMS` var     | Pipeline variable - highest priority                        |

For the complete list of comment types see the [Calculator CLI Reference](../features/calculator-cli.md#version-20-traceability-comments).

### 4.1 Resource sizing in per-service-parameters

The `per-service-parameters/cloud-bss-7b/deployment-parameters.yaml` file uses different comment types because its values come from the SBOM and Resource Profile Overrides:

```yaml
bss-api:
  CPU_REQUEST: 250m #rp-baseline: prod
  CPU_LIMIT: 500m #rp-baseline: prod
  REPLICAS: 2 #rp-baseline: prod
bss-processor:
  CPU_REQUEST: 500m #rp-baseline: prod
  CPU_LIMIT: 2000m #rp-baseline: prod
  REPLICAS: 5 #rp-override: prod-bss-override
```

`#rp-baseline: prod` - value comes from the Resource Profile Baseline named `prod` in the application SBOM. To change it, add a Resource Profile Override in the Instance.

`#rp-override: prod-bss-override` - the SBOM baseline was overridden by `Profiles/prod-bss-override.yml` in the Instance.

> [!NOTE]
> If the application is not an app chart (its Helm chart is a flat chart, not an umbrella chart with nested sub-charts), the structure differs: each microservice gets its own subfolder with a flat (non-nested) `deployment-parameters.yaml`. See [Calculator CLI Reference](/docs/features/calculator-cli.md) for details.

## Step 5: Read the Topology Context

Open:

```text
effective-set/topology/parameters.yaml
```

The topology context describes the environment's structural layout. It is not per-application - it covers the entire environment:

```yaml
cluster:
  api_url: api.prod-cluster.example.com
  api_port: "6443"
  protocol: HTTPS
  public_url: prod-cluster.example.com

environments:
  prod-cluster/prod-01:
    namespaces:
      prod-01-bss:
        deployPostfix: bss
      prod-01-oss:
        deployPostfix: oss

composite_structure: {}

bg_domain: {}
```

The topology context is consumed by orchestration tools that need to understand which namespaces belong to an environment, how they relate to each other, and cluster connection details. `composite_structure` and `bg_domain` are empty when not configured for this environment.

The `topology/credentials.yaml` file contains per-namespace Kubernetes service account tokens (SOPS-encrypted):

```yaml
k8s_tokens:
  prod-01-bss: ENC[AES256_GCM,data:...]
  prod-01-oss: ENC[AES256_GCM,data:...]
```

## Step 6: Read the Pipeline Context

Open:

```text
effective-set/pipeline/parameters.yaml
```

The pipeline context contains parameters consumed by orchestration pipelines - values that control how downstream pipeline jobs run rather than how the application itself is configured:

```yaml
DCL_CONFIG_ARGOCD_URL: "https://argocd-server.prod-cluster.example.com"
DCL_CONFIG_ARGOCD_PROJECT: "infra"
DCL_CONFIG_DOCKER_REGISTRY: "registry.example.com:17014"
DCL_CONFIG_REGISTRY_URL: "https://registry.example.com"
DCL_CONFIG_SKIP_CREDENTIALS_ENCRYPTION: false
DCL_CONFIG_SOPS_DCL2ARGO_AGE_PUBLIC_KEY: "age1abc123..."
DCL_GIT_BRANCH: master
DCL_GIT_URL: "https://git.example.com/pipelines/gitlab-dcl"
```

These parameters come from the `e2eParameters` sections of the Cloud object in the Environment Instance. Sensitive values (ArgoCD credentials, SSO secrets) are split into `pipeline/credentials.yaml` which is SOPS-encrypted.

> [!NOTE]
> The attribute is called `e2eParameters` for historical reasons. They are general-purpose pipeline orchestration parameters.

If consumer-specific contexts were configured in `EFFECTIVE_SET_CONFIG`, their files appear alongside the generic ones:

```text
pipeline/
├── parameters.yaml
├── credentials.yaml
├── e2e-runner-parameters.yaml   ← consumer-specific
└── e2e-runner-credentials.yaml  ← consumer-specific
```

The consumer-specific files contain a validated subset of the pipeline parameters, filtered through the consumer's JSON schema.

## Step 7: Understand Parameter Priority

When the same parameter key is defined at multiple levels, EnvGene applies a strict priority order to decide which value wins. From highest to lowest:

1. **Custom Params** (`CUSTOM_PARAMS` pipeline variable) - highest, always wins
2. **Resource Profile Override** - instance-level (in `Profiles/`) takes precedence over template-level
3. **Resource Profile Baseline** (from SBOM)
4. **Application object** (`deployParameters` in `Applications/<app>.yml`)
5. **Namespace object** (`deployParameters` in `namespace.yml`)
6. **Cloud object** (`deployParameters` in `cloud.yml`)
7. **Tenant object** (`deployParameters` in `tenant.yml`)

A practical example: if `Tenant` defines `LOG_LEVEL: INFO` and `Namespace` defines `LOG_LEVEL: DEBUG`, the value in `deployment-parameters.yaml` will be `DEBUG` because Namespace has higher priority than Tenant.

### 7.1 Verify priority with traceability comments

Suppose `deployment-parameters.yaml` for `Cloud-BSS` shows:

```yaml
LOG_LEVEL: "DEBUG" #namespace
```

The comment `#namespace` tells you the value is defined at the namespace level - either directly in `namespace.yml` or in a ParameterSet referenced by it. To change it, check `namespace.yml`:

```text
environments/prod-cluster/prod-01/Namespaces/bss/namespace.yml
```

or the ParameterSet files under `Inventory/parameters/` that are assigned to the `bss` namespace. After editing, regenerate the Effective Set.

The same logic applies to other comments:

| Comment                  | Where to look                                             |
|--------------------------|-----------------------------------------------------------|
| `#tenant`                | `tenant.yml` or ParameterSets assigned to Tenant          |
| `#cloud`                 | `cloud.yml` or ParameterSets assigned to Cloud            |
| `#namespace`             | `namespace.yml` or ParameterSets assigned to Namespace    |
| `#application`           | Application object in `Applications/`                     |
| `#sbom`                  | Application SBOM in `sboms/` - not directly editable      |
| `#rp-baseline: <name>`   | SBOM baseline - override with a Resource Profile Override |
| `#rp-override: <name>`   | `Profiles/` in the Instance or Template Repository        |
| `#envgene calculated`    | Derived by EnvGene - not directly editable                |
| `#envgene default`       | Internal default - not configurable                       |
| `#custom params`         | `CUSTOM_PARAMS` pipeline variable - highest priority      |

## Step 8: Understand What Triggers a Regeneration

The Effective Set becomes stale whenever any of its inputs change. You must regenerate it in these situations:

| Change                                               | Required action                            |
|------------------------------------------------------|--------------------------------------------|
| Environment Specific ParameterSet modified           | Regenerate Effective Set                   |
| Template ParameterSet changed (new template version) | Regenerate both Instance and Effective Set |
| Resource Profile Override modified                   | Regenerate Effective Set                   |
| Solution Descriptor applications changed             | Update SD, regenerate Effective Set        |
| Cloud Passport data updated                          | Regenerate both Instance and Effective Set |
| Credentials rotated                                  | Regenerate Effective Set                   |

## Summary

In this tutorial you traced the full Effective Set lifecycle for the BSS solution:

- **What it is** - the final merged parameter tree for one environment, written to `effective-set/` and read by ArgoCD and other consumers.
- **Five contexts** - `deployment` (application parameters and artifacts), `pipeline` (CI/CD parameters), `topology` (cluster layout and structure), `runtime` (runtime management parameters), `cleanup` (teardown parameters).
- **Parameter flow** - Tenant → Cloud → Namespace → Application → SBOM → Resource Profile Override, with each level overriding the previous one.
- **deployment-parameters.yaml** - the merged application parameters; traceability comments show which object type (Cloud, Namespace, Application, etc.) contributed each value.
- **deploy-descriptor.yaml** - SBOM-derived artifact metadata consumed by the deployer to know which Docker images and charts to install.
- **per-service-parameters** - resource sizing per microservice; `#rp-baseline` and `#rp-override` comments identify the source.
- **topology/parameters.yaml** - cluster structure: environment list, namespace mapping, composite structure, BG domain.
- **Priority order** - Custom Params win over everything; Instance ParameterSets override Template ParameterSets; Namespace overrides Cloud overrides Tenant.
- **Regeneration triggers** - any change to inputs (ParameterSets, Resource Profiles, SBOMs, SD, credentials) requires a new Effective Set generation.

**Related documentation:**

- [Calculator CLI](/docs/features/calculator-cli.md)
- [How to Generate an Effective Set](/docs/how-to/generate-effective-set.md)
- [How to Override Template Parameters](/docs/how-to/environment-specific-parameters.md)
- [Tutorial: Managing Resource Profiles](/docs/tutorials/resource-profiles.md)
- [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md)
