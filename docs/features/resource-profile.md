# Resource profiles

- [Resource profiles](#resource-profiles)
  - [Overview](#overview)
  - [Three-level hierarchy](#three-level-hierarchy)
  - [Environment generation: combining overrides](#environment-generation-combining-overrides)
    - [Template Resource Profile Override](#template-resource-profile-override)
    - [Environment-specific Resource Profile Override](#environment-specific-resource-profile-override)
    - [Merge and replace](#merge-and-replace)
      - [Replace mode](#replace-mode)
      - [Merge mode](#merge-mode)
    - [Naming rules for Resource Profile Override](#naming-rules-for-resource-profile-override)
  - [Effective Set calculation: resolving the profile](#effective-set-calculation-resolving-the-profile)
    - [Side selection](#side-selection)
    - [Baseline resolution within the active side](#baseline-resolution-within-the-active-side)
    - [Applying the override and baseline to each service](#applying-the-override-and-baseline-to-each-service)
    - [Outcome table](#outcome-table)
    - [Result in the Effective Set](#result-in-the-effective-set)
  - [Resolving dot notation](#resolving-dot-notation)
    - [Baseline example](#baseline-example)
    - [Override example](#override-example)
  - [Related documentation](#related-documentation)

## Overview

Performance parameters such as CPU, memory, and replicas are grouped into Resource Profiles, keeping them
separate from other deployment parameters so they can be managed independently.

For the implementation details, see the
[`env_build` step](/docs/technical-design/instance-pipeline/steps/env-build.md) for how overrides are
combined and the [Calculator CLI](/docs/features/calculator-cli.md) for how the baseline and override are
resolved.
For worked scenarios, see [Resource profiles use cases](/docs/use-cases/resource-profiles.md).

## Three-level hierarchy

Resource Profiles are organized into three levels.

A **baseline** is a named set of performance parameters that the application provides for its services.
Application developers create baselines and ship them with the application. An application can define
multiple baselines, each identified by a unique name.

Typical baseline names are:

- `dev` - the minimum resources required for the service to run under low load.
- `prod` - the recommended resources for production workloads.

As an application developer, you can give a baseline any name, for example `small`, `medium`, or
`large`. As a configurator, you can only select a baseline that the application already defines.

A **[template override](/docs/envgene-objects.md#template-resource-profile-override)** (Template Resource
Profile Override) sets custom values on top of a baseline. The configurator creates these in the Template
repository to apply a consistent adjustment across all environments of the same type.

An **[environment-specific override][env-specific-rpo]** (Environment Specific Resource Profile Override)
sets a further set of custom values on top of the template override. The configurator creates these in the
Instance repository for a specific environment.

When generating an [Environment Instance](/docs/envgene-objects.md#environment-instance-objects), the
template and environment-specific overrides are combined (merged or replaced) into a single
[Resource Profile Override](/docs/envgene-objects.md#resource-profile-override). The environment-specific
override wins on conflicts.

When calculating the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20), the Resource
Profile Override and the applicable baseline are combined to produce
[per-service deployment context parameters][per-service-params].
The override always takes precedence over the baseline.

## Environment generation: combining overrides

During environment generation, the template override and the environment-specific override are combined into
one [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) per Cloud or Namespace.

### Template Resource Profile Override

A template override applies to a Namespace or Cloud only when that object references it by name through
its `profile.name` attribute. An override file that no object references is ignored, wherever it sits. Each
override is a YAML file under `/templates/resource_profiles` in the Environment Template repository. The
filename (without the `.yaml` or `.yml` extension) must exactly match the value of `profile.name`.

For example, a Namespace with:

```yaml
profile:
  name: dev-over
```

references `/templates/resource_profiles/dev-over.yaml`.

### Environment-specific Resource Profile Override

An environment-specific override applies to a Namespace or Cloud only when it is referenced by name in
`envTemplate.envSpecificResourceProfiles` in the
[Environment Inventory](/docs/envgene-configs.md#env_definitionyml). An override file that no entry
references is ignored, wherever it sits:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    # Key: `cloud` or the namespace folder name under `Namespaces/` in the Environment Instance.
    # Value: the name of the environment-specific Resource Profile Override file (without extension).
    cloud: <env-specific-override-name>
    <namespace-folder-name>: <env-specific-override-name>
```

Once a name is referenced, EnvGene resolves it to a file by searching the Instance repository in the
following order, from the most specific scope to the least specific. The first match wins, so the same
name resolves to the most specific file available:

1. `/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles` - the environment scope.
2. `/environments/<cluster-name>/resource_profiles` - the cluster scope, one file reusable by every
   environment in the cluster.
3. `/environments/resource_profiles` - the global scope, one file reusable across the repository.

The scope is only where a referenced name is looked up and how widely one file can be reused. A file placed
in a broad scope still applies only where it is referenced by name.

A standalone environment-specific override is allowed. When no `profile.name` is set on the Cloud or
Namespace in the template, EnvGene attaches the override to the object directly.

### Merge and replace

When an environment-specific override is present, it is merged with or replaces the template override.
The mode is controlled by `inventory.config.mergeEnvSpecificResourceProfiles` in the
[Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
inventory:
  config:
    # Optional. Default: true.
    # true  - merge the environment-specific override with the template override.
    # false - replace the template override entirely with the environment-specific override.
    mergeEnvSpecificResourceProfiles: boolean
```

#### Replace mode

When `mergeEnvSpecificResourceProfiles` is `false`, the environment-specific override completely
replaces the template override. The resulting
[Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) takes the name of the
environment-specific override.

Replace mode is how you change the baseline for an environment. Because replace drops the template override,
the custom values bound to the old baseline are not carried onto the new one.

#### Merge mode

When `mergeEnvSpecificResourceProfiles` is `true` (the default), the environment-specific override is
merged into the template override. It adds entries the template does not have and wins on any conflicting
leaf value. When both overrides carry a `baseline` field, the environment-specific value is used. The
resulting [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) takes the name of
the template override.

Merge mode is for adding custom values on the same baseline. Merging when the template override carries
custom values and its baseline differs from the environment-specific override's baseline is the wrong path
for changing a baseline. It is tolerated and emits a warning, and you should use replace mode instead. A
baseline-only template override merged with a different environment-specific baseline is not warned.

### Naming rules for Resource Profile Override

To ensure every [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) has a
unique name across the Instance repository, enable `updateRPOverrideNameWithEnvName` in the
[Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
inventory:
  config:
    # Optional. Default: false.
    # If true, resource profile override names are prefixed with <tenant>-<cloud>-<env>- during
    # CMDB import.
    updateRPOverrideNameWithEnvName: boolean
```

When set to `true`, EnvGene prefixes the name of each
[Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) with
`<tenant-name>-<cloud-name>-<env-name>-` (using the values from
[`current_env.tenant`](/docs/template-macros.md#current_envtenant),
[`current_env.cloud`](/docs/template-macros.md#current_envcloud), and
[`current_env.name`](/docs/template-macros.md#current_envname)) and applies the same prefix to the
`profile.name` attribute of the Cloud or Namespace.

For example: `acme-prod-eu-west-myprofile`.

## Effective Set calculation: resolving the profile

During Effective Set calculation, the Effective Set generator resolves which Resource Profile Override
and baseline to apply for each service the application provides.

### Side selection

The generator resolves the profile from either the Namespace or the Cloud, never both at once. A signal
gate chooses the side. The Namespace is the active side when it carries any profile signal, meaning its
object `profile.baseline` is set or an override is present for it. Otherwise the Cloud is the active side.
The Namespace is the recommended layer for setting a resource profile, and the Cloud is a rarely-needed
fallback.

### Baseline resolution within the active side

Within the active side, the effective baseline name is resolved from three sources, in order of precedence
from highest to lowest:

1. the `baseline` field of the environment-specific override, when set.
2. the `baseline` field of the template override, when set.
3. the `profile.baseline` value on the Cloud or Namespace object.

In replace mode the template override is dropped, so its baseline drops out of the order and the precedence
collapses to the environment-specific override's baseline, then the object baseline.

An empty string in any of these fields is treated as absent. Setting an empty string instead of omitting
the field is valid YAML but is bad practice.

The `baseline` is optional in every source: in each override and on the Cloud or Namespace object. The
profile name on the object is optional too. Setting a baseline is nonetheless the best-practice choice,
because an override's custom values are meant to sit on top of a named baseline. An override that sets
custom values but declares no baseline is tolerated and emits a warning.

The override's parameter list is optional as well. A baseline-only override sets only a name and a baseline,
with no custom values, which changes the baseline for an environment without adjusting any parameter.

The baseline value is a free-form string. Any name the application defines is accepted, not only the
well-known values like `dev` or `prod`. When the resolved name does not match a baseline that a service
ships (and that service does ship baselines), the override still applies and a warning is emitted.

### Applying the override and baseline to each service

The override is always applied. Baseline parameters are layered under the override only when the resolved
baseline name is found among the baselines the application defines.

The override's custom values are always included. When a baseline name is resolved and matched, the baseline
parameters serve as the base layer and the override's custom values take precedence on any matching key. If
the resolved name is not found among a service's baselines but the service does ship baselines, the override
still applies and a warning is emitted. A service that ships no baselines at all receives the override only,
with no warning.

Generation continues in every case. There are no hard failures in resource profile resolution. The
abnormal-but-tolerated cases surface as warnings only.

> [!NOTE]
> A service with no baselines at all is never warned, even when a baseline name is specified in the profile.
> A warning is emitted only when a resolved name does not match the baselines that a service does ship.

### Outcome table

The result for a service depends on two independent inputs plus the service's own baselines:

- **Resolved baseline** - the name from [Baseline resolution](#baseline-resolution-within-the-active-side).
  `Set` means a non-empty name was resolved.
- **Override present** - whether the override carries custom values for the service.
- **Application's baselines** - the baselines the service itself defines.

A baseline and an override are independent. A service can receive a baseline only, an override only, both,
or neither. Generation continues in every row.

| Resolved baseline | Override present | Application's baselines           | Result                                  |
| ----------------- | ---------------- | --------------------------------- | --------------------------------------- |
| Set               | Yes              | Found (name matches)              | Baseline parameters + override          |
| Set               | Yes              | Service has baselines, none match | Override only, with a warning           |
| Set               | Yes              | Service has no baselines          | Override only                           |
| Not set           | Yes              | Any                               | Override only                           |
| Set               | No               | Found (name matches)              | Baseline only                           |
| Set               | No               | Service has baselines, none match | No parameters, with a warning           |
| Set               | No               | Service has no baselines          | No parameters                           |
| Not set           | No               | Any                               | No parameters                           |

### Result in the Effective Set

The resolved parameters are included as
[per-service parameters](/docs/features/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters)
in the deployment context of [Effective Set v2.0](/docs/features/calculator-cli.md#effective-set-v20).

- When a service has no baseline and no override, it receives no performance parameters.
- When only a baseline is resolved, the service receives the baseline parameters.
- When only an override is present, the service receives the override's custom values.
- When both are resolved, the override's custom values take precedence on any matching key.

## Resolving dot notation

When the Effective Set generator applies Resource Profile parameters, it expands parameter keys that
contain dots into nested YAML structures.

The part before the first dot becomes the top-level key. Each subsequent segment becomes a key at the
next nesting level. The parameter value goes into the innermost key.

### Baseline example

Input:

```yaml
resources.requests.cpu: 100m
resources.requests.memory: 128Mi
replicas: 1
```

Expanded:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
replicas: 1
```

### Override example

Input (using the Resource Profile Override `name`/`value` format):

```yaml
- name: "resources.requests.cpu"
  value: "100m"
- name: "resources.requests.memory"
  value: "128Mi"
- name: "replicas"
  value: 1
```

Expanded:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
replicas: 1
```

## Related documentation

- [Configure resource profiles](/docs/how-to/configure-resource-profiles.md) - task scenarios for setting profiles
- [Resource profiles tutorial](/docs/tutorials/resource-profiles.md) - a guided end-to-end lesson
- [Resource profiles use cases](/docs/use-cases/resource-profiles.md) - observable behavior scenarios
- [ADR-0006](/docs/adr/0006-resource-profile-baseline-override-resolution.md) - the resolution design decision
- [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md) - how overrides are combined
- [`generate_effective_set`](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md) - launches the calculator
- [Calculator CLI](/docs/features/calculator-cli.md) - baseline and override resolution

[env-specific-rpo]: /docs/envgene-objects.md#environment-specific-resource-profile-override
[per-service-params]: /docs/features/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters
