# Resource Profiles

- [Resource Profiles](#resource-profiles)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
  - [Энвген Объекты](#энвген-объекты)
  - [Resource Profile Processing During Environment Generation](#resource-profile-processing-during-environment-generation)
    - [Naming Rules for Resource Profile Override](#naming-rules-for-resource-profile-override)
    - [Combination Logic](#combination-logic)
  - [Процессинг профайлов при калькуляции эффектив сета](#процессинг-профайлов-при-калькуляции-эффектив-сета)
    - [Резолвинг дот нотации](#резолвинг-дот-нотации)

## Problem Statement

## Proposed Approach

Performance deployment parameters like `CPU_LIMIT` and `MEMORY_REQUEST` are grouped separately into Resource Profiles. This makes it manage separately these parameters apart from all other deployment values.

The Resource Profiles system has a 3-level hierarchy:

1. Resource Profile Baselines

    These are sets of pre-configured performance parameters for services, used to deploy a service in a standard way.  
    Service developers create these baselines and distribute them together with the app (which includes the services), as part of the Application SBOM.

    Typical baseline profiles are:

    - `dev`: The minimum amount of resources required for the service to run under low load.
    - `prod`: The recommended amount for production workloads, so that you only need to scale the number of replicas.

    You can have any number of profiles and call them whatever you want, e.g. `small`, `medium`, `large`.

2. [Template Resource Profile Override](/docs/envgene-objects.md#templates-resource-profile-override)

    These are sets of customizations for performance parameters, over a baseline Resource Profile.  
    Template overrides are created in the template envgene repository, allowing the configurator to adjust performance parameters for all environments of the same type.

3. [Environment-specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)

    These are customizations of performance parameters for a baseline Resource Profile, specific to one or several environments.  
    Such overrides are created by the configurator in the instance envgene repository, to further adjust performance parameters on top of the baseline and template override.

When generating an [Environment Instance](/docs/envgene-objects.md#environment-instance-objects), the template and instance resource profile overrides are either merged or replaced, resulting in the [environment instance resource profile override object](/docs/envgene-objects.md#resource-profile-override). The instance-level override has higher priority.

When calculating the [effective set](/docs/calculator-cli.md#effective-set-v20), parameters from the baseline and the [environment instance resource profile override](/docs/envgene-objects.md#resource-profile-override) are also merged and used as [per-service deployment context parameters](/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters). Here again, the environment instance resource profile override has priority.

## Энвген Объекты

1. [Темплейтный Ресурс профайл оверрайд](/docs/envgene-objects.md#templates-resource-profile-override)
2. [Энв специфик Ресурс профайл оверрайд](/docs/envgene-objects.md#environment-specific-resource-profile-override)
3. [ресурс профайл оверрайд энв инстанса](/docs/envgene-objects.md#resource-profile-override)
4. [эффектив сета](/docs/calculator-cli.md#effective-set-v20)

## Resource Profile Processing During Environment Generation

During Environment generation, as part of the [`env_build`](/docs/envgene-pipelines.md#instance-pipeline) job, two types of Resource Profile Overrides are processed and combined:

1. [Template Resource Profile Override](/docs/envgene-objects.md#templates-resource-profile-override)

    This is defined separately for each Namespace or Cloud.  
    It is a file in the `templates/resource_profiles` directory inside the EnvironmentTemplate artifact.  
    The filename matches the value of the `profile.name` attribute for that Cloud or Namespace.

2. [Environment-Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override)

    This is also defined separately for each Namespace or Cloud.  
    The name is determined by the `envTemplate.envSpecificResourceProfiles` parameter in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

    ```yaml
    envTemplate:
      envSpecificResourceProfiles: hashmap
        # Key: 'cloud' or namespace template name
        # Value: name of env-specific resource profile override file (without extension)
        cloud: <env-specific-override-name>
        <namespace-template-name>: <env-specific-override-name>
    ```

    The file is searched in the following locations in the Instance Repository, in order of priority:

    1. `/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles`
    2. `/environments/<cluster-name>/resource_profiles`
    3. `/environments/resource_profiles`

The final result of processing is a [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) object.

### Naming Rules for Resource Profile Override

The name of the resulting [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override) is determined as follows:

- If there are both template and environment-specific Resource Profile Overrides for a Cloud or Namespace, the name of environment-specific one is used.
- If only the template override is defined, it name is used.
- If only the environment-specific override is defined, it name is used.

These rules apply to both the override filename and the `profile.name` field in the Cloud or Namespace.

Additionally, the naming of the Resource Profile Override in the Environment can be updated if the `updateRPOverrideNameWithEnvName.inventory.config` option is enabled in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):section:

```yaml
inventory:
  config:
    # Optional. Default value: false
    # If true, during CMDB import the resource profile override names will be updated by this pattern:
    # <tenant-name>-<cloud-name>-<env-name>-<RPO-name>
    updateRPOverrideNameWithEnvName: boolean
```

The naming principle does not depend on the [Combination Logic](#combination-logic) mode.

### Combination Logic

The combination operation is performed when Environment-Specific Resource Profile Overrides are defined for a particular Cloud/Namespace object.  
Environment-Specific Resource Profile Overrides are specified using `envTemplate.envSpecificResourceProfiles` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
envTemplate:
  # Environment-specific resource profile overrides
  envSpecificResourceProfiles: hashmap
    # Key: cloud name or namespace identifier
    # Value: name of the env-specific resource profile override file (without extension)
```

There are two combination modes: merge and replace. The combination mode is controlled by `inventory.config.mergeEnvSpecificResourceProfiles` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
inventory:
  config:
    # Optional. Default value: false
    # If true, environment-specific Resource Profile Overrides defined in envTemplate.envSpecificResourceProfiles
    # are merged with Resource Profile Overrides from the Environment Template
    # If false, they completely replace the Environment Template's Resource Profile Overrides
    mergeEnvSpecificResourceProfiles: boolean
```

In replace mode, environment-specific Resource Profile Overrides fully replace Template's Resource Profile Overrides.

Algorithm for merging an environment-specific resource profile override (`target`) into a template resource profile override (`source`):

1. For each `application` in source, look for an application with the same `name` in target.
2. If no such application exists in target — copy the whole object from source.
3. If found—merge services:
   1. For each `service` in the source application, look for a service with the same `name` in the target.
   2. If no such service — copy the whole service from source.
   3. If the service is found — merge parameters:
      1. For each `parameter` in the source service, look for a parameter with the same `name` in the target service.
      2. If the parameter is not present—add it entirely.
      3. If the parameter is present—overwrite the `value` in the target with the value from the source.

## Процессинг профайлов при калькуляции эффектив сета

?mime-type=application/vnd.qubership.resource-profile-baseline

При калькуляции эффектив сета, в процессе выолнения `generate_effective_set` джобы, параметры из [ресурс профайл оверрайд энв инстанса](/docs/envgene-objects.md#resource-profile-override) мержаться в ресурс профайл бейслайн, расположенного в Application SBOM.

1. для каждого приложения из солюшен дескриптора:
   1. выбирается ресурс профайл бейслайн:
      1. тот что задан на клауде или неймспейсе, или задан на обоих выбирается неймспейс
   2. находится аппликейшен сбом
      1. в этом сбом для каждого сервиса из [сервисного листа](/docs/calculator-cli.md#version-20-service-inclusion-criteria-and-naming-convention)
         1. ищется дочерний `application/vnd.qubership.resource-profile-baselinе` (если такого нет, шаг пропускается)
         2. выбирается в нем бейслайн из П1.1.1
         3. параметры из него подвергаются [раскрытию](#резолвинг-дот-нотации)
         4. копируются в персервисные параметры деплоймент контекста эффектив сета
   3. выбирается ресурс профайл оверрайд
      1. тот что задан на клауде или неймспейсе, или задан на обоих выбирается неймспейс
   4. 

Ресультат мержа добавляется в [персервисными параметрами деплоймент контекста](/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-parameters) [эффектив сета версии 2](/docs/calculator-cli.md#effective-set-v20)

Эффектив сет версии 1 генерируется без учета ресурс профайл бейслайн.

### Резолвинг дот нотации

Калькулятор кли, при генерации эффектив сета разворачивает дот бейс параметры в YAML структуру для:

1. ресурс профайл бейслайн

    При чтении параметров ресурс профайл бейслайн, если в ключе параметра содержится точка (например, `resources.requests.cpu`), этот параметр интерпретируется как вложенное свойство yaml-объекта:

    - Строка до первой точки становится ключом первого уровня.
    - Строка между точками — ключи следующих уровней, рекурсивно.
    - Значение параметра помещается в самый вложенный ключ.

    **Пример:**

    Исходные параметры:

    ```yaml
    resources.requests.cpu: 100m
    resources.requests.memory: 128Mi
    replicas: 1
    ```

    Преобразуются в:

    ```yaml
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
    replicas: 1
    ```

2. [ресурс профайл оверрайд энв инстанса](/docs/envgene-objects.md#resource-profile-override)

    При чтении параметров [ресурс профайл оверрайд энв инстанса](/docs/envgene-objects.md#resource-profile-override), если в ключе параметра (`name`) содержится точка (например, `resources.requests.cpu`), этот параметр интерпретируется как вложенное свойство yaml-объекта:

    - Строка до первой точки становится ключом первого уровня.
    - Строка между точками — ключи следующих уровней, рекурсивно.
    - Значение параметра (`value`) помещается в самый вложенный ключ.

    **Пример:**

    Исходные параметры:

    ```yaml
    ...
    - name: "resources.requests.cpu"
      value: "100m"
    - name: "resources.requests.memory"
      value: "128Mi"
    - name: "replicas"
      value: 1
    ```

    Преобразуются в:

    ```yaml
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
    replicas: 1
    ```
