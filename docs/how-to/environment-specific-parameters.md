# How to Override Template Parameters for Environment or Group of Environments

- [How to Override Template Parameters for Environment or Group of Environments](#how-to-override-template-parameters-for-environment-or-group-of-environments)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
    - [1. Identify Parameters to Override](#1-identify-parameters-to-override)
    - [2. Create Environment Specific ParameterSet](#2-create-environment-specific-parameterset)
    - [3. Reference ParameterSet in env\_definition.yml](#3-reference-parameterset-in-env_definitionyml)
    - [4. Commit and Regenerate](#4-commit-and-regenerate)
  - [Results](#results)
  - [Common Scenarios](#common-scenarios)
    - [Override for Multiple Namespaces](#override-for-multiple-namespaces)
    - [Override Application-Level Parameters](#override-application-level-parameters)
  - [Best Practices](#best-practices)
  - [Related Documentation](#related-documentation)

## Description

This guide shows how to override template-level parameters for one environment or a group of environments using **Environment Specific ParameterSets** in the Instance Repository.

Template-level parameters are defined in the Template Repository (in Cloud and Namespace templates) in two ways:

- **Directly on the object:** `deployParameters`, `e2eParameters`, `technicalConfigurationParameters` attributes
- **Via ParameterSets:** referenced in `deployParameterSets`, `e2eParameterSets`, `technicalConfigurationParameterSets` arrays

When you need environment-specific values, you create **Environment Specific ParameterSets** in the Instance Repository. By choosing the appropriate **file location**, you control the override scope:

- **Environment-specific** (`/environments/<cluster-name>/<environment-name>/Inventory/parameters/`) — applied to a single environment
- **Cluster-wide** (`/environments/<cluster-name>/parameters/`) — shared across all environments in a cluster
- **Global** (`/environments/parameters/`) — shared across multiple clusters or environments

> [!NOTE]
> **Parameter Contexts:** EnvGene uses three isolated parameter contexts — **Deployment** (`deployParameters`), **Pipeline/E2E** (`e2eParameters`), and **Runtime/Technical Configuration** (`technicalConfigurationParameters`). Each context has its own Template ParameterSets and Environment Specific ParameterSets with separate override mechanisms. See [Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset) for details.

---

## Prerequisites

1. Instance Repository exists with the target environment
2. Template Repository defines base parameters
3. You know:
   - Which namespace or cloud needs parameter overrides
   - Which parameter context to override (deployment, pipeline/end-to-end, or runtime/technical configuration)
   - The namespace identifier (defined by `deploy_postfix` in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor), or by the Namespace template filename without extension)

---

## Steps

### 1. Identify Parameters to Override

Check template parameters in Template Repository:

```yaml
# Template: templates/namespaces/billing.yaml
deployParameters:
  INGRESS_HOST: "billing.example.com"
  FEATURE_NEW_API: "false"
deployParameterSets:
  - billing-deploy-base
```

Identify what needs to change for production:

- `INGRESS_HOST: "billing.prod.example.com"`
- `FEATURE_NEW_API: "true"`

---

### 2. Create Environment Specific ParameterSet

Choose location based on reuse scope:

| Location                                                                | Scope                | Use When                        |
|-------------------------------------------------------------------------|----------------------|---------------------------------|
| `/environments/<cluster-name>/<environment-name>/Inventory/parameters/` | Environment-specific | One environment only            |
| `/environments/<cluster-name>/parameters/`                              | Cluster-wide         | All environments in cluster     |
| `/environments/parameters/`                                             | Global               | Multiple clusters               |

Create ParameterSet file:

```bash
mkdir -p environments/prod-cluster/prod-env/Inventory/parameters
```

**File: `environments/prod-cluster/prod-env/Inventory/parameters/billing-prod-deploy.yml`**

```yaml
name: billing-prod-deploy
parameters:
  INGRESS_HOST: "billing.prod.example.com"
  FEATURE_NEW_API: "true"
  STORAGE_CLASS: "ssd-retain"
  DATABASE_NAME: "billing_prod"
  INGRESS_TLS_ENABLED: "true"
applications:
  - appName: billing-api
    parameters:
      SERVICE_TYPE: "LoadBalancer"
      EXTERNAL_PORT: "8443"
```

> [!IMPORTANT]
> The `name` field must match the filename (without extension).

---

### 3. Reference ParameterSet in env_definition.yml

**File: `environments/prod-cluster/prod-env/Inventory/env_definition.yml`**

```yaml
inventory:
  environmentName: prod-env
  tenantName: my-tenant
envTemplate:
  name: composite-prod
  artifact: deployment-configuration-env-templates:1.2.3
  
  # Override deployment parameters
  envSpecificParamsets:
    billing:                    # Namespace identifier
      - billing-prod-deploy     # ParameterSet name (without .yml)
```

**For different parameter contexts:**

```yaml
envTemplate:
  # Deployment parameters
  envSpecificParamsets:
    billing:
      - billing-prod-deploy
  
  # Pipeline parameters
  envSpecificE2EParamsets:
    billing:
      - billing-prod-e2e
  
  # Runtime parameters
  envSpecificTechnicalParamsets:
    billing:
      - billing-prod-runtime
```

**Multiple ParameterSets:**

```yaml
envSpecificParamsets:
  billing:
    - billing-prod-deploy       # Applied first
    - billing-security-params   # Overrides previous
```

**Cloud-level overrides:**

```yaml
envSpecificParamsets:
  cloud:                        # Special key for Cloud level
    - cloud-prod-overrides
```

---

### 4. Commit and Regenerate

```bash
git add environments/prod-cluster/prod-env/Inventory/
git commit -m "Add billing parameter overrides for prod-env"
git push origin main
```

Trigger pipeline:

```text
ENV_NAMES: prod-cluster/prod-env
ENV_BUILDER: true
```

---

## Results

After Environment Instance generation completes, the **generated Namespace object** contains merged parameters:

> [!NOTE]
> This is a partial example showing merged parameters. A complete Namespace object includes additional required fields: `isServerSideMerge`, `cleanInstallApprovalRequired`, and `mergeDeployParametersAndE2EParameters`. See [Namespace object reference](/docs/envgene-objects.md#namespace) for the full schema.
> [!IMPORTANT]
> **ParameterSets are "expanded" during generation:**
>
> - Parameters from `parameters` section are **merged** into the corresponding object attributes (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`)
> - Parameters from `applications` section create separate **Application objects** in `Namespaces/<namespace>/Applications/<appName>.yml`
> - **ParameterSet reference arrays are cleared** — the generated Namespace contains `deployParameterSets: []` (empty), not the list of ParameterSet names
> - Each parameter includes a **traceability comment** indicating which ParameterSet it came from

```yaml
name: billing
deployParameters:
  # Template parameters (not overridden)
  CACHE_ENABLED: "true"  # paramset: billing-base version: 1.0 source: template
  
  # Overridden parameters
  INGRESS_HOST: "billing.prod.example.com"  # paramset: billing-prod-deploy version: 1.0 source: instance
  FEATURE_NEW_API: "true"                   # paramset: billing-prod-deploy version: 1.0 source: instance
  STORAGE_CLASS: "ssd-retain"               # paramset: billing-prod-deploy version: 1.0 source: instance
  DATABASE_NAME: "billing_prod"             # paramset: billing-prod-deploy version: 1.0 source: instance
  INGRESS_TLS_ENABLED: "true"               # paramset: billing-prod-deploy version: 1.0 source: instance

deployParameterSets: []  # ← Empty after expansion
e2eParameterSets: []     # ← Empty after expansion
technicalConfigurationParameterSets: []  # ← Empty after expansion
```

**What happened to ParameterSets:**

1. ✅ **Template ParameterSets** (`billing-deploy-base`) were processed first
2. ✅ **Environment Specific ParameterSets** (`billing-prod-deploy`) were processed second, overriding template values
3. ✅ All parameters were **extracted and merged** into `deployParameters`
4. ✅ ParameterSet reference arrays (`deployParameterSets`) were **cleared to empty arrays**
5. ✅ Each parameter has a **comment** showing its source ParameterSet and version

---

## Common Scenarios

### Override for Multiple Namespaces

Create shared ParameterSet:

```yaml
# environments/parameters/prod-shared-deploy.yml
name: prod-shared-deploy
parameters:
  INGRESS_TLS_ENABLED: "true"
  STORAGE_CLASS: "ssd-retain"
  MONITORING_ENABLED: "true"
```

Reference in multiple namespaces:

```yaml
envTemplate:
  envSpecificParamsets:
    billing:
      - prod-shared-deploy
      - billing-specific        # Additional overrides
    core:
      - prod-shared-deploy
    oss:
      - prod-shared-deploy
```

---

### Override Application-Level Parameters

Application-level parameters from the `applications` section create separate **Application objects** during generation.

```yaml
# environments/.../parameters/billing-apps-prod.yml
name: billing-apps-prod
parameters:
  INGRESS_HOST: "billing.prod.example.com"
applications:
  - appName: billing-api
    parameters:
      SERVICE_TYPE: "LoadBalancer"
      EXTERNAL_PORT: "443"
      HEALTH_CHECK_PATH: "/api/health"
```

**Result:** A separate Application object is created at:

- **Location:** `Namespaces/billing/Applications/billing-api.yml`
- **Content:** Contains `deployParameters` with `SERVICE_TYPE`, `EXTERNAL_PORT`, `HEALTH_CHECK_PATH`

---

## Best Practices

✅ **DO:**

- Use descriptive names: `billing-prod-deploy.yml`
- Separate contexts in different ParameterSets (one for deployment, one for pipeline, one for runtime)
- Choose appropriate scope (environment/cluster/global)
- Add comments in ParameterSet files explaining why overrides exist
- Use the `applications` section for application-specific parameters that should create Application objects

❌ **DON'T:**

- Mix parameter contexts in one ParameterSet (don't put `deployParameters` and `e2eParameters` in the same file)
- Use generic names: `override.yml`, `params.yml`
- Duplicate same overrides across namespaces (use shared ParameterSets instead)
- Expect to see ParameterSet names in generated Namespace objects (they are expanded during generation)

> [!NOTE]
> **Traceability:** Even though ParameterSets are expanded, you can trace each parameter's origin through the comments added during generation (e.g., `# paramset: billing-prod-deploy version: 1.0 source: instance`)

---

## Related Documentation

- **[Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset)** — Complete reference and schema
- **[Environment Inventory](/docs/envgene-configs.md#env_definitionyml)** — `env_definition.yml` structure and reference
- **[Template ParameterSet](/docs/envgene-objects.md#template-parameterset)** — Template Repository ParameterSets
- **[ParameterSet JSON Schema](/schemas/paramset.schema.json)** — Validation schema
