# Tutorial: Managing Resource Profiles

- [Tutorial: Managing Resource Profiles](#tutorial-managing-resource-profiles)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Scenario](#scenario)
  - [Step 1: Understand the Resource Profile Hierarchy](#step-1-understand-the-resource-profile-hierarchy)
  - [Step 2: Create a Template Resource Profile Override](#step-2-create-a-template-resource-profile-override)
    - [2.1 Create the override file](#21-create-the-override-file)
    - [2.2 Reference the profile in a Namespace template](#22-reference-the-profile-in-a-namespace-template)
  - [Step 3: Use `template_override` to Differentiate Template Profiles](#step-3-use-template_override-to-differentiate-template-profiles)
  - [Step 4: Use `overrides-parent` in a Composed Template](#step-4-use-overrides-parent-in-a-composed-template)
  - [Step 5: Add an Environment-Specific Override in the Instance Repository](#step-5-add-an-environment-specific-override-in-the-instance-repository)
    - [5.1 Choose the right scope](#51-choose-the-right-scope)
    - [5.2 Create the env-specific override file](#52-create-the-env-specific-override-file)
    - [5.3 Reference the override in `env_definition.yml`](#53-reference-the-override-in-env_definitionyml)
  - [Step 6: Override the Override for a Single Environment](#step-6-override-the-override-for-a-single-environment)
  - [Step 7: Verify the Result](#step-7-verify-the-result)
    - [7.1 Profile Override file in `Profiles/`](#71-profile-override-file-in-profiles)
    - [7.2 Effective Set](#72-effective-set)
  - [Summary](#summary)

## What You Will Learn

By the end of this tutorial you will know how to:

- Read and understand a Resource Profile Baseline distributed with an application artifact
- Create a Template Resource Profile Override in the Template Repository
- Apply different profiles to different environment types without duplicating templates
- Add an environment-specific override in the Instance Repository
- Override the override for a single environment

## Prerequisites

- A working Template Repository with Cloud and at least one Namespace template
- A working Instance Repository with at least one environment
- Basic familiarity with EnvGene template and instance repository structure

## Scenario

You manage a solution called BSS that consists of one application (`Cloud-BSS`) with a service called `bss-processor`. The solution is deployed to two types of environments: `dev` and `prod`. You want to:

1. Apply modest, developer-friendly resource limits to all dev environments.
2. Apply production-grade resource limits to all prod environments.
3. Temporarily double the CPU limit for a single environment called `prod-01` during a load test.

## Step 1: Understand the Resource Profile Hierarchy

EnvGene manages performance parameters (CPU, memory, replicas, etc.) through a three-level hierarchy:

| Level | Name                                               | Where it lives                                             | Who controls it       |
|-------|----------------------------------------------------|------------------------------------------------------------|-----------------------|
| 1     | Resource Profile **Baseline**                      | Application SBOM artifact                                  | Application developer |
| 2     | **Template** Resource Profile Override             | Template Repository `/templates/resource_profiles/`        | Template configurator |
| 3     | **Environment-Specific** Resource Profile Override | Instance Repository `/environments/.../resource_profiles/` | Instance configurator |

Each level overrides the previous one. The Baseline is the starting point; it ships inside the application (SBOM) and is selected by the name defined in the Cloud or Namespace template (e.g. `dev`, `prod`). You do not edit it.

A typical Baseline embedded in the application looks like this (shown for orientation only - you cannot change it):

```yaml
# Baseline name: "dev"
CPU_REQUEST: 100m
CPU_LIMIT: 500m
MEMORY_REQUEST: 256Mi
MEMORY_LIMIT: 512Mi
REPLICAS: 1
```

> [!NOTE]
> EnvGene also supports dot-notation keys (e.g. `resources.limits.cpu`) in Baselines and Override files
> and resolves them into nested YAML structures.

## Step 2: Create a Template Resource Profile Override

A Template Resource Profile Override lets you tune the Baseline values for all environments that use the same template - without touching the application artifact itself.

### 2.1 Create the override file

Create two files in the Template Repository, one for `dev` and one for `prod`:

**`/templates/resource_profiles/dev-bss-override.yml`**

```yaml
name: "dev-bss-override"
baseline: "dev"
description: "Dev resource profile for BSS processor"
applications:
  - name: "Cloud-BSS"
    services:
      - name: "bss-processor"
        parameters:
          - name: "CPU_REQUEST"
            value: "100m"
          - name: "CPU_LIMIT"
            value: "500m"
          - name: "MEMORY_REQUEST"
            value: "256Mi"
          - name: "MEMORY_LIMIT"
            value: "512Mi"
          - name: "REPLICAS"
            value: 1
```

**`/templates/resource_profiles/prod-bss-override.yml`**

```yaml
name: "prod-bss-override"
baseline: "prod"
description: "Production resource profile for BSS processor"
applications:
  - name: "Cloud-BSS"
    services:
      - name: "bss-processor"
        parameters:
          - name: "CPU_REQUEST"
            value: "2000m"
          - name: "CPU_LIMIT"
            value: "4000m"
          - name: "MEMORY_REQUEST"
            value: "2Gi"
          - name: "MEMORY_LIMIT"
            value: "4Gi"
          - name: "REPLICAS"
            value: 5
```

> The `name` field **must** exactly match the filename without the extension.
> The `baseline` field is informational only and is not processed by EnvGene.

### 2.2 Reference the profile in a Namespace template

Open your BSS Namespace template and add the `profile` section:

**`/templates/env_templates/dev/Namespaces/bss.yml.j2`**

```yaml
---
name: "{{ current_env.environmentName }}-bss"
# ... other required fields ...
profile:
  name: dev-bss-override
  baseline: dev
# ... other required fields ...
```

**`/templates/env_templates/prod/Namespaces/bss.yml.j2`**

```yaml
---
name: "{{ current_env.environmentName }}-bss"
# ... other required fields ...
profile:
  name: prod-bss-override
  baseline: prod
# ... other required fields ...
```

EnvGene reads `profile.name` from the rendered template and looks up the file `<name>.yml` (or `.yaml`) inside `/templates/resource_profiles/`.

## Step 3: Use `template_override` to Differentiate Template Profiles

The two-file approach from Step 2 works, but maintaining separate template files that differ only in the `profile` section does not scale. An alternative is to keep a **single**, profile-neutral base template and assign the profile at the descriptor level using `template_override`.

Replace the two namespace templates from Step 2 with one shared file:

**`/templates/env_templates/base/Namespaces/bss.yml.j2`**

```yaml
---
name: "{{ current_env.environmentName }}-bss"
# ... other required fields ...
# no profile section
```

Then create two Template Descriptors that reference it with different profiles:

**`/templates/env_templates/dev.yml`**

```yaml
tenant: "{{ templates_dir }}/env_templates/base/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/base/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/base/Namespaces/bss.yml.j2"
    template_override:
      profile:
        name: "dev-bss-override"
        baseline: "dev"
```

**`/templates/env_templates/prod.yml`**

```yaml
tenant: "{{ templates_dir }}/env_templates/base/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/base/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/base/Namespaces/bss.yml.j2"
    template_override:
      profile:
        name: "prod-bss-override"
        baseline: "prod"
```

When EnvGene generates an Environment Instance it renders `bss.yml.j2`, then merges the `template_override` block into the result. The final Namespace object gets `profile.name: dev-bss-override` (or `prod-bss-override`), overriding whatever the template originally defined.

`template_override` supports Jinja expressions, so you can also compute profile names dynamically from environment variables.

## Step 4: Use `overrides-parent` in a Composed Template

A different situation arises when you consume a component from an **external artifact** - a parent template referenced via `parent-templates` that you cannot edit directly. `overrides-parent` is the right mechanism for this case: it lets a child Template Descriptor swap or augment the parent's profile without touching the parent artifact.

Suppose a parent template (`bss-product-template:2.0.0`) ships with a namespace whose `profile.name` is `default-bss-override`. A child (project-level) template wants to apply `project-bss-override` instead.

In the **child** Template Descriptor:

```yaml
parent-templates:
  default-bss: bss-product-template:2.0.0

namespaces:
  - name: "{env}-bss"
    parent: default-bss
    overrides-parent:
      profile:
        override-profile-name: "project-bss-override"
        parent-profile-name: "default-bss-override"
        baseline-profile-name: "dev"
        merge-with-parent: true
```

Key fields explained:

| Field                   | Required | Description                                           |
|-------------------------|----------|-------------------------------------------------------|
| `override-profile-name` | Optional | Profile file in the **child** template repository     |
| `parent-profile-name`   | Optional | Profile from the **parent** template to override      |
| `baseline-profile-name` | Optional | Baseline name to set                                  |
| `merge-with-parent`     | Optional | `true`: merge into parent; `false`: replace (default) |

When `merge-with-parent: true` the child's `project-bss-override` values are **merged into** the parent's `default-bss-override`. Only the parameters listed in `project-bss-override` are overwritten; all other parent parameters are preserved.

When `merge-with-parent: false` the parent's profile is completely replaced by `project-bss-override`.

The `overrides-parent` mechanism works for Cloud templates too - place the same `profile` sub-block under `cloud.overrides-parent`.

## Step 5: Add an Environment-Specific Override in the Instance Repository

You can further adjust resource parameters for a specific environment in the Instance Repository without modifying the Template Repository at all.

### 5.1 Choose the right scope

Place the override file in the location that matches the desired scope:

| Location                                                        | Scope           | Use When                     |
|-----------------------------------------------------------------|-----------------|------------------------------|
| `/environments/<cluster>/<env>/Inventory/resource_profiles/`    | One environment | Env-specific tuning          |
| `/environments/<cluster>/resource_profiles/`                    | Cluster-wide    | All envs in cluster          |
| `/environments/resource_profiles/`                              | Global          | All envs in the repository   |

When an environment references a file by name (via `envSpecificResourceProfiles`), EnvGene searches these three locations **from most specific to most general** and uses the first file it finds with that name.

**How to decide:**

Ask yourself: *which environments need this override?*

- **One specific environment** - use the environment-specific path. Changes stay isolated and do not affect any neighbor
- **All environments in a cluster** - use the cluster-wide path. One file covers all environments in that cluster without repeating the file per environment
- **All environments in the repository** - use the global path

Prefer the **broadest scope that still makes sense** to avoid duplicating files.

> [!NOTE]
> The file must still be **referenced by name** in each environment's `env_definition.yml` via `envTemplate.envSpecificResourceProfiles`. The location only determines *which file with that name* is actually used when EnvGene finds multiple files with the same name at different levels.

<!-- -->

> [!WARNING]
> Placing files with the **same name** at different levels (e.g. a cluster-wide file and an env-specific file with the identical name) is technically supported but makes troubleshooting harder: reading `bss: "prod-cluster-bss"` in `env_definition.yml` gives no indication that a shadow file exists and silently takes priority. **Prefer distinct names** and reference the correct name explicitly - this makes the active override immediately obvious from the inventory alone.

### 5.2 Create the env-specific override file

You want all production environments to use 6 replicas. Create a cluster-wide override:

**`/environments/prod-cluster/resource_profiles/prod-cluster-bss.yml`**

```yaml
name: "prod-cluster-bss"
baseline: "prod"
description: "Cluster-wide production tuning for BSS"
applications:
  - name: "Cloud-BSS"
    services:
      - name: "bss-processor"
        parameters:
          - name: "REPLICAS"
            value: 6
          - name: "MEMORY_LIMIT"
            value: "6Gi"
```

### 5.3 Reference the override in `env_definition.yml`

Update the environment inventory for each environment in `prod-cluster`. Because the file is at cluster level, any environment that references `prod-cluster-bss` will find it automatically via location priority.

**`/environments/prod-cluster/prod-01/Inventory/env_definition.yml`**

```yaml
envTemplate:
  envSpecificResourceProfiles:
    bss: "prod-cluster-bss"
```

The key (`bss`) must match the **namespace template name** as defined in the environment template. The value is the filename without the extension.

By default (`mergeEnvSpecificResourceProfiles: true`) EnvGene **merges** the env-specific file into the template override. The `REPLICAS: 6` and `MEMORY_LIMIT: 6Gi` from `prod-cluster-bss` are applied on top of `prod-bss-override`; all other parameters from the template override are preserved. The resulting Resource Profile Override keeps the name of the Template Override.

To **replace** the template override entirely instead of merging, set:

```yaml
inventory:
  config:
    mergeEnvSpecificResourceProfiles: false
```

In this case the resulting Resource Profile Override keeps the name of the env-specific file.

## Step 6: Override the Override for a Single Environment

`prod-01` needs to double its CPU limit for an upcoming load test, while all other `prod-cluster` environments keep the cluster-wide profile.

The recommended approach is to give the env-specific file a **distinct name** and reference it explicitly in `env_definition.yml`. This makes the active override immediately visible in the inventory without having to inspect the filesystem.

Create the file at the environment-specific path:

**`/environments/prod-cluster/prod-01/Inventory/resource_profiles/prod-01-bss-loadtest.yml`**

```yaml
name: "prod-01-bss-loadtest"
baseline: "prod"
description: "Temporary load-test profile for prod-01"
applications:
  - name: "Cloud-BSS"
    services:
      - name: "bss-processor"
        parameters:
          - name: "REPLICAS"
            value: 6
          - name: "CPU_REQUEST"
            value: "4000m"
          - name: "CPU_LIMIT"
            value: "8000m"
          - name: "MEMORY_LIMIT"
            value: "6Gi"
```

Then update `env_definition.yml` for `prod-01` to point to the new file:

**`/environments/prod-cluster/prod-01/Inventory/env_definition.yml`**

```yaml
envTemplate:
  envSpecificResourceProfiles:
    bss: "prod-01-bss-loadtest"
```

EnvGene finds `prod-01-bss-loadtest.yml` at the env-specific path and applies it. All other environments in `prod-cluster` still reference `prod-cluster-bss` and are unaffected.

> [!WARNING]
> An alternative is to create the env-specific file with the **same name** as the cluster-wide file (`prod-cluster-bss.yml`) and skip the `env_definition.yml` change entirely. EnvGene will silently pick up the more specific copy due to location priority. Avoid this pattern: when reading the inventory you cannot tell which file is actually active, which makes incidents significantly harder to diagnose.

## Step 7: Verify the Result

After committing your changes, trigger environment generation and inspect two artifacts.

### 7.1 Profile Override file in `Profiles/`

The name of the resulting file in `Profiles/` depends on the combination mode:

| `mergeEnvSpecificResourceProfiles` | Resulting filename in `Profiles/`           |
|------------------------------------|---------------------------------------------|
| `true` (default)                   | Name of the **template** override           |
| `false`                            | Name of the **env-specific** override       |

In this tutorial the default merge mode is used, so the resulting file keeps the template override name:

```text
environments/prod-cluster/prod-01/Profiles/prod-bss-override.yml
```

Open it to verify the merged result. Parameters that came from `prod-01-bss-loadtest` carry an inline `# from prod-01-bss-loadtest` comment, making it clear which env-specific file contributed each value:

```yaml
applications:
- name: "Cloud-BSS"
  services:
  - name: "bss-processor"
    parameters:
    - name: "REPLICAS"
      value: 6          # from prod-01-bss-loadtest
    - name: "CPU_REQUEST"
      value: "4000m"    # from prod-01-bss-loadtest
    - name: "CPU_LIMIT"
      value: "8000m"    # from prod-01-bss-loadtest
    - name: "MEMORY_REQUEST"
      value: "2Gi"
    - name: "MEMORY_LIMIT"
      value: "6Gi"      # from prod-01-bss-loadtest
```

`MEMORY_REQUEST` has no comment - it was not present in `prod-01-bss-loadtest` and was kept unchanged from the template override.

### 7.2 Effective Set

Then inspect the per-service deployment parameters in the Effective Set:

```text
environments/prod-cluster/prod-01/effective-set/deployment/bss/Cloud-BSS/values/per-service-parameters/bss-processor/deployment-parameters.yaml
```

Each parameter line carries an inline traceability comment showing its ultimate source after baseline + override resolution:

```yaml
bss-processor:
  REPLICAS: 6 #rp-override: prod-bss-override
  CPU_REQUEST: 4000m #rp-override: prod-bss-override
  CPU_LIMIT: 8000m #rp-override: prod-bss-override
  MEMORY_REQUEST: 2Gi #rp-override: prod-bss-override
  MEMORY_LIMIT: 6Gi #rp-override: prod-bss-override
  HPA_ENABLED: false #rp-baseline: prod
```

The two comment formats:

| Comment                | Meaning                                                            |
|------------------------|--------------------------------------------------------------------|
| `#rp-baseline: <name>` | Value comes from the Baseline in the application SBOM              |
| `#rp-override: <name>` | Value was set or overridden by the named Resource Profile Override |

- **Effective Set comment** - shows which `Profiles/` file contributed the value.
- **`Profiles/` comment** (`# from ...`) - shows which env-specific file overrode that value inside the Profile Override.

This makes troubleshooting straightforward: if a service is using unexpected resource values, open the Effective Set file, find the parameter, read the comment, and go directly to the source.

## Summary

In this tutorial you walked through the full resource profile management workflow:

- **Baseline** - ships with the application artifact; defines starting performance parameters; read-only from EnvGene's perspective.
- **Template Resource Profile Override** - lives in `/templates/resource_profiles/`; referenced by `profile.name` in Cloud/Namespace templates; applies to all environments using the same template.
- **`template_override`** - replace two near-identical template files with a single base template; assign different profiles in `dev.yml` / `prod.yml` Template Descriptors via the `template_override.profile` block.
- **`overrides-parent`** - when consuming an external versioned parent template artifact, swap or augment its profile in the child Template Descriptor without editing the parent artifact.
- **Environment-Specific Override** - lives in the Instance Repository; referenced via `envSpecificResourceProfiles` in `env_definition.yml`; merged into or replaces the template override depending on `mergeEnvSpecificResourceProfiles`.
- **Override of override** - give the env-specific file a distinct name and reference it explicitly in `env_definition.yml`; use the environment-specific path (`/environments/<cluster>/<env>/Inventory/resource_profiles/`) to scope it to one environment, leaving all others unaffected.

**Related documentation:**

- [Resource Profile Feature Documentation](/docs/features/resource-profile.md)
- [How to Configure Resource Profiles](/docs/how-to/configure-resource-profiles.md)
- [Template Resource Profile Override Schema](/docs/envgene-objects.md#template-resource-profile-override)
- [Environment Specific Resource Profile Override Schema](/docs/envgene-objects.md#environment-specific-resource-profile-override)
- [Template Override Feature](/docs/features/template-override.md)
- [Template Composition Feature](/docs/features/template-composition.md)
- [Environment Inventory Reference](/docs/envgene-configs.md#env_definitionyml)
