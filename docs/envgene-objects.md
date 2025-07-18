# EnvGene Objects

- [EnvGene Objects](#envgene-objects)
  - [Template Repository Objects](#template-repository-objects)
    - [Environment Template Objects](#environment-template-objects)
      - [Template Descriptor](#template-descriptor)
      - [Tenant Template](#tenant-template)
      - [Cloud Template](#cloud-template)
      - [Namespace Template](#namespace-template)
      - [ParameterSet](#parameterset)
      - [Resource Profile Override (in Template)](#resource-profile-override-in-template)
      - [Composite Structure Template](#composite-structure-template)
    - [System Credentials File (in Template repository)](#system-credentials-file-in-template-repository)
  - [Instance Repository Objects](#instance-repository-objects)
    - [Environment Instance Objects](#environment-instance-objects)
      - [Tenant](#tenant)
      - [Cloud](#cloud)
      - [Namespace](#namespace)
      - [Application](#application)
      - [Resource Profile Override (in Instance)](#resource-profile-override-in-instance)
      - [Composite Structure](#composite-structure)
      - [Environment Credentials File](#environment-credentials-file)
      - [Solution Descriptor](#solution-descriptor)
    - [Credential](#credential)
      - [`usernamePassword`](#usernamepassword)
      - [`secret`](#secret)
    - [Shared Credentials File](#shared-credentials-file)
    - [System Credentials File (in Instance repository)](#system-credentials-file-in-instance-repository)
    - [Cloud Passport](#cloud-passport)
      - [Main File](#main-file)
      - [Credential File](#credential-file)

## Template Repository Objects

### Environment Template Objects

An Environment Template is a file structure within the Envgene Template Repository that describes the structure of a solution — such as which namespaces are part of the solution, as well as environment-agnostic parameters, which are common to a specific type of solution.

The objects that make up the Environment Template extensively use the Jinja template engine. During the generation of an Environment Instance, Envgene renders these templates with environment-specific parameters, allowing a single template to be used for preparing configurations for similar but not entirely identical environment/solution instances.

The template repository can contain multiple Environment Templates describing configurations for different types of environments/solution instances, such as DEV, PROD, and SVT.

When a commit is made to the Template Repository, an artifact is built and published. This artifact contains all the Environment Templates located in the repository.

#### Template Descriptor

This object is a describes the structure of a solution, links to solution's components. It has the following structure:

```yaml
# Optional
# Template Inheritance configuration
# See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
parent-templates:
  <parent-template-name>: "<app:ver-of-parent-template>"
# Mandatory
# Can be specified either as direct template path (string) or as an object
tenant: "<path-to-the-tenant-template-file>"
# or
tenant:
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  parent: "<parent-template-name>"
# Mandatory
# Can be specified either as direct template path (string) or as an object
cloud: "<path-to-the-cloud-template-file>"
# or
cloud:
  # Optional
  template_path: "<path-to-the-cloud-template-file>"
  # Optional
  # Template Override configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
  template_override:     
    "<yaml or jinja expression>"
  # Optional
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  parent: "<parent-template-name>"
  # Optional
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  overrides-parent:
    profile:
      override-profile-name: "<resource-profile-override-name>"
      parent-profile-name: "<resource-profile-override-name>"
      baseline-profile-name: "<resource-profile-baseline-name>"
      merge-with-parent: <boolean>
    deployParameters: <hashmap-with-parameters>
    e2eParameters: <hashmap-with-parameters>
    technicalConfigurationParameters: <hashmap-with-parameters>
    deployParameterSets: <list-with-parameter-sets>
    e2eParameterSets: <list-with-parameter-sets>
    technicalConfigurationParameterSets: <list-with-parameter-sets>
composite_structure: "<path-to-the-composite-structure-template-file>"
namespaces:
  - # Optional
    template_path: "<path-to-the-namespace-template-file>"
    # Optional
    # See details https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
    template_override:
      "<yaml or jinja expression>"
    # Optional
    # Template Inheritance configuration
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    name: <namespace-name-in-parent-template>
    # Optional
    # Template Inheritance configuration
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    parent: "<parent-template-name>"
    # Optional
    # Template Inheritance configuration
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    overrides-parent:
      profile:
        override-profile-name: "<resource-profile-override-name>"
        parent-profile-name: "<resource-profile-override-name>"
        baseline-profile-name: "<resource-profile-baseline-name>"
        merge-with-parent: true
      deployParameters: <hashmap-with-parameters>
      e2eParameters: <hashmap-with-parameters>
      technicalConfigurationParameters: <hashmap-with-parameters>
      deployParameterSets: <list-with-parameter-sets>
      e2eParameterSets: <list-with-parameter-sets>
      technicalConfigurationParameterSets: <list-with-parameter-sets>
      template_path: "<path-to-the-namespace-template-file>"
```

[Template Descriptor JSON schema](/schemas/template-descriptor.schema.json)

Any YAML file located in the `/templates/env_templates/` folder is considered a Template Descriptor.

The name of this file serves as the name of the Environment Template. In the Environment Inventory, this name is used to specify which Environment Template from the artifact should be used.

#### Tenant Template

This is a Jinja template file used to render the [Tenant](#tenant) object. The Tenant Template is used to define tenant-level properties and parameters that are common across all namespaces in an environment.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the tenant. Usually set to `{{current_env.tenant}}`. | Used as an identifier in logs, UI, and for reference in templates. |
| **registryName** | string | No | The name of the registry to use. Usually set to "default". | Used to determine which registry to use for container images. |
| **description** | string | No | A description of the tenant. Usually set to `{{current_env.description}}`. | Used for documentation and display purposes in UI. |
| **owners** | string | No | The owners of the tenant. Usually set to `{{current_env.owners}}`. | Used for documentation and notification purposes. |
| **gitRepository** | string | No | The Git repository URL for the tenant configuration. | Used to track the source of tenant configuration. |
| **defaultBranch** | string | No | The default Git branch for the tenant configuration. | Used to determine which branch to use when fetching tenant configuration. |
| **credential** | string | No | The credential ID for accessing the Git repository. | Used to authenticate with the Git repository. |
| **labels** | array of strings | No | Labels for the tenant. | Used for filtering and organization in UI and APIs. |

##### globalE2EParameters

Global end-to-end testing parameters for the tenant.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **pipelineDefaultRecipients** | string | No | Default recipients for pipeline notifications. | Used to determine who receives pipeline notifications by default. |
| **recipientsStrategy** | string | No | Strategy for merging recipients. Usually "merge". | Controls how recipients are merged when multiple sources define recipients. |
| **mergeTenantsAndE2EParameters** | boolean | No | Whether to merge tenant parameters and E2E parameters. Usually false. | Controls parameter merging behavior during effective set generation. |
| **environmentParameters** | object | No | Environment-specific parameters for E2E testing. | Used to configure environment-specific aspects of E2E testing. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the tenant level. | Used during deployment to configure applications across all namespaces. |

##### Usage in Flow

The Tenant Template is used in several key processes:

1. **Environment Instance Creation**: The Tenant Template is rendered using Jinja2 with environment variables to create the Tenant object.

2. **Parameter Inheritance**: The parameters defined in the Tenant Template are inherited by all namespaces in the environment.

3. **Pipeline Configuration**: The globalE2EParameters defined in the Tenant Template are used to configure pipeline notifications and testing parameters.

#### Cloud Template

This is a Jinja template file used to render the [Cloud](#cloud) object. It defines cloud-level parameters for environment generation. The Cloud Template is used to define cloud-level properties and parameters that are common across all namespaces in an environment.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the cloud configuration. Usually set to `{{current_env.cloudNameWithCluster}}`. | Used as an identifier in logs, UI, and for reference in templates. |
| **apiUrl** | string | Yes | The URL of the Kubernetes API server. Usually set to `{{current_env.cluster.cloud_api_url}}`. | Used to connect to the Kubernetes cluster for deployments and operations. |
| **apiPort** | string | Yes | The port of the Kubernetes API server. Usually set to `{{current_env.cluster.cloud_api_port}}`. | Used along with apiUrl to form the complete connection string to the Kubernetes API. |
| **privateUrl** | string | No | The private URL of the cloud. Usually empty. | Rarely used in templates. Potential candidate for deprecation. |
| **publicUrl** | string | Yes | The public URL of the cloud. Usually set to `{{current_env.cluster.cloud_public_url}}`. | Used to generate URLs for various services and in templates. |
| **dashboardUrl** | string | No | The URL of the Kubernetes dashboard. Usually set to `https://dashboard.{{current_env.cluster.cloud_public_url}}`. | Used in UI links and stored in deployParameters as CLOUD_DASHBOARD_URL. |
| **labels** | array of strings | No | Labels for the cloud. Usually empty. | Rarely used for filtering or organization. Potential candidate for deprecation. |
| **defaultCredentialsId** | string | Yes | The default credentials ID for accessing the cloud. Usually "token". | Used to authenticate with the Kubernetes API. |
| **protocol** | string | Yes | The protocol used to connect to the Kubernetes API. Usually set to `{{current_env.cluster.cloud_api_protocol}}`. | Used along with apiUrl and apiPort to form the complete connection string. |
| **mergeDeployParametersAndE2EParameters** | boolean | No | Whether to merge deployParameters and e2eParameters. Usually false. | Controls parameter merging behavior during effective set generation. Potential candidate for deprecation. |
| **dbMode** | string | No | The database mode. Usually "db". | Rarely used for configuration variations. Potential candidate for deprecation. |
| **databases** | array | No | List of databases. Usually empty. | Rarely used and might be redundant with dbaasConfigs. Potential candidate for deprecation. |

##### maasConfig

Configuration for the Monitoring as a Service (MaaS) component.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing MaaS. Usually "maas". | Used to authenticate with the MaaS service. |
| **maasUrl** | string | Yes (if enable is true) | The URL of the MaaS service. Usually set to `http://maas.{{current_env.cluster.cloud_public_url}}`. | Used to connect to the MaaS service for monitoring operations. |
| **maasInternalAddress** | string | Yes (if enable is true) | The internal address of the MaaS service. Usually "http://maas.maas:8888". | Used for internal service-to-service communication with MaaS. |
| **enable** | boolean | Yes | Whether MaaS is enabled. Usually true. | Controls whether MaaS configuration is applied during environment building. |

##### vaultConfig

Configuration for the Vault service for secrets management.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **url** | string | Yes (if enable is true) | The URL of the Vault service. Usually empty. | Used to connect to the Vault service for secrets operations. |
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing Vault. Usually empty. | Used to authenticate with the Vault service. |
| **enable** | boolean | Yes | Whether Vault is enabled. Usually false. | Controls whether Vault configuration is applied during environment building. |

##### dbaasConfigs

Configuration for the Database as a Service (DBaaS) component. This is an array of DBaaS configurations.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing DBaaS. Usually "dbaas". | Used to authenticate with the DBaaS service. |
| **apiUrl** | string | Yes (if enable is true) | The API URL of the DBaaS service. Usually "http://dbaas.dbaas:8888". | Used to connect to the DBaaS service for database operations. |
| **aggregatorUrl** | string | Yes (if enable is true) | The aggregator URL of the DBaaS service. Usually set to `https://dbaas.{{current_env.cluster.cloud_public_url}}`. | Used for aggregated database operations. |
| **enable** | boolean | Yes | Whether DBaaS is enabled. Usually true. | Controls whether DBaaS configuration is applied during environment building. |

##### consulConfig

Configuration for the Consul service for service discovery and configuration.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **tokenSecret** | string | Yes (if enabled is true) | The token secret for Consul. Usually "consul-token". | Used to authenticate with the Consul service. |
| **publicUrl** | string | Yes (if enabled is true) | The public URL of the Consul service. Usually set to `https://consul.{{current_env.cluster.cloud_public_url}}`. | Used to connect to the Consul service from outside the cluster. |
| **enabled** | boolean | Yes | Whether Consul is enabled. Usually true. | Controls whether Consul configuration is applied during environment building. |
| **internalUrl** | string | Yes (if enabled is true) | The internal URL of the Consul service. Usually "http://consul.consul:8888". | Used for internal service-to-service communication with Consul. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the cloud level. | Used during deployment to configure applications. |
| **e2eParameters** | object | No | Key-value pairs of end-to-end testing parameters at the cloud level. | Used during testing to configure test environments. |
| **technicalConfigurationParameters** | object | No | Key-value pairs of technical configuration parameters at the cloud level. | Used for technical configurations that are not directly related to deployment or testing. |
| **deployParameterSets** | array of strings | No | List of deployment parameter set names to include at the cloud level. | Used to include predefined sets of deployment parameters. |
| **e2eParameterSets** | array of strings | No | List of end-to-end testing parameter set names to include at the cloud level. | Used to include predefined sets of testing parameters. |
| **technicalConfigurationParameterSets** | array of strings | No | List of technical configuration parameter set names to include at the cloud level. | Used to include predefined sets of technical configuration parameters. |

##### Usage in Flow

The Cloud Template is used in several key processes:

1. **Environment Instance Creation**: The Cloud Template is rendered using Jinja2 with environment variables to create the Cloud object.

2. **Service Configuration**: The Cloud Template defines configurations for various services like MaaS, Vault, DBaaS, and Consul that are used during environment building.

3. **Parameter Inheritance**: The parameters defined in the Cloud Template are inherited by all namespaces in the environment.

#### Namespace Template

This is a Jinja template file used to render the [Namespace](#namespace) object. It defines namespace-level parameters for environment generation. The Namespace Template is used to define namespace-level properties and parameters that are specific to a namespace in an environment.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the namespace. Usually set to `{{current_env.name}}-namespace`. | Used as the Kubernetes namespace name and as an identifier in logs, UI, and templates. |
| **tenantName** | string | No | The name of the tenant this namespace belongs to. Usually set to `{{current_env.env_template}}`. | Used to associate the namespace with its tenant for parameter inheritance and organization. |
| **credentialsId** | string | No | The credentials ID for accessing the namespace. Usually empty. | Used for authentication when performing operations in this namespace. |
| **labels** | array of strings | No | Labels for the namespace. Usually includes solution instance and solution labels. | Used for filtering, organization, and grouping in UI and APIs. |
| **isServerSideMerge** | boolean | Yes | Whether to perform parameter merging on the server side. Usually false. | Controls where parameter merging happens during deployment. |
| **cleanInstallApprovalRequired** | boolean | Yes | Whether clean installations require approval. Usually false. | Controls the approval workflow for clean installations in this namespace. |
| **mergeDeployParametersAndE2EParameters** | boolean | Yes | Whether to merge deployParameters and e2eParameters. Usually false. | Controls parameter merging behavior during effective set generation. |

##### profile

Resource profile configuration for the namespace.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | No | The name of the resource profile override to use. Usually "dev_namespace" or similar. | Used to determine which resource profile override to apply to applications in this namespace. |
| **baseline** | string | No | The baseline profile to use. Usually "dev". | Used as the base resource profile before applying overrides. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the namespace level. Usually includes NAMESPACE_NAME. | Used during deployment to configure applications in this namespace. |
| **e2eParameters** | object | No | Key-value pairs of end-to-end testing parameters at the namespace level. Usually empty. | Used during testing to configure test environments for this namespace. |
| **technicalConfigurationParameters** | object | No | Key-value pairs of technical configuration parameters at the namespace level. Usually empty. | Used for technical configurations specific to this namespace. |
| **deployParameterSets** | array of strings | No | List of deployment parameter set names to include at the namespace level. Usually empty. | Used to include predefined sets of deployment parameters for this namespace. |
| **e2eParameterSets** | array of strings | No | List of end-to-end testing parameter set names to include at the namespace level. Usually empty. | Used to include predefined sets of testing parameters for this namespace. |
| **technicalConfigurationParameterSets** | array of strings | No | List of technical configuration parameter set names to include at the namespace level. Usually empty. | Used to include predefined sets of technical configuration parameters for this namespace. |

##### Usage in Flow

The Namespace Template is used in several key processes:

1. **Environment Instance Creation**: The Namespace Template is rendered using Jinja2 with environment variables to create the Namespace object.

2. **Kubernetes Namespace Creation**: The Namespace object is used to create and configure the Kubernetes namespace during environment building.

3. **Application Deployment**: The Namespace object is used to determine where applications should be deployed and how they should be configured.

#### ParameterSet

A ParameterSet is a YAML file that defines a set of parameters that can be reused across multiple templates. ParameterSets are located in the `/templates/parameters/` folder.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the parameter set. | Used to reference the parameter set in templates. |
| **parameters** | object | Yes | Key-value pairs of parameters. | The actual parameters that will be included when this parameter set is referenced. |

##### Usage in Flow

ParameterSets are used in several key processes:

1. **Template Reference**: ParameterSets are referenced in the `deployParameterSets`, `e2eParameterSets`, and `technicalConfigurationParameterSets` arrays in the Tenant, Cloud, and Namespace templates.

2. **Parameter Reuse**: ParameterSets allow for the reuse of common parameters across multiple templates, reducing duplication and making parameter management easier.

3. **Effective Set Generation**: During effective set generation, parameters from referenced parameter sets are merged into the effective parameter set according to the merging rules.

#### Resource Profile Override (in Template)

A Resource Profile Override is a YAML file that defines resource allocation overrides for applications in a namespace. Resource Profile Overrides are located in the `/templates/resource_profiles/` folder.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the resource profile override. | Used to reference the resource profile override in namespace templates. |
| **baseline** | string | Yes | The baseline profile to use. Usually one of "dev", "dev-ha", "prod", or "prod-nonha". | Used as the base resource profile before applying overrides. |
| **description** | string | No | A description of the resource profile override. | Used for documentation purposes. |
| **applications** | array | Yes | List of applications with their service overrides. | The actual resource overrides for applications and their services. |
| **version** | number | No | The version of the resource profile override. | Used for versioning and tracking changes. |

##### applications

Each item in the applications array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the application. | Used to identify which application the overrides apply to. |
| **version** | string | No | The version of the application. | Used to specify which version of the application the overrides apply to. |
| **sd** | string | No | The solution descriptor for the application. | Used to link the application to its solution descriptor. |
| **services** | array | Yes | List of services with their parameter overrides. | The actual resource overrides for services within the application. |

##### services

Each item in the services array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the service. | Used to identify which service the overrides apply to. |
| **parameters** | array | Yes | List of parameter overrides for the service. | The actual resource parameter overrides for the service. |

##### parameters

Each item in the parameters array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the parameter to override. | Used to identify which parameter to override. |
| **value** | string | Yes | The value to set for the parameter. | The actual override value for the parameter. |

##### Usage in Flow

Resource Profile Overrides are used in several key processes:

1. **Namespace Configuration**: Resource Profile Overrides are referenced in the `profile` property of the Namespace template.

2. **Resource Allocation**: During deployment, the resource profile overrides are applied to control CPU, memory, and other resource allocations for applications and services.

3. **Environment Optimization**: Resource Profile Overrides allow for fine-grained control over resource allocation, making it possible to optimize resource usage based on environment requirements.

#### Composite Structure Template

This is a Jinja template file used to render the [Composite Structure](#composite-structure) object.

Example:

```yaml
name: "{{ current_env.cloudNameWithCluster }}-composite-structure"
baseline:
  name: "{{ current_env.name }}-core"
  type: "namespace"
satellites:
  - name: "{{ current_env.name }}-bss"
    type: "namespace"
  - name: "{{ current_env.name }}-oss"
    type: "namespace"
```

### System Credentials File (in Template repository)

This file contains [Credential](#credential) objects used by EnvGene to integrate with external systems like artifact registries, GitLab, GitHub, and others.

Location: `/environments/configuration/credentials/credentials.yml|yaml`

Example:

```yaml
artifactory-cred:
  type: usernamePassword
  data:
    username: "s3cr3tN3wLogin"
    password: "s3cr3tN3wP@ss"
gitlab-token-cred:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_ba"
```

## Instance Repository Objects

### Environment Instance Objects

An Environment Instance is a file structure within the Envgene Instance Repository that describes the configuration for a specific environment/solution instance.  

It is generated during the rendering process of an Environment Template. During this rendering process, environment-agnostic parameters from the Environment Template are combined with environment-specific parameters, such as Cloud Passport, environment-specific ParameterSet, environment-specific Resource Profile Overrides, to produce a set of parameters specific to a particular environment/solution instance.  

The Environment Inventory is mandatory for creating an Environment Instance. It is a configuration file that describes a specific environment, including which Environment Template artifact to use and which environment-specific parameters to apply during rendering. It serves as the "recipe" for creating an Environment Instance.  

The Environment Instance has a human-readable structure and is not directly used by parameter consumers. For parameter consumers, a consumer-specific structure is generated based on the Environment Instance. For example, for ArgoCD, an Effective Set is generated.

EnvGene adds the following header to all auto-generated objects (all Environment Instance objects are auto-generated):

```yaml
# The contents of this file is generated from template artifact: <environment-template-artifact>.
# Contents will be overwritten by next generation.
# Please modify this contents only for development purposes or as workaround.
```

> [!NOTE]
> The \<environment-template-artifact> placeholder is automatically replaced with the name of the EnvGene Environment Template artifact used for generation.

EnvGene sorts every Environment Instance object according to its JSON schema. This ensures that when objects are modified (e.g., when applying a new template version), the repository commits remain human-readable.

EnvGene validates each Environment Instance object against the corresponding [JSON schema](/schemas/).

#### Tenant

The Tenant object is generated from the [Tenant Template](#tenant-template) during environment instance creation. It defines tenant-level properties and parameters. The Tenant object is located at `/environments/<cluster-name>/<env-name>/tenant.yml`.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the tenant. Usually set to the environment template name. | Used as an identifier in logs, UI, and for reference in templates. |
| **registryName** | string | No | The name of the registry to use. Usually set to "default". | Used to determine which registry to use for container images. |
| **description** | string | No | A description of the tenant. | Used for documentation and display purposes in UI. |
| **owners** | string | No | The owners of the tenant. | Used for documentation and notification purposes. |
| **gitRepository** | string | No | The Git repository URL for the tenant configuration. | Used to track the source of tenant configuration. |
| **defaultBranch** | string | No | The default Git branch for the tenant configuration. | Used to determine which branch to use when fetching tenant configuration. |
| **credential** | string | No | The credential ID for accessing the Git repository. | Used to authenticate with the Git repository. |
| **labels** | array of strings | No | Labels for the tenant. | Used for filtering and organization in UI and APIs. |

##### globalE2EParameters

Global end-to-end testing parameters for the tenant.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **pipelineDefaultRecipients** | string | No | Default recipients for pipeline notifications. | Used to determine who receives pipeline notifications by default. |
| **recipientsStrategy** | string | No | Strategy for merging recipients. Usually "merge". | Controls how recipients are merged when multiple sources define recipients. |
| **mergeTenantsAndE2EParameters** | boolean | No | Whether to merge tenant parameters and E2E parameters. Usually false. | Controls parameter merging behavior during effective set generation. |
| **environmentParameters** | object | No | Environment-specific parameters for E2E testing. | Used to configure environment-specific aspects of E2E testing. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the tenant level. | Used during deployment to configure applications across all namespaces. |

##### Usage in Flow

The Tenant object is used in several key processes:

1. **Template Rendering**: The tenant properties are used in Jinja2 templates to generate environment-specific configurations.

2. **Effective Set Generation**: The tenant object is used to generate effective parameter sets for deployments by providing tenant-level parameters that apply across all namespaces.

3. **Environment Building**: The tenant object is used during environment building to configure tenant-level aspects of the environment.

4. **Pipeline Configuration**: The tenant's globalE2EParameters are used to configure pipeline notifications and testing parameters.

[Tenant JSON schema](/schemas/tenant.schema.json)

#### Cloud

The Cloud object is generated from the [Cloud Template](#cloud-template) during environment instance creation. It defines cloud-level parameters for environment generation. The Cloud object is located at `/environments/<cluster-name>/<env-name>/cloud.yml`.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the cloud configuration. Usually set to the cluster name. | Used as an identifier in logs, UI, and for reference in templates. |
| **apiUrl** | string | Yes | The URL of the Kubernetes API server. | Used to connect to the Kubernetes cluster for deployments and operations. |
| **apiPort** | string | Yes | The port of the Kubernetes API server. Usually "6443" for HTTPS. | Used along with apiUrl to form the complete connection string to the Kubernetes API. |
| **privateUrl** | string | No | The private URL of the cloud. | Rarely used in templates. Potential candidate for deprecation. |
| **publicUrl** | string | Yes | The public URL of the cloud. | Used to generate URLs for various services and in templates. |
| **dashboardUrl** | string | No | The URL of the Kubernetes dashboard. | Used in UI links and stored in deployParameters as CLOUD_DASHBOARD_URL. |
| **labels** | array of strings | No | Labels for the cloud. | Rarely used for filtering or organization. Potential candidate for deprecation. |
| **defaultCredentialsId** | string | Yes | The default credentials ID for accessing the cloud. Usually "token". | Used to authenticate with the Kubernetes API. |
| **protocol** | string | Yes | The protocol used to connect to the Kubernetes API. Usually "https". | Used along with apiUrl and apiPort to form the complete connection string. |
| **mergeDeployParametersAndE2EParameters** | boolean | No | Whether to merge deployParameters and e2eParameters. Usually false. | Controls parameter merging behavior during effective set generation. Potential candidate for deprecation. |
| **dbMode** | string | No | The database mode. Usually "db". | Rarely used for configuration variations. Potential candidate for deprecation. |
| **databases** | array | No | List of databases. Usually empty. | Rarely used and might be redundant with dbaasConfigs. Potential candidate for deprecation. |

##### maasConfig

Configuration for the Monitoring as a Service (MaaS) component.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing MaaS. | Used to authenticate with the MaaS service. |
| **maasUrl** | string | Yes (if enable is true) | The URL of the MaaS service. | Used to connect to the MaaS service for monitoring operations. |
| **maasInternalAddress** | string | Yes (if enable is true) | The internal address of the MaaS service. | Used for internal service-to-service communication with MaaS. |
| **enable** | boolean | Yes | Whether MaaS is enabled. | Controls whether MaaS configuration is applied during environment building. |

##### vaultConfig

Configuration for the Vault service for secrets management.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **url** | string | Yes (if enable is true) | The URL of the Vault service. | Used to connect to the Vault service for secrets operations. |
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing Vault. | Used to authenticate with the Vault service. |
| **enable** | boolean | Yes | Whether Vault is enabled. | Controls whether Vault configuration is applied during environment building. |

##### dbaasConfigs

Configuration for the Database as a Service (DBaaS) component. This is an array of DBaaS configurations.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **credentialsId** | string | Yes (if enable is true) | The credentials ID for accessing DBaaS. | Used to authenticate with the DBaaS service. |
| **apiUrl** | string | Yes (if enable is true) | The API URL of the DBaaS service. | Used to connect to the DBaaS service for database operations. |
| **aggregatorUrl** | string | Yes (if enable is true) | The aggregator URL of the DBaaS service. | Used for aggregated database operations. |
| **enable** | boolean | Yes | Whether DBaaS is enabled. | Controls whether DBaaS configuration is applied during environment building. |

##### consulConfig

Configuration for the Consul service for service discovery and configuration.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **tokenSecret** | string | Yes (if enabled is true) | The token secret for Consul. | Used to authenticate with the Consul service. |
| **publicUrl** | string | Yes (if enabled is true) | The public URL of the Consul service. | Used to connect to the Consul service from outside the cluster. |
| **enabled** | boolean | Yes | Whether Consul is enabled. | Controls whether Consul configuration is applied during environment building. |
| **internalUrl** | string | Yes (if enabled is true) | The internal URL of the Consul service. | Used for internal service-to-service communication with Consul. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters. | Used during deployment to configure applications. |
| **e2eParameters** | object | No | Key-value pairs of end-to-end testing parameters. | Used during testing to configure test environments. |
| **technicalConfigurationParameters** | object | No | Key-value pairs of technical configuration parameters. | Used for technical configurations that are not directly related to deployment or testing. |
| **deployParameterSets** | array of strings | No | List of deployment parameter set names to include. | Used to include predefined sets of deployment parameters. |
| **e2eParameterSets** | array of strings | No | List of end-to-end testing parameter set names to include. | Used to include predefined sets of testing parameters. |
| **technicalConfigurationParameterSets** | array of strings | No | List of technical configuration parameter set names to include. | Used to include predefined sets of technical configuration parameters. |

##### Usage in Flow

The Cloud object is used in several key processes:

1. **Template Rendering**: The cloud properties are used in Jinja2 templates to generate environment-specific configurations.

2. **Cloud Passport Processing**: The cloud object is updated with values from the cloud passport during environment instance creation. The `cloud_passport.py` script maps keys from cloud passport to cloud object properties using a substitution dictionary.

3. **Effective Set Generation**: The cloud object is used in `effective_set_generator.py` to generate effective parameter sets for deployments by merging parameters from various sources.

4. **Environment Building**: The cloud object is used during environment building to configure various services and components, especially the MaaS, Vault, DBaaS, and Consul services.

##### Potential Deprecation Candidates

1. **privateUrl**: Often set to an empty string and rarely used in templates.

2. **dbMode**: Usually set to "db" and doesn't seem to be actively used for configuration variations.

3. **databases**: Often empty and might be redundant with dbaasConfigs.

4. **mergeDeployParametersAndE2EParameters**: Usually set to false and might not be actively used.

5. **labels**: Often empty and doesn't appear to be actively used for filtering or organization.

[Cloud JSON schema](/schemas/cloud.schema.json)

#### Namespace

The Namespace object is generated from the [Namespace Template](#namespace-template) during environment instance creation. It defines namespace-level parameters for environment generation. The Namespace object is located at `/environments/<cluster-name>/<env-name>/Namespaces/<namespace-name>/namespace.yml`.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the namespace. Usually follows the pattern `<env-name>-<namespace-purpose>`. | Used as the Kubernetes namespace name and as an identifier in logs, UI, and templates. |
| **tenantName** | string | No | The name of the tenant this namespace belongs to. | Used to associate the namespace with its tenant for parameter inheritance and organization. |
| **credentialsId** | string | No | The credentials ID for accessing the namespace. | Used for authentication when performing operations in this namespace. |
| **labels** | array of strings | No | Labels for the namespace. Usually includes solution instance and solution labels. | Used for filtering, organization, and grouping in UI and APIs. |
| **isServerSideMerge** | boolean | Yes | Whether to perform parameter merging on the server side. | Controls where parameter merging happens during deployment. |
| **cleanInstallApprovalRequired** | boolean | Yes | Whether clean installations require approval. | Controls the approval workflow for clean installations in this namespace. |
| **mergeDeployParametersAndE2EParameters** | boolean | Yes | Whether to merge deployParameters and e2eParameters. | Controls parameter merging behavior during effective set generation. |

##### profile

Resource profile configuration for the namespace.

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | No | The name of the resource profile override to use. | Used to determine which resource profile override to apply to applications in this namespace. |
| **baseline** | string | No | The baseline profile to use. Usually one of "dev", "dev-ha", "prod", or "prod-nonha". | Used as the base resource profile before applying overrides. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the namespace level. | Used during deployment to configure applications in this namespace. |
| **e2eParameters** | object | No | Key-value pairs of end-to-end testing parameters at the namespace level. | Used during testing to configure test environments for this namespace. |
| **technicalConfigurationParameters** | object | No | Key-value pairs of technical configuration parameters at the namespace level. | Used for technical configurations specific to this namespace. |
| **deployParameterSets** | array of strings | No | List of deployment parameter set names to include at the namespace level. | Used to include predefined sets of deployment parameters for this namespace. |
| **e2eParameterSets** | array of strings | No | List of end-to-end testing parameter set names to include at the namespace level. | Used to include predefined sets of testing parameters for this namespace. |
| **technicalConfigurationParameterSets** | array of strings | No | List of technical configuration parameter set names to include at the namespace level. | Used to include predefined sets of technical configuration parameters for this namespace. |

##### Usage in Flow

The Namespace object is used in several key processes:

1. **Template Rendering**: The namespace properties are used in Jinja2 templates to generate namespace-specific configurations.

2. **Effective Set Generation**: The namespace object is used to generate effective parameter sets for deployments by providing namespace-level parameters that apply to applications in this namespace.

3. **Environment Building**: The namespace object is used during environment building to create and configure the Kubernetes namespace and its resources.

4. **Resource Profile Application**: The namespace's profile is used to determine which resource profile overrides to apply to applications in this namespace.

5. **Deployment Configuration**: The namespace's parameters and parameter sets are used to configure deployments in this namespace.

[Namespace JSON schema](/schemas/namespace.schema.json)

#### Application

The Application object is generated during environment instance creation based on the Solution Descriptor. It defines application-level parameters for environment generation.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the application. | Used as an identifier for the application in logs, UI, and templates. |
| **version** | string | Yes | The version of the application to deploy. | Used to determine which version of the application to deploy. |
| **deployPostfix** | string | No | A postfix to add to the deployment name. | Used to create unique deployment names when multiple versions of the same application are deployed. |
| **namespace** | string | Yes | The namespace where the application will be deployed. | Used to determine which Kubernetes namespace to deploy the application to. |

##### Parameter Sets

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **deployParameters** | object | No | Key-value pairs of deployment parameters at the application level. | Used during deployment to configure this specific application. |
| **e2eParameters** | object | No | Key-value pairs of end-to-end testing parameters at the application level. | Used during testing to configure test environments for this specific application. |
| **technicalConfigurationParameters** | object | No | Key-value pairs of technical configuration parameters at the application level. | Used for technical configurations specific to this application. |

##### Usage in Flow

The Application object is used in several key processes:

1. **Effective Set Generation**: The application object is used to generate effective parameter sets for deployments by providing application-specific parameters.

2. **Deployment**: The application object is used during deployment to determine which version of the application to deploy and how to configure it.

3. **Testing**: The application object is used during testing to configure test environments for this specific application.

#### Resource Profile Override (in Instance)

The Resource Profile Override object is generated from the [Resource Profile Override Template](#resource-profile-override-in-template) during environment instance creation. It defines resource allocation overrides for applications in a namespace. The Resource Profile Override object is located at `/environments/<cluster-name>/<env-name>/Namespaces/<namespace-name>/resource_profile_override.yml`.

##### Properties

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the resource profile override. | Used to identify the resource profile override in logs and references. |
| **baseline** | string | Yes | The baseline profile used. Usually one of "dev", "dev-ha", "prod", or "prod-nonha". | Used as the base resource profile before applying overrides. |
| **description** | string | No | A description of the resource profile override. | Used for documentation purposes. |
| **applications** | array | Yes | List of applications with their service overrides. | The actual resource overrides for applications and their services. |
| **version** | number | No | The version of the resource profile override. | Used for versioning and tracking changes. |

##### applications

Each item in the applications array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the application. | Used to identify which application the overrides apply to. |
| **version** | string | No | The version of the application. | Used to specify which version of the application the overrides apply to. |
| **sd** | string | No | The solution descriptor for the application. | Used to link the application to its solution descriptor. |
| **services** | array | Yes | List of services with their parameter overrides. | The actual resource overrides for services within the application. |

##### services

Each item in the services array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the service. | Used to identify which service the overrides apply to. |
| **parameters** | array | Yes | List of parameter overrides for the service. | The actual resource parameter overrides for the service. |

##### parameters

Each item in the parameters array has the following properties:

| Property | Type | Required | Description | Usage in Flow |
|----------|------|----------|-------------|---------------|
| **name** | string | Yes | The name of the parameter to override. | Used to identify which parameter to override. |
| **value** | string | Yes | The value to set for the parameter. | The actual override value for the parameter. |

##### Usage in Flow

The Resource Profile Override object is used in several key processes:

1. **Deployment Configuration**: During deployment, the resource profile overrides are applied to control CPU, memory, and other resource allocations for applications and services.

2. **Resource Management**: The resource profile overrides help in managing and optimizing resource usage in the Kubernetes cluster.

3. **Environment Optimization**: Resource Profile Overrides allow for fine-grained control over resource allocation, making it possible to optimize resource usage based on environment requirements and constraints.

#### Composite Structure

This object describes the composite structure of a solution. It contains information about which namespace hosts the core applications that offer essential tools and services for business microservices (`baseline`), and which namespace contains the applications that consume these services (`satellites`). It has the following structure:

```yaml
name: <composite-structure-name>
baseline:
  name: <baseline-namespace>
  type: namespace
satellites:
  - name: <satellite-namespace-1>
    type: namespace
  - name: <satellite-namespace-2>
    type: namespace
```

The Composite Structure is located in the path `/configuration/environments/<CLUSTER-NAME>/<ENV-NAME>/composite-structure.yml`

[Composite Structure JSON schema](/schemas/composite-structure.schema.json)

Example:

```yaml
name: "clusterA-env-1-composite-structure"
baseline:
  name: "env-1-core"
  type: "namespace"
satellites:
  - name: "env-1-bss"
    type: "namespace"
  - name: "env-1-oss"
    type: "namespace"
```

#### Environment Credentials File

This file stores all [Credential](#credential) objects of the Environment Instance upon generation

Location: `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml`

Example:

```yaml
db_cred:
  type: usernamePassword
  data:
    username: "s3cr3tN3wLogin"
    password: "s3cr3tN3wP@ss"
token:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_ba"
```

#### Solution Descriptor

The Solution Descriptor (SD) defines the application composition of a solution. In EnvGene it serves as the primary input for EnvGene's Effective Set calculations. The SD can also be used for template rendering through the [`current_env.solution_structure`](/docs/template-macros.md#current_envsolution_structure) variable.

Other systems can use it for other reasons, for example as a deployment blueprint for external systems.

Only SD versions 2.1 and 2.2 can be used by EnvGene for the purposes described above, as their `application` list elements contain the `deployPostfix` and `version` attributes.

SD processing in EnvGene is described [here](/docs/sd-processing.md).

SD in EnvGene can be introduced either through a manual commit to the repository or by running the Instance repository pipeline. The parameters of this [pipeline](/docs/instance-pipeline-parameters.md) that start with `SD_` relate to SD processing.

In EnvGene, there are:

**Full SD**: Defines the complete application composition of a solution. There can be only one Full SD per environment, located at the path `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yml`

**Delta SD**: A partial Solution Descriptor that contains incremental changes to be applied to the Full SD. Delta SDs enable selective updates to solution components without requiring a complete SD replacement. There can be only one Delta SD per environment, located at the path `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yml`

Only Full SD is used for Effective Set calculation. The Delta SD is only needed for troubleshooting purposes.

Example:

```yaml
version: 2.1
type: "solutionDeploy"
deployMode: "composite"
applications:
  - version: "MONITORING:0.64.1"
    deployPostfix: "platform-monitoring"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres-services:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql-dbaas"
```

### Credential

This object is used by EnvGene to manage sensitive parameters. It is generated during environment instance creation for each `<cred-id>` specified in [Credential macros](/docs/template-macros.md#credential-macros)

There are two Credential types with different structures:

#### `usernamePassword`

```yaml
<cred-id>:
  type: usernamePassword
  data:
    username: <value>
    password: <value>
```

#### `secret`

```yaml
<cred-id>:
  type: "secret"
  data:
    secret: <value>
```

After generation, `<value>` is set to `envgeneNullValue`. The user must manually set the actual value.

[Credential JSON schema](/schemas/credential.schema.json)

### Shared Credentials File

This file provides centralized storage for [Credential](#credential) values that can be shared across multiple environments. During Environment Instance generation, EnvGene automatically copies relevant Credential objects from these shared files into the [Environment Credentials File](#environment-credentials-file)

The relationship between Shared Credentials and Environment is established through:

- The `envTemplate.sharedMasterCredentialFiles` property in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- The property value should be the filename (without extension) of the Shared Credentials File

Credentials can be defined at three scopes with different precedence:

1. **Environment-level**  
   Location: `/environments/<cluster-name>/<env-name>/Inventory/credentials/`
2. **Cluster-level**  
   Location: `/environments/<cluster-name>/credentials/`
3. **Site-level**  
   Location: `/environments/credentials/`

EnvGene checks these locations in order (environment → cluster → site) and uses the first matching file found.

Any YAML file located in these folders is treated as a Shared Credentials File.

Example:

```yaml
db_cred:
  type: usernamePassword
  data:
    username: "s3cr3tN3wLogin"
    password: "s3cr3tN3wP@ss"
token:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_ba"
```

### System Credentials File (in Instance repository)

This file contains [Credential](#credential) objects used by EnvGene to integrate with external systems like artifact registries, GitLab, GitHub, and others.

Location:
  
- `/environments/configuration/credentials/credentials.yml|yaml`
- `/environments/<cluster-name>/app-deployer/<any-string>-creds.yml|yaml`

Example:

```yaml
registry-cred:
  type: usernamePassword
  data:
    username: "s3cr3tN3wLogin"
    password: "s3cr3tN3wP@ss"
gitlab-token-cred:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_ba"
```

### Cloud Passport

Cloud Passport is contracted set of environment-specific deployment parameters that enables a business solution instance's (Environment) applications to access cloud infrastructure resources from a platform solution instance (Environment).

A Cloud Passport can be obtained either through cloud discovery (using the Cloud Passport Discovery Tool) or manually gathered.

#### Main File

Contains non-sensitive Cloud Passport parameters

Location: `/environments/<cluster-name>/cloud-passport/<any-string>.yml|yaml`

#### Credential File

Contains sensitive Cloud Passport parameters

Location: `/environments/<cluster-name>/cloud-passport/<any-string>-creds.yml|yaml`
