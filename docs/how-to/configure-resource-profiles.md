# Configure resource profiles

- [Configure resource profiles](#configure-resource-profiles)
  - [Description](#description)
  - [How profiles resolve](#how-profiles-resolve)
  - [Scenario 1: Do not manage performance parameters](#scenario-1-do-not-manage-performance-parameters)
  - [Scenario 2: Use a baseline for all environments](#scenario-2-use-a-baseline-for-all-environments)
  - [Scenario 3: Use a different baseline for one environment](#scenario-3-use-a-different-baseline-for-one-environment)
  - [Scenario 4: Use a baseline with custom values for one environment](#scenario-4-use-a-baseline-with-custom-values-for-one-environment)
  - [Scenario 5: Use a baseline with custom values for a cluster](#scenario-5-use-a-baseline-with-custom-values-for-a-cluster)
  - [Scenario 6: Use a baseline with custom values for all environments](#scenario-6-use-a-baseline-with-custom-values-for-all-environments)
  - [Scenario 7: Add custom values for one environment on top of a template override](#scenario-7-add-custom-values-for-one-environment-on-top-of-a-template-override)
  - [Best practices](#best-practices)
  - [Related documentation](#related-documentation)

## Description

This guide shows how to configure resource profiles for environments in EnvGene. Resource profiles
control performance-related parameters such as CPU and memory limits, requests, and replica counts.

A service gets these parameters from two sources: a **baseline** - a named set the application provides
(for example `dev` or `prod`) - and **custom values** you set in an override on top of the baseline. Both
are performance parameters: the baseline is the application's set, custom values are yours.

This guide assumes a Template repository with Cloud and Namespace templates and an Instance repository with at
least one target environment already exist. The baseline names come from the application developer, so check the
application ZIP part if you are unsure which baselines an application defines.

Each scenario below covers a distinct intent - read its "When to use" line to confirm it matches your
situation before following the steps. This guide configures profiles on the namespace.

## How profiles resolve

An override affects a namespace through two things: whether it is associated with that namespace, and what
it carries.

**Association determines what applies.** An override applies to a namespace only when it is referenced by
name: `profile.name` on the namespace or cloud template (a template override), or an entry in
`envSpecificResourceProfiles` in `env_definition.yml` (an environment-specific override). An override file
that nothing references is ignored, wherever it sits.

**Location determines which file a name resolves to.** A referenced environment-specific name is resolved
by searching the environment's `Inventory/resource_profiles/` first, then the cluster scope
(`<cluster>/resource_profiles/`), then the global scope (`environments/resource_profiles/`). The first
match wins, so the most specific scope takes precedence. Placing one file at cluster or global scope lets
several environments reference the same name without copying it.

**What the override carries determines the result.** An override can carry custom values, a `baseline`
name, or both. The `baseline` selects the application's parameter set. Custom values apply on top of the
baseline parameters.

Baseline precedence, highest first: the environment-specific override's baseline, then the template
override's baseline, then the baseline set on the namespace.

For the full resolution rules and the outcome table, see the
[resource profile feature doc](/docs/features/resource-profile.md).

## Scenario 1: Do not manage performance parameters

**When to use:** You do not manage performance parameters for this environment.

Take no action. Omit `profile` from the namespace template and omit `envSpecificResourceProfiles` from
`env_definition.yml`. The application receives no resource profile parameters.

## Scenario 2: Use a baseline for all environments

**When to use:** Every environment of this type should use one of the application's baselines as-is, with no
custom values.

Set `profile.baseline` on the namespace template (do not create an override file and omit `profile.name`):

```yaml
# templates/env_templates/<template-name>/<namespace>.yml.j2
profile:
  baseline: "dev"
```

The baseline value is a free-form string. Use the name the application defines, not a fixed list. The Effective
Set calculator applies the `dev` baseline parameters for each service that defines that baseline. Services that
ship no baselines receive no baseline parameters.

Then release the template and generate an environment against the new template version.

**Sample:** a namespace template that sets only a baseline -
`docs/samples/template-repository/templates/env_templates/simple/billing.yml.j2`.

## Scenario 3: Use a different baseline for one environment

**When to use:** One environment needs a different baseline than the others (for example, the rest use `dev`
and this one needs `prod`).

This scenario assumes the namespace already has a template override (a Template Resource Profile Override,
see Scenario 6). Changing the baseline requires replace mode: your environment-specific override replaces
that template override entirely and sets its own baseline. If the namespace has no template override, use
Scenario 4 (a standalone override) instead.

> [!WARNING]
> Merging a different baseline on top of a template override that sets custom values is the wrong path.
> When the template override sets custom values and its baseline differs from the environment-specific override's
> baseline, environment build warns. Use replace mode.

Create the environment-specific override in the Instance repository, setting only the `baseline`:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/core-prod-override.yml
name: "core-prod-override"
baseline: "prod"
```

The override carries no `applications`, so it sets no custom values. Replace mode drops the template override,
so the environment uses the `prod` baseline with no custom values. Set `baseline` to a baseline the application
defines.

If the new baseline also needs custom values, add an `applications` block to this override, the same shape as
in Scenario 4. Replace mode still applies, so these values are the environment's complete override and nothing
from the template override is kept.

Reference the override in `env_definition.yml` and set replace mode:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  config:
    mergeEnvSpecificResourceProfiles: false
envTemplate:
  envSpecificResourceProfiles:
    core: "core-prod-override"
```

The key under `envSpecificResourceProfiles` is the namespace folder name under `Namespaces/` in the generated
environment instance. Then commit to the Instance repository and trigger environment generation.

**Sample:** a baseline-only override and its replace-mode `env_definition.yml` -
`docs/samples/instance-repository/environments/cluster-01/env-01/`.

## Scenario 4: Use a baseline with custom values for one environment

**When to use:** You need to set custom values for one environment that has no template override yet.

When the namespace template has no `profile.name`, EnvGene attaches this override to the namespace
automatically.

Create the override in the environment's `Inventory/resource_profiles/` folder:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/core-prod-override.yml
name: "core-prod-override"
baseline: "prod"
applications:
  - name: "Core"
    services:
      - name: "core-service"
        parameters:
          - name: "CPU_LIMIT"
            value: "2000m"
          - name: "MEMORY_LIMIT"
            value: "2Gi"
```

Set `baseline` to a baseline the application defines. Reference the override in `env_definition.yml`:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
envTemplate:
  envSpecificResourceProfiles:
    core: "core-prod-override"
```

No `mergeEnvSpecificResourceProfiles` setting is needed. The default (`true`) is fine because there is no
template override to merge with. Then commit to the Instance repository and trigger environment generation.

## Scenario 5: Use a baseline with custom values for a cluster

**When to use:** Every environment in a cluster needs the same custom values.

Place the override at cluster scope. EnvGene searches the most specific location first, so any
environment that has its own override in `Inventory/resource_profiles/` still uses that one instead.

Create the override at cluster scope:

```yaml
# environments/cluster-01/resource_profiles/core-cluster-override.yml
name: "core-cluster-override"
baseline: "prod"
applications:
  - name: "Core"
    services:
      - name: "core-service"
        parameters:
          - name: "CPU_LIMIT"
            value: "1500m"
          - name: "MEMORY_LIMIT"
            value: "1536Mi"
```

In each environment's `env_definition.yml`, reference the override by name:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    core: "core-cluster-override"
```

The file does not need to exist in each environment's folder. EnvGene finds it at cluster scope.
All environments that reference the same name share the same file. Then commit to the Instance repository and
trigger environment generation.

**Sample:** a cluster-scope override -
`docs/samples/instance-repository/environments/cluster-01/resource_profiles/cloud-specific-profile.yml`.

## Scenario 6: Use a baseline with custom values for all environments

**When to use:** Every environment of this type needs the same baseline and the same custom values.

Create a Template Resource Profile Override in the Template repository and reference it via `profile.name`
on the namespace template.

Create the override in the Template repository:

```yaml
# templates/resource_profiles/dev-core-override.yml
name: "dev-core-override"
baseline: "dev"
description: "Dev profile for core namespace"
applications:
  - name: "Core"
    services:
      - name: "core-service"
        parameters:
          - name: "CPU_LIMIT"
            value: "500m"
          - name: "MEMORY_LIMIT"
            value: "512Mi"
          - name: "REPLICAS"
            value: "1"
```

Reference the override via `profile.name` on the namespace template:

```yaml
# templates/env_templates/<template-name>/<namespace>.yml.j2
profile:
  name: "dev-core-override"
  baseline: "dev"
```

Both `profile.name` and `profile.baseline` are optional. Setting `profile.baseline` here makes the namespace
baseline available as the lowest-priority fallback when no override sets one. Then release the template and
generate an environment against the new template version.

**Sample:** template overrides -
`docs/samples/template-repository/templates/resource_profiles/`.

## Scenario 7: Add custom values for one environment on top of a template override

**When to use:** A template override already exists and one environment needs extra custom values on top of it,
keeping the same baseline.

Use MERGE mode (the default). Both overrides must carry the same `baseline`. If you need a
different baseline, use Scenario 3 instead.

This scenario assumes the namespace already has a template override (see Scenario 6).

Create the environment-specific override in the Instance repository:

```yaml
# environments/cluster-01/env-01/Inventory/resource_profiles/core-prod-extra.yml
---
name: "core-prod-extra"
baseline: "prod"
applications:
  - name: "Core"
    services:
      - name: "tenant-manager"
        parameters:
          - name: "REPLICAS"
            value: "3"
```

Set `baseline` to the same value the template override carries. When both overrides set custom values and their
baselines differ, environment build warns. Reference the override in `env_definition.yml` and do not set
`mergeEnvSpecificResourceProfiles` (or set it to `true` explicitly):

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
envTemplate:
  # ...
  envSpecificResourceProfiles:
    core: "core-prod-extra"
```

Then commit to the Instance repository and trigger environment generation.

In the generated environment instance, the result file takes the name of the template override.
The environment-specific entries are merged in: entries the template does not have are added, and
conflicting values use the environment-specific value.

**Sample:** an environment-specific override merged onto a template override -
`docs/samples/instance-repository/environments/cluster-01/env-02/`.

## Best practices

**Set a baseline on every override that sets custom values.** An override that sets custom values but no
`baseline` generates a warning. The `baseline` field is optional in the schema for backward compatibility, but
setting it is mandated by configuration best practice.

**Do not set `baseline: ""`** (empty string). An empty string is treated as absent in the resolution
logic. Omit the field instead if you want no baseline selection.

**Use REPLACE to change the baseline.** Merge mode is the right tool for adding custom values within the
same baseline. Replace mode is the right tool for switching to a different baseline in one environment.

**Prefer namespace scope.** Cloud-level profiles exist for rare cases where no namespace is appropriate.
Use namespace scope for all standard configurations.

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md) - full resolution rules, baseline precedence, and the
  outcome table
- [`env_build` step](/docs/technical-design/instance-pipeline/steps/env-build.md) - how the template and
  environment-specific overrides are combined
- [Calculator CLI](/docs/features/calculator-cli.md) - how the baseline and override are resolved
- [Template Resource Profile Override](/docs/envgene-objects.md#template-resource-profile-override) -
  schema reference
- [Environment Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override) -
  schema reference
- [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) - `env_definition.yml`
  structure and parameters including `mergeEnvSpecificResourceProfiles`
- [ADR-0006](/docs/adr/0006-resource-profile-baseline-override-resolution.md) - design decisions
  behind the resolution model
