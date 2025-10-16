# Resource Profiles

- [Resource Profiles](#resource-profiles)
  - [Proposed Approach](#proposed-approach)
  - [Resource Profile Processing During Environment Generation](#resource-profile-processing-during-environment-generation)
    - [Combination Logic](#combination-logic)
    - [Naming Rules for Resource Profile Override](#naming-rules-for-resource-profile-override)
  - [Resource Profile Processing During Effective Set Calculation](#resource-profile-processing-during-effective-set-calculation)
    - [Merging Logic](#merging-logic)
    - [Resolving Dot Notation](#resolving-dot-notation)

## Proposed Approach

Performance deployment parameters like `CPU_LIMIT` and `MEMORY_REQUEST` are grouped separately into Resource Profiles. This makes it manage separately these parameters apart from all other deployment parameters.

The Resource Profiles system has a 3-level hierarchy:

1. Resource Profile Baselines

    These are sets of pre-configured performance parameters for services, intended to provide a standardized performance configuration for a service.  
    Service developers create these baselines and distribute them together with the application artifact. Later, they are included in the Application SBOM.

    Typical baseline profiles are:

    - `dev`: The minimum amount of resources required for the service to run under low load.
    - `prod`: The recommended amount for production workloads, so that you only need to scale the number of replicas.

    You can have any number of profiles and call them whatever you want, e.g. `small`, `medium`, `large`.

2. [Template Resource Profile Override](/docs/envgene-objects.md#templates-resource-profile-override)

    These are customizations for performance parameters, over a Baseline Resource Profile.
    Such overrides are created by the configurator in the Template repository, to further adjust performance parameters on top of the Baseline Resource Profile Override for all environments of the same type.

3. [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)

    These are customizations for performance parameters, over a Baseline Resource Profile and Template Resource Profile Override.
    Such overrides are created by the configurator in the Instance repository, to further adjust performance parameters on top of the Baseline Resource Profile and Template Resource Profile Override.

When generating an [Environment Instance](/docs/envgene-objects.md#environment-instance-objects), the Template and Environment-specific Resource Profile Overrides are either merged or replaced, resulting in the [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override). The Environment-specific Resource Profile Override has higher priority.

When calculating the [Effective Set](/docs/calculator-cli.md#effective-set-v20), parameters from the Resource Profile Baselines and the [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) are also merged and used as [per-service deployment context parameters](/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters). The Resource Profile Override has higher priority.

## Resource Profile Processing During Environment Generation

During Environment generation, as part of the [`env_build`](/docs/envgene-pipelines.md#instance-pipeline) job, two types of Resource Profile Overrides are processed and combined:

1. [Template Resource Profile Override](/docs/envgene-objects.md#templates-resource-profile-override)

    The Template Resource Profile Override is configured individually for each Namespace or Cloud, identified by the `profile.name` property.  
    Each override is represented as a YAML file located at `/templates/resource_profiles` within the Environment Template repository.  
    The filename (without the `.yaml` or `.yml` extension) must exactly correspond to the value set in `profile.name` for that specific Cloud or Namespace.

    For example, if a namespace specifies `profile.name: dev-over`, it will use `/templates/resource_profiles/dev-over.yaml` as its template resource profile override.

2. [Environment-Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)

    The Environment-Specific Resource Profile Override is specified individually for each Namespace or Cloud via `envTemplate.envSpecificResourceProfiles` parameter of the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

    ```yaml
    envTemplate:
      envSpecificResourceProfiles:
        # Key: cloud' or the namespace template name as defined in the environment template
        # Value: The name of the Environment Specific Resource Profile Override file (exclude file extension)
        cloud: <env-specific-override-name>
        <namespace-template-name>: <env-specific-override-name>
    ```

    When an Environment Specific Resource Profile Override is referenced, EnvGene searches for the corresponding YAML file in the Instance repository using the following location priority (from highest to lowest):

    1. `/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles` — Environment-specific, highest priority  
    2. `/environments/<cluster-name>/resource_profiles` — Cluster-wide, applies to all environments in the cluster  
    3. `/environments/resource_profiles` — Global, common for the entire repository  

    The first match found is used as the environment-specific override for the given Cloud or Namespace.

The final result of processing is a [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override)

### Combination Logic

Resource Profile combination happens when you define Environment-Specific Resource Profile Overrides for a particular Cloud or Namespace.  
These overrides are referenced via `envTemplate.envSpecificResourceProfiles` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
envTemplate:
  envSpecificResourceProfiles:
    # Key: cloud' or the namespace template name as defined in the environment template
    # Value: The name of the Environment Specific Resource Profile Override file (exclude file extension)
    cloud: <env-specific-override-name>
    <namespace-template-name>: <env-specific-override-name>
```

There are two ways to combine overrides: **merge** and **replace**.  
Which mode is used is controlled by the `inventory.config.mergeEnvSpecificResourceProfiles` setting in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
inventory:
  config:
    # Optional. Default value - `true`
    # If `true`, environment-specific Resource Profile Overrides defined in envTemplate.envSpecificParamsets
    # are merged with Resource Profile Overrides from the Environment Template
    # If `false`, they completely replace the Environment Template's Resource Profile Overrides
    mergeEnvSpecificResourceProfiles: boolean
```

**Replace mode:**

The Environment-Specific Resource Profile Override completely replaces the corresponding Template Resource Profile Override.

In this mode, the resulting [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) will have the same name as the [Environment-Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override).

**Merge mode:**

The Environment-Specific Resource Profile Override is merged **into** the Template Override according to this algorithm:

1. For each `application` in the template override (`source`), search for an application with the same `name` in the environment-specific override (`target`).
2. If the target does not have this application, copy the entire application object from the template override.
3. If the application exists in both:
    - For each `service` in the template's application, look for a service with the same `name` in the target.
    - If the target does not have the service, copy the service from the template.
    - If the service exists in both:
        - For each `parameter` in the template's service, check for a parameter with the same `name` in the target.
        - If the parameter is missing in the target, add the entire parameter from the template.
        - If the parameter exists in both, update the parameter in the target by overwriting its `value` with the one from the template.

In this mode, the resulting [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) will have the same name as the [Template Resource Profile Override](/docs/envgene-objects.md#templates-resource-profile-override).

### Naming Rules for Resource Profile Override

To avoid name collisions and ensure that every [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) has a unique name across Instance repository, you can enable a setting in your [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) file called `updateRPOverrideNameWithEnvName`:

```yaml
inventory:
  config:
    # Optional
    # Default: false
    # If true, resource profile override names are automatically updated during CMDB import using the following pattern:
    # <tenant-name>-<cloud-name>-<env-name>-<RPO-name>
    updateRPOverrideNameWithEnvName: boolean
```

If you set `updateRPOverrideNameWithEnvName: true`, the system will:
  
1. Add a prefix to the name of each [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override). The prefix will be constructed from the [`<tenant-name>`](/docs/template-macros.md#current_envtenant), [`<cloud-name>`](/docs/template-macros.md#current_envcloud), and [`<environment-name>`](/docs/template-macros.md#current_envname), joined by hyphens, followed by the original Resource Profile Override name.
2. Add the same prefix to the `profile.name` attribute of the Cloud or Namespace

For example: `acme-prod-eu-west-myprofile`.

## Resource Profile Processing During Effective Set Calculation

During the calculation of the Effective Set, as performed by the `generate_effective_set` job, parameters from the [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) are merged into the Resource Profile Baseline found in the Application SBOM:

1. Resource Profile Baseline

    Optionally contained in the Application SBOM for a service (with mime-type: `application/vnd.qubership.resource-profile-baseline`). Each SBOM may define multiple baselines, each identified by a unique baseline name. These baselines are included in the SBOM from the application's artifact.

2. [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override)

    This object is result of [Resource Profile Processing During Environment Generation](#resource-profile-processing-during-environment-generation) phase, representing a combination of the Template Resource Profile Override and the Environment-Specific Resource Profile Override

### Merging Logic

1. Reading Resource Profile Baseline
   1. For each service in the Application SBOM, its Resource Profile Baseline (if present) is retrieved
   2. The required baseline is selected by its name, as defined at either the Cloud or Namespace level for the application (if there’s a conflict, the Namespace value takes precedence)
   3. The baseline parameters are [resolved](#resolving-dot-notation) from dot notation into a YAML structure.

2. Applying the Resource Profile Override
   1. For the corresponding application/service, parameters from the Resource Profile Override are retrieved.
   2. The Resource Profile Override parameters are [resolved](#resolving-dot-notation) from dot notation into a YAML structure.
   3. The values from the Override are applied on top of the Baseline: matching keys are overwritten.

   > [!NOTE]
   > Values from the Resource Profile Override take precedence over matching keys in the Resource Profile Baseline.

3. Writing Result to the Effective Set
   1. The result (Resource Profile Baseline + Resource Profile Override) is included as [per-service parameters](/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters) in the deployment context of [Effective Set v2.0](/docs/calculator-cli.md#effective-set-v20).

- If a service does not have a Baseline, only the parameters from the Override are used.
- If the Override is empty, only the Baseline is used.
- If both are missing, the service does not receive any performance-specific parameters.

> [!NOTE]
> Effective Set v1.0 is generated without considering the Resource Profile Baseline.

### Resolving Dot Notation

When generating the Effective Set, the Calculator CLI resolves parameters written in dot notation into YAML structures for two sources:

1. Resource Profile Baseline

    When reading Resource Profile Baseline parameters, if a parameter key contains a dot (for example, `resources.requests.cpu`), it is interpreted as a nested YAML property:

    - The part before the first dot becomes the top-level key.
    - Parts between the dots are keys for deeper nested levels.
    - The parameter value goes into the innermost key.

    **Example:**

    Original parameters:

    ```yaml
    resources.requests.cpu: 100m
    resources.requests.memory: 128Mi
    replicas: 1
    ```

    Are transformed into:

    ```yaml
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
    replicas: 1
    ```

2. [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override)

    When reading parameters from [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override), if the parameter name contains a dot (for example, `resources.requests.cpu`), it is also expanded into a nested YAML property:

    - The part before the first dot becomes the top-level key.
    - Parts between dots become nested keys.
    - The parameter value (`value`) goes into the deepest key.

    **Example:**

    Original parameters:

    ```yaml
    ...
    - name: "resources.requests.cpu"
      value: "100m"
    - name: "resources.requests.memory"
      value: "128Mi"
    - name: "replicas"
      value: 1
    ```

    Are transformed into:

    ```yaml
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
    replicas: 1
    ```
