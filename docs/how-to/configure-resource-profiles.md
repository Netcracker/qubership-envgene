# How to Configure Resource Profiles for Different Environment Types

- [How to Configure Resource Profiles for Different Environment Types](#how-to-configure-resource-profiles-for-different-environment-types)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Option 1: Create Template Resource Profile Override (Template Repository)](#option-1-create-template-resource-profile-override-template-repository)
    - [Step 1: Create Resource Profile Override File](#step-1-create-resource-profile-override-file)
    - [Step 2: Reference Profile in Cloud/Namespace Template](#step-2-reference-profile-in-cloudnamespace-template)
    - [Step 3: Commit and Publish Template](#step-3-commit-and-publish-template)
  - [Option 2: Create Environment Specific Resource Profile Override (Instance Repository)](#option-2-create-environment-specific-resource-profile-override-instance-repository)
    - [Step 1: Choose Override Scope](#step-1-choose-override-scope)
    - [Step 2: Create Environment Specific Override](#step-2-create-environment-specific-override)
    - [Step 3: Reference Override in `env_definition.yml`](#step-3-reference-override-in-env_definitionyml)
    - [Step 4: Commit and Test](#step-4-commit-and-test)
  - [Common Use Cases](#common-use-cases)
    - [Use Case 1: Development vs Production Profiles](#use-case-1-development-vs-production-profiles)
    - [Use Case 2: Cluster-Wide Resource Scaling](#use-case-2-cluster-wide-resource-scaling)
    - [Use Case 3: Single Environment Hot Fix](#use-case-3-single-environment-hot-fix)
  - [Best Practices](#best-practices)
  - [Verification](#verification)
  - [Related Documentation](#related-documentation)

## Description

This guide shows how to configure resource profiles for one environment or a group of environments using Resource Profile Overrides in EnvGene.

Resource profiles control performance-related parameters like resource limits, requests, and scaling settings.

EnvGene uses a layered approach:

- **Template Resource Profile Override** (Template Repository) — common settings for all environments of the same type (e.g., dev, prod)
- **Environment Specific Resource Profile Override** (Instance Repository) — customizations for specific environments or clusters

By choosing the appropriate **file location**, you control the override scope:

- **Environment-specific** (`/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles/`) — applied to a single environment
- **Cluster-wide** (`/environments/<cluster-name>/resource_profiles/`) — shared across all environments in a cluster
- **Global** (`/environments/resource_profiles/`) — shared across multiple clusters or environments

---

## Prerequisites

1. Template Repository exists with Cloud/Namespace templates
2. Instance Repository exists with the target environment
3. Understanding of your application's performance parameters

---

## Option 1: Create Template Resource Profile Override (Template Repository)

Use this when you want to set **default** resource profiles for **all environments** using the same template.

### Step 1: Create Resource Profile Override File

Create a new file in the Template Repository:

**Location:** `/templates/resource_profiles/<profile-name>.yml`

**Example:** `/templates/resource_profiles/dev-core-profile.yml`

```yaml
name: "dev-core-profile"
baseline: "dev"
description: "Development environment resource profile for core services"
applications:
  - name: "Cloud-Core"
    services:
      - name: "facade-operator"
        parameters:
          - name: "resources.limits.cpu"
            value: "500m"
          - name: "resources.limits.memory"
            value: "512Mi"
          - name: "resources.requests.cpu"
            value: "100m"
          - name: "resources.requests.memory"
            value: "256Mi"
      - name: "tenant-manager"
        parameters:
          - name: "resources.limits.memory"
            value: "1Gi"
          - name: "resources.requests.memory"
            value: "512Mi"
          - name: "replicas"
            value: 2
```

### Step 2: Reference Profile in Cloud/Namespace Template

Update your Cloud or Namespace template to reference the profile:

**Example:** `/templates/namespaces/core.yaml`

```yaml
name: "{{ current_env.name }}-core"
type: namespace
profile:
  name: "dev-core-profile"
applications:
  - name: "Cloud-Core"
    # ... application configuration ...
```

### Step 3: Commit and Publish Template

```bash
git add templates/resource_profiles/dev-core-profile.yml
git add templates/namespaces/core.yaml
git commit -m "Add dev-core-profile resource profile override"
git push
```

Publish the new template version following your template publishing process.

---

## Option 2: Create Environment Specific Resource Profile Override (Instance Repository)

Use this when you want to **customize** resource profiles for **specific environments** without modifying the template.

### Step 1: Choose Override Scope

Determine where to place the override based on scope:

| Location                                                                       | Scope                | Use When             |
|--------------------------------------------------------------------------------|----------------------|----------------------|
| `/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles/` | Environment-specific | One environment only |
| `/environments/<cluster-name>/resource_profiles/`                              | Cluster-wide         | All environments     |
| `/environments/resource_profiles/`                                             | Global               | Multiple clusters    |

### Step 2: Create Environment Specific Override

Create a new file in the Instance Repository at the chosen location:

**Example (environment-specific):** `/environments/prod-cluster/prod-env-01/Inventory/resource_profiles/core-prod-override.yml`

```yaml
name: "core-prod-override"
baseline: "prod"
description: "Production resource profile override for core services"
applications:
  - name: "Cloud-Core"
    services:
      - name: "facade-operator"
        parameters:
          - name: "resources.limits.cpu"
            value: "2000m"
          - name: "resources.limits.memory"
            value: "2Gi"
          - name: "resources.requests.cpu"
            value: "1000m"
          - name: "resources.requests.memory"
            value: "1Gi"
      - name: "tenant-manager"
        parameters:
          - name: "resources.limits.memory"
            value: "4Gi"
          - name: "resources.requests.memory"
            value: "2Gi"
          - name: "replicas"
            value: 5
      - name: "identity-provider"
        parameters:
          - name: "PG_MAX_POOL_SIZE"
            value: 100
```

**Example (cluster-wide):** `/environments/prod-cluster/resource_profiles/prod-cluster-baseline.yml`

```yaml
name: "prod-cluster-baseline"
baseline: "prod"
description: "Production cluster baseline resource profile"
applications:
  - name: "Cloud-Core"
    services:
      - name: "facade-operator"
        parameters:
          - name: "resources.limits.cpu"
            value: "1500m"
          - name: "resources.limits.memory"
            value: "1536Mi"
```

### Step 3: Reference Override in `env_definition.yml`

Update the environment inventory to reference the new override:

**File:** `/environments/prod-cluster/prod-env-01/Inventory/env_definition.yml`

```yaml
inventory:
  environmentName: "prod-env-01"
envTemplate:
  envSpecificResourceProfiles:
    core: "core-prod-override"
```

**For multiple namespaces:**

```yaml
envTemplate:
  envSpecificResourceProfiles:
    core: "core-prod-override"
    api: "api-prod-override"
    worker: "worker-prod-override"
```

### Step 4: Commit and Test

```bash
git add environments/prod-cluster/prod-env-01/Inventory/resource_profiles/core-prod-override.yml
git add environments/prod-cluster/prod-env-01/Inventory/env_definition.yml
git commit -m "Add production resource profile override for prod-env-01"
git push
```

Trigger environment generation to verify the changes.

---

## Common Use Cases

### Use Case 1: Development vs Production Profiles

**Template Repository:**

```yaml
# /templates/resource_profiles/dev-baseline.yml
name: "dev-baseline"
applications:
  - name: "billing-api"
    services:
      - name: "api-server"
        parameters:
          - name: "resources.limits.cpu"
            value: "500m"
          - name: "replicas"
            value: 1
```

```yaml
# /templates/resource_profiles/prod-baseline.yml
name: "prod-baseline"
applications:
  - name: "billing-api"
    services:
      - name: "api-server"
        parameters:
          - name: "resources.limits.cpu"
            value: "4000m"
          - name: "replicas"
            value: 5
```

**Reference in templates:**

```yaml
# /templates/namespaces/billing-dev.yaml
profile:
  name: "dev-baseline"
```

```yaml
# /templates/namespaces/billing-prod.yaml
profile:
  name: "prod-baseline"
```

### Use Case 2: Cluster-Wide Resource Scaling

Apply the same resource profile to all environments in a production cluster:

**Instance Repository:** `/environments/prod-cluster-eu/resource_profiles/eu-prod-scaling.yml`

```yaml
name: "eu-prod-scaling"
description: "EU production cluster scaling profile"
applications:
  - name: "billing-api"
    services:
      - name: "api-server"
        parameters:
          - name: "replicas"
            value: 8
          - name: "resources.limits.cpu"
            value: "3000m"
```

All environments in `prod-cluster-eu` will inherit this profile automatically via **file location priority** (cluster-level overrides apply to all environments within that cluster unless overridden at environment level).

### Use Case 3: Single Environment Hot Fix

Quickly increase resources for a specific environment under load:

**Instance Repository:** `/environments/prod-cluster/prod-env-03/Inventory/resource_profiles/hotfix-scaling.yml`

```yaml
name: "hotfix-scaling"
description: "Emergency scaling for prod-env-03"
applications:
  - name: "payment-gateway"
    services:
      - name: "processor"
        parameters:
          - name: "resources.limits.cpu"
            value: "8000m"
          - name: "resources.limits.memory"
            value: "16Gi"
          - name: "replicas"
            value: 10
```

Update `env_definition.yml` for `prod-env-03` only.

---

## Best Practices

1. **Use Template Profiles for Defaults**
   - Define baseline profiles in Template Repository
   - Reference appropriate profiles for environment types (dev, staging, prod)

2. **Use Environment Specific Overrides for Exceptions**
   - Only override when environment needs differ from template defaults
   - Document why specific values are needed

3. **Organize by Scope**

   - **Environment-specific**: High-traffic environments, special requirements
   - **Cluster-wide**: Regional or infrastructure-based differences
   - **Global**: Cross-cluster standards

4. **Use Descriptive Names**
   - Include environment type, purpose, or special notes
   - Examples: `prod-high-traffic`, `eu-cluster-baseline`, `hotfix-temp-scaling`

5. **Document Decisions**
   - Add `description` field explaining why values were chosen
   - Link to performance test results or incidents if applicable

6. **Version Control Best Practices**
   - Keep resource profiles in version control
   - Review changes carefully (resource changes affect costs and stability)
   - Test in lower environments first

---

## Verification

After configuring resource profiles, verify they are applied correctly:

1. **Generate Environment Instance:**

   Trigger the pipeline with `ENV_NAMES=<cluster-name>/<environment-name>`

2. **Check Generated Configuration:**

   Look for the Resource Profile Override in the generated output:

   ```text
   Namespaces/<namespace-name>/resource_profiles/<profile-name>.yml
   ```

3. **Verify Merge Result:**

   The generated profile should contain merged values from:
   - Baseline Resource Profile (referenced in `baseline` field — informational only, not processed by EnvGene)
   - Template Resource Profile Override
   - Environment Specific Resource Profile Override

4. **Review Application Manifests:**

   Check that resource limits/requests appear in generated Helm values or manifests:

   ```text
   Namespaces/<namespace-name>/Applications/<app-name>/values.yaml
   ```

---

## Related Documentation

- **[Resource Profile Feature Documentation](/docs/features/resource-profile.md)** — Detailed explanation of how resource profiles work
- **[Template Resource Profile Override](/docs/envgene-objects.md#template-resource-profile-override)** — Complete schema reference for Template Repository profiles
- **[Environment Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)** — Complete schema reference for Instance Repository profiles
- **[Resource Profile Override](/docs/envgene-objects.md#resource-profile-override)** — Generated Environment Instance profile object
- **[Environment Inventory](/docs/envgene-configs.md#env_definitionyml)** — `env_definition.yml` structure and parameters
