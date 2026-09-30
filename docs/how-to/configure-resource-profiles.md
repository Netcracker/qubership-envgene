# How to Configure Resource Profiles for Different Environment Types

- [How to Configure Resource Profiles for Different Environment Types](#how-to-configure-resource-profiles-for-different-environment-types)
  - [Running this guide](#running-this-guide)
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
  - [Verification](#verification)
  - [Related Documentation](#related-documentation)

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename configure-resource-profiles.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

Steps marked **Manual step — cannot be automated** are blockquotes — runme skips them automatically.

---

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
3. Git and Node.js (v16+) available locally.

Verify tools are available:

```bash
git --version
# Expected: git version x.x.x
node --version
# Expected: v16.x.x or higher
```

---

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required for | Example | Description |
|---|---|---|---|
| `PROFILE_NAME` | Option 1 | `dev-core-profile` | Profile file name without extension (Template Repository) |
| `CLUSTER_NAME` | Option 2 | `prod-cluster` | Directory name under `environments/` |
| `ENV_NAME` | Option 2 | `prod-env-01` | Directory name under `environments/<cluster>/` |
| `PROFILE_OVERRIDE_NAME` | Option 2 | `core-prod-override` | Profile override file name without extension |

**Template for Option 1 (Template Repository)** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":true,"name":"input-template-option1"}
PROFILE_NAME=dev-core-profile
```

**Template for Option 2 (Instance Repository)**:

```bash {"excludeFromRunAll":true,"name":"input-template-option2"}
CLUSTER_NAME=prod-cluster
ENV_NAME=prod-env-01
PROFILE_OVERRIDE_NAME=core-prod-override
```

Validate inputs (first runnable cell — fails immediately if a required variable is missing):

```bash
# validate-inputs
if [ -n "$PROFILE_NAME" ]; then
  echo "Option 1 selected: PROFILE_NAME=$PROFILE_NAME"
elif [ -n "$CLUSTER_NAME" ] && [ -n "$ENV_NAME" ] && [ -n "$PROFILE_OVERRIDE_NAME" ]; then
  echo "Option 2 selected: CLUSTER_NAME=$CLUSTER_NAME  ENV_NAME=$ENV_NAME  PROFILE_OVERRIDE_NAME=$PROFILE_OVERRIDE_NAME"
else
  echo "ERROR: Set PROFILE_NAME (Option 1) OR all three of CLUSTER_NAME, ENV_NAME, PROFILE_OVERRIDE_NAME (Option 2)"
  exit 1
fi
```

---

## Option 1: Create Template Resource Profile Override (Template Repository)

Use this when you want to set **default** resource profiles for **all environments** using the same template.

### Step 1: Create Resource Profile Override File

Create the file `templates/resource_profiles/$PROFILE_NAME.yml`:

```bash
if [ -z "$PROFILE_NAME" ]; then echo "Option 1 not selected — skipping"; exit 0; fi
mkdir -p templates/resource_profiles
cat > "templates/resource_profiles/$PROFILE_NAME.yml" <<EOF
name: "$PROFILE_NAME"
baseline: "dev"
description: "Resource profile for $PROFILE_NAME"
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
EOF
```

Verify the file was created:

```bash
if [ -z "$PROFILE_NAME" ]; then exit 0; fi
cat "templates/resource_profiles/$PROFILE_NAME.yml"
# Expected: YAML with actual value for name field (not literal $PROFILE_NAME)
```

### Step 2: Reference Profile in Cloud/Namespace Template

> **Manual step — cannot be automated:** Open the relevant namespace template (e.g. `templates/namespaces/core.yaml`)
> and add a `profile` block referencing `$PROFILE_NAME`:

```yaml {"excludeFromRunAll":true}
profile:
  name: "<your-profile-name>"
  baseline: "dev"
```

> Complete this edit before running the commit step below.

### Step 3: Commit and Publish Template

```bash
if [ -z "$PROFILE_NAME" ]; then echo "Option 1 not selected — skipping"; exit 0; fi
git add "templates/resource_profiles/$PROFILE_NAME.yml"
git commit -m "Add $PROFILE_NAME resource profile override"
git push
```

Verify the commit was created:

```bash
if [ -z "$PROFILE_NAME" ]; then exit 0; fi
git log --oneline -1
# Expected: "Add <profile-name> resource profile override"
```

> **Manual step — cannot be automated:** Publish the new template version following your template publishing process.

---

## Option 2: Create Environment Specific Resource Profile Override (Instance Repository)

Use this when you want to **customize** resource profiles for **specific environments** without modifying the template.

### Step 1: Choose Override Scope

Determine where to place the override based on scope:

| Location                                                                          | Scope                | Use When             |
|-----------------------------------------------------------------------------------|----------------------|----------------------|
| `/environments/$CLUSTER_NAME/$ENV_NAME/Inventory/resource_profiles/` | Environment-specific | One environment only |
| `/environments/$CLUSTER_NAME/resource_profiles/`                      | Cluster-wide         | All environments     |
| `/environments/resource_profiles/`                                    | Global               | Multiple clusters    |

### Step 2: Create Environment Specific Override

Create the profile override file (environment-specific location):

```bash
if [ -z "$CLUSTER_NAME" ]; then echo "Option 2 not selected — skipping"; exit 0; fi
mkdir -p "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/resource_profiles"
cat > "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/resource_profiles/$PROFILE_OVERRIDE_NAME.yml" <<EOF
name: "$PROFILE_OVERRIDE_NAME"
baseline: "prod"
description: "Resource profile override for $ENV_NAME"
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
EOF
```

Verify the file was created:

```bash
if [ -z "$CLUSTER_NAME" ]; then exit 0; fi
cat "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/resource_profiles/$PROFILE_OVERRIDE_NAME.yml"
# Expected: YAML with actual values for name and env fields
```

### Step 3: Reference Override in `env_definition.yml`

> **Manual step — cannot be automated:** Open
> `environments/$CLUSTER_NAME/$ENV_NAME/Inventory/env_definition.yml`
> and add the `envSpecificResourceProfiles` block:

```yaml {"excludeFromRunAll":true}
envTemplate:
  envSpecificResourceProfiles:
    core: "<your-profile-override-name>"
```

> Complete this edit before running the commit step below.

### Step 4: Commit and Test

Stages the profile override file and `env_definition.yml` (if Step 3 was completed):

```bash
if [ -z "$CLUSTER_NAME" ]; then echo "Option 2 not selected — skipping"; exit 0; fi
git add "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/resource_profiles/$PROFILE_OVERRIDE_NAME.yml"
if ! git diff --ignore-all-space --quiet "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/env_definition.yml" 2>/dev/null; then
  git add "environments/$CLUSTER_NAME/$ENV_NAME/Inventory/env_definition.yml"
  echo "env_definition.yml staged (Step 3 changes detected)"
else
  echo "env_definition.yml unchanged — skipping (complete Step 3 first if needed)"
fi
git commit -m "Add $PROFILE_OVERRIDE_NAME resource profile override for $ENV_NAME"
git push
```

Verify the commit was created:

```bash
if [ -z "$CLUSTER_NAME" ]; then exit 0; fi
git log --oneline -1
# Expected: "Add <profile-override-name> resource profile override for <env-name>"
```

> **Manual step — cannot be automated:** Trigger the instance pipeline from the GitLab UI or via the API to
> generate the environment and apply the profile override.

---

## Common Use Cases

### Use Case 1: Development vs Production Profiles

**Template Repository:**

```yaml {"excludeFromRunAll":true}
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

```yaml {"excludeFromRunAll":true}
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

```yaml {"excludeFromRunAll":true}
# /templates/namespaces/billing-dev.yaml
profile:
  name: "dev-baseline"
```

```yaml {"excludeFromRunAll":true}
# /templates/namespaces/billing-prod.yaml
profile:
  name: "prod-baseline"
```

### Use Case 2: Cluster-Wide Resource Scaling

Apply the same resource profile to all environments in a production cluster:

**Instance Repository:** `/environments/prod-cluster-eu/resource_profiles/eu-prod-scaling.yml`

```yaml {"excludeFromRunAll":true}
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

Each environment in `prod-cluster-eu` that references `eu-prod-scaling` via `envTemplate.envSpecificResourceProfiles` in its `env_definition.yml` will use this file. EnvGene finds it automatically via location priority - no need to copy the file per environment, but the reference in `env_definition.yml` is still required.

### Use Case 3: Single Environment Hot Fix

Quickly increase resources for a specific environment under load:

**Instance Repository:** `/environments/prod-cluster/prod-env-03/Inventory/resource_profiles/hotfix-scaling.yml`

```yaml {"excludeFromRunAll":true}
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

## Verification

After configuring resource profiles, verify they are applied correctly.

1. **Generate Environment Instance:**

   > **Manual step — cannot be automated:** Trigger the instance pipeline from the GitLab UI or via the API.
   > Set `ENV_NAMES=$CLUSTER_NAME/$ENV_NAME` as the pipeline variable.

2. **Check Generated Configuration:**

   After the pipeline completes, pull the latest changes:

   ```bash {"excludeFromRunAll":true}
   git pull
   ```

   Confirm the profile was written to the generated output:

   ```bash {"excludeFromRunAll":true}
   ls "environments/$CLUSTER_NAME/$ENV_NAME/Profiles/"
   # Expected: $PROFILE_OVERRIDE_NAME.yml (Option 2) or $PROFILE_NAME.yml (Option 1) appears in the listing
   ```

   Inspect the merged profile:

   ```bash {"excludeFromRunAll":true}
   cat "environments/$CLUSTER_NAME/$ENV_NAME/Profiles/$PROFILE_OVERRIDE_NAME.yml"
   # Expected: merged resource values from the template and override are present
   ```

3. **Verify Merge Result:**

   The generated profile contains merged values from:
   - Baseline Resource Profile (referenced in the `baseline` field — informational only, not processed by EnvGene)
   - Template Resource Profile Override
   - Environment Specific Resource Profile Override

4. **Review Application Manifests:**

   List the generated namespace directories:

   ```bash {"excludeFromRunAll":true}
   ls Namespaces/
   # Expected: namespace directories for your environment are present
   ```

   Find values files and spot-check resource configuration:

   ```bash {"excludeFromRunAll":true}
   find Namespaces/ -name "values.yaml" | head -5
   # Expected: values files for your applications are listed
   ```

---

## Related Documentation

- **[Resource Profile Feature Documentation](/docs/features/resource-profile.md)** — Detailed explanation of how resource profiles work
- **[Template Resource Profile Override](/docs/envgene-objects.md#template-resource-profile-override)** — Complete schema reference for Template Repository profiles
- **[Environment Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)** — Complete schema reference for Instance Repository profiles
- **[Resource Profile Override](/docs/envgene-objects.md#resource-profile-override)** — Generated Environment Instance profile object
- **[Environment Inventory](/docs/envgene-configs.md#env_definitionyml)** — `env_definition.yml` structure and parameters
