# EnvGene Objects

- [EnvGene Objects](#envgene-objects)
  - [Template Repository Objects](#template-repository-objects)
    - [Environment Template Objects](#environment-template-objects)
      - [Template Descriptor](#template-descriptor)
      - [Tenant Template](#tenant-template)
      - [Cloud Template](#cloud-template)
      - [Namespace Template](#namespace-template)
      - [Template ParameterSet](#template-parameterset)
      - [Template Resource Profile Override](#template-resource-profile-override)
      - [Composite Structure Template](#composite-structure-template)
      - [BG Domain Template](#bg-domain-template)
      - [Registry Definition Template](#registry-definition-template)
      - [Application Definition Template](#application-definition-template)
    - [System Credentials File (in Template repository)](#system-credentials-file-in-template-repository)
  - [Instance Repository Objects](#instance-repository-objects)
    - [Environment Instance Objects](#environment-instance-objects)
      - [Tenant](#tenant)
      - [Cloud](#cloud)
      - [Namespace](#namespace)
      - [Application](#application)
      - [Resource Profile Override](#resource-profile-override)
      - [Composite Structure](#composite-structure)
      - [BG Domain](#bg-domain)
    - [Solution Descriptor](#solution-descriptor)
    - [Credential](#credential)
      - [`usernamePassword`](#usernamepassword)
      - [`secret`](#secret)
    - [Environment Credentials File](#environment-credentials-file)
    - [Shared Credentials File](#shared-credentials-file)
    - [System Credentials File (in Instance repository)](#system-credentials-file-in-instance-repository)
    - [Environment Specific ParameterSet](#environment-specific-parameterset)
    - [Environment Specific Resource Profile Override](#environment-specific-resource-profile-override)
    - [Cloud Passport](#cloud-passport)
      - [Main File](#main-file)
      - [Credential File](#credential-file)
    - [Artifact Definition](#artifact-definition)
    - [Registry Definition](#registry-definition)
      - [Registry Definition v1.0](#registry-definition-v10)
      - [Registry Definition v2.0](#registry-definition-v20)
    - [Application Definition](#application-definition)
  - [Discovery Repository Objects](#discovery-repository-objects)
    - [Cloud Passport Template](#cloud-passport-template)

## Template Repository Objects

### Environment Template Objects

An Environment Template is a file structure within the Envgene Template Repository that describes the structure of a solution — such as which namespaces are part of the solution, as well as environment-agnostic parameters, which are common to a specific type of solution.

The objects that make up the Environment Template extensively use the Jinja template engine. During the generation of an Environment Instance, Envgene renders these templates with environment-specific parameters, allowing a single template to be used for preparing configurations for similar but not entirely identical environment/solution instances.

The template repository can contain multiple Environment Templates describing configurations for different types of environments/solution instances, such as DEV, PROD, and SVT.

When a commit is made to the Template Repository, an artifact is built and published. This artifact contains all the Environment Templates located in the repository.

#### Template Descriptor

This object is a describes the structure of a solution, links to solution's components.

The name of this file serves as the name of the Environment Template. In the Environment Inventory, this name is used to specify which Environment Template from the artifact should be used.

**Location:** Any YAML file located in the `/templates/env_templates/` folder is considered a Template Descriptor.

It has the following structure:

```yaml
# Optional
# Template Inheritance configuration
# See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
parent-templates:
  # Optional
  # Value must be in `application:version` notation
  <parent-template-name>: string
# Mandatory
# Can be specified either as direct template path (string) or as an object
tenant: string
# or
tenant:
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  parent: string
# Mandatory
# Can be specified either as direct template path (string) or as an object
cloud: string
# or
cloud:
  # Optional
  template_path: string
  # Optional
  # Template Override configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
  template_override:     
  template_override:
    <yaml or jinja expression>
  # Optional
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  parent: string
  # Optional
  # Template Inheritance configuration
  # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
  overrides-parent:
    profile:
      override-profile-name: string
      parent-profile-name: string
      baseline-profile-name: string
      merge-with-parent: string
    deployParameters: hashmap
    e2eParameters: hashmap
    technicalConfigurationParameters: hashmap
    deployParameterSets: list
    e2eParameterSets: list
    technicalConfigurationParameterSets: list
composite_structure: string
namespaces:
  - # Optional
    # Path to the namespace template file
    template_path: string
    # Optional
    # Used for determining the name of the parent folder for the Namespace when generating the Environment Instance
    # If the value is not specified, the name of the namespace template file (without extension) is used
    deploy_postfix: <deploy-postfix>
    # Optional
    # See details https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
    template_override:
      <yaml or jinja expression>
    # Optional
    # Name of Namespace in Parent Template
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    name: string
    # Optional
    # Parent template name
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    parent: string
    # Optional
    # Template Inheritance configuration
    # See details in https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-inheritance.md
    overrides-parent:
      profile:
        override-profile-name: string
        parent-profile-name: string
        baseline-profile-name: string
        merge-with-parent: boolean
      deployParameters: hashmap
      e2eParameters: hashmap
      technicalConfigurationParameters: hashmap
      deployParameterSets: list
      e2eParameterSets: list
      technicalConfigurationParameterSets: list
      template_path: string
```

[Template Descriptor JSON schema](/schemas/template-descriptor.schema.json)

#### Tenant Template

TBD

#### Cloud Template

TBD

#### Namespace Template

This is a Jinja template file used to render the [Namespace](#namespace) object. It defines namespace-level parameters for Environment Instance generation.

The Namespace template must be developed so that after Jinja rendering, the result is a valid Namespace object according to the [schema](/schemas/namespace.schema.json).

[Macros](/docs/template-macros.md) are available for use when developing the template.

**Location:** The Namespace template is located at `/templates/env_templates/*/`

**Example:**

```yaml
name: "{{ current_env.name }}-core"
credentialsId: ""
labels:
  - "solutionInstance-{{current_env.name}}"
  - "solution-{{current_env.tenant}}"
isServerSideMerge: false
cleanInstallApprovalRequired: false
mergeDeployParametersAndE2EParameters: false
profile:
  name: dev-override
  baseline: dev
deployParameters:
  AIRFLOW_REDIS_DB: "1"
  ARTIFACTORY_BASE_URL: "https://artifactory.qubership.org"
  ESCAPE_SEQUENCE: "true"
e2eParameters:
  QTP_DYNAMIC_PARAMETERS: ""
technicalConfigurationParameters:
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: "${DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD}"
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: "${DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME}"
  DBAAS_TEMP_PASS: "${DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD}"
  MAAS_DEPLOYER_CLIENT_PASSWORD: "${MAAS_CREDENTIALS_PASSWORD}"
  MAAS_DEPLOYER_CLIENT_USERNAME: "${MAAS_CREDENTIALS_USERNAME}"
deployParameterSets:
  - core-deploy-common
{% if current_env.additionalTemplateVariables.site | default ('offsite') == 'offsite' %}
  - core-deploy-offsite
{% else %}
  - core-deploy-onsite
{% endif %}
technicalConfigurationParameterSets:
  - core-runtime
```

#### Template ParameterSet

A ParameterSet is a container for a set of parameters that can be reused across multiple templates. This helps to avoid duplication and simplifies parameter management. ParameterSets are processed during the generation of an Environment Instance.

ParameterSets are referenced in the `deployParameterSets`, `e2eParameterSets`, and `technicalConfigurationParameterSets` arrays in the [Cloud](#cloud-template), and [Namespace](#namespace-template) templates.

During the generation of an Environment Instance the parameters from the `parameters` section of a ParameterSet are assigned to the corresponding attributes of the object with which the ParameterSet is associated, as follows:

- Parameters from the `parameters` section of a ParameterSet referenced in `deployParameterSets` are set on the `deployParameters` attribute of the same object.
- Parameters from the `parameters` section of a ParameterSet referenced in  `e2eParameterSets` are set on `e2eParameters`.
- Parameters from the `parameters` section of a ParameterSet referenced in  `technicalConfigurationParameterSets` are set on `technicalConfigurationParameters`.

ParameterSets also allow to define application-level parameters, i.e., parameters specific to a particular application, using the `application` section of a ParameterSet. The parameters from `application[].parameters` are set on the [Application](#application) object, which is created for each `application` entry and has the name `application[].appName`.

ParameterSets can be parameterized using Jinja and [macros](/docs/template-macros.md). In this case, the file should be named `<paramset-name>.yaml.j2` or `<paramset-name>.yml.j2`.

**Location:** `/templates/parameters/` folder and its subfolders, but with a nesting level of no more than two

```yaml
# Optional
# Deprecated
version: string
# Mandatory
# The name of the Parameter Set
# Used to reference the Parameter Set in templates
# Must match the Parameter Set filename
name: string
# Mandatory
# Key-value pairs of parameters
# The actual parameters that will be set when this Parameter Set is referenced
parameters: hashmap
# Optional
# Section describing application-level parameters
# For each `appName`, an Application object will be created with parameters specified in `parameters`
application:
  - # Mandatory
    appName: string
    # Mandatory
    parameters: hashmap
```

**Example:**

```yaml
version: 1
name: configuration
parameters:
  CONFIGURATION:
    DEFAULT_MAIN_SD: "Toolset-SD"
{% if current_env.additionalTemplateVariables.site | default ('offsite') == 'offsite' %}
  DBAAS_LODB_PER_NAMESPACE_AUTOBALANCE_RULES: "postgresql=>postgresql:postgres"
{% else %}
  DBAAS_LODB_PER_NAMESPACE_AUTOBALANCE_RULES: "envgeneNullValue"
{% endif %}
applications:
  - appName: "core"
    parameters:
      securityContexts:
        pod:
          runAsNonRoot: true
          runAsUser: null
          fsGroup: null
          seccompProfile:
            type: RuntimeDefault
        containers:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
              - ALL
```

The filename of the ParameterSet must match the value of the `name` attribute. The ParameterSet name must be unique within the template repository. This is validated during processing; if the validation fails, the operation will stop with an error.

The Parameter Set schema in the template repository is identical to the [Environment Specific ParameterSet](#environment-specific-parameterset).

[ParameterSet JSON schema](/schemas/paramset.schema.json)

#### Template Resource Profile Override

These are customizations for performance parameters, over a Baseline Resource Profile. Such overrides are created by the configurator in the Template repository, to further adjust performance parameters on top of the Baseline Resource Profile Override for all environments of the same type.

Template Resource Profile Override are referenced in the `profile.name` attribute in the [Cloud](#cloud-template) or [Namespace](#namespace-template) templates.

During the generation of an Environment Instance, resource profiles that are associated with the [Cloud](#cloud) and [Namespace](#namespace) are merged or replaced with the [Environment Specific Resource Profile Override](#environment-specific-resource-profile-override) and become part of the [Resource Profile Override](#resource-profile-override) (part of the environment instance).

Template Resource Profile Override can be parameterized using Jinja and [macros](/docs/template-macros.md). In this case, the file should be named `<resource-profile-override-name>.yaml.j2` or `<resource-profile-override-name>.yml.j2`.

In Template Resource Profile Override, you can set nested parameter values using dots in the parameter name (dot notation). For example:

```yaml
...
applications:
  - name: "my-app"
    services:
      - name: "nginx"
        parameters:
          - name: "resources.limits.cpu"
            value: "1000m"
          - name: "resources.limits.memory"
            value: "512Mi"
```

See details in [resource-profile](/docs/features/resource-profile.md)

[Template Resource Profile Override JSON schema](/schemas/resource-profile.schema.json)

**Location:** `/templates/resource_profiles/` folder and its subfolders, but with a nesting level of no more than two

```yaml
# Mandatory
# Resource profile override name
# Must match the filename without extension
name: string
# Optional
# Deprecated
# Not processed by Envgene 
version: string
# Optional
# Name of the resource profile baseline that this override modifies
# Not processed by EnvGene
baseline: string
# Optional
# Override description
description: string
# Mandatory
applications:
- # Mandatory
  # Application name to which the override applies
  # Must exactly match the application name
  name: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  version: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  sd: string
  # Optional
  services:
  - # Mandatory
    # Service name to which the override applies
    # Must exactly match the service name
    name: string
    # Mandatory
    parameters:
    - # Mandatory
      # Parameter key
      name: string
      # Mandatory
      # Parameter value
      value: string OR integer OR boolean
```

**Example:**

```yaml
name: "dev_core_override"
baseline: "dev"
applications:
- name: "Cloud-Core"
  services:
  - name: "facade-operator"
    parameters:
    - name: "FACADE_GATEWAY_MEMORY_LIMIT"
      value: "96Mi"
    - name: "FACADE_GATEWAY_CPU_REQUEST"
      value: "50m"
  - name: "tenant-manager"
    parameters:
    - name: "MEMORY_LIMIT"
      value: "512Mi"
  - name: "identity-provider"
    parameters:
    - name: "PG_MAX_POOL_SIZE"
      value: "30"
```

#### Composite Structure Template

This is a Jinja template file used to render the [Composite Structure](#composite-structure) object.

**Location:** The object is located at `/templates/env_templates/*/`

**Example:**

```yaml
name: "{{ current_env.cloudNameWithCluster }}-composite-structure"
baseline:
  name: "{{ current_env.name }}-core"
  type: "namespace"
satellites:
  - name: "{{ current_env.name }}-api"
    type: "namespace"
  - name: "{{ current_env.name }}-ui"
    type: "namespace"
```

#### BG Domain Template

This is a Jinja template file used to render the [BG Domain](#bg-domain) object for environments that use Blue-Green Domain (BGD) support.

**Location:** `/templates/env-templates/{Group name}/bg-domain.yml.j2`

**Example:**

```yaml
name: "{{ current_env.name }}-bg-domain"
type: bgdomain
originNamespace:
  name: "{{ current_env.name }}-origin-bss" 
  type: namespace
peerNamespace:
  name: "{{ current_env.name }}-peer-bss" 
  type: namespace
controllerNamespace:
  name: "{{ current_env.name }}-bg-controller"
  type: namespace
  credentials: bgdomain-cred
  url: https://controller-env-1-controller.qubership.org
```

#### Registry Definition Template

This is a Jinja template file used to render the [Registry Definition](#registry-definition) object.

In addition to other macros, [`regdefs.overrides`](/docs/template-macros.md#regdefsoverrides) is available when rendering the Application Definition Template.

**Location:** `/templates/regdefs/<registry-name>.yaml|yml|yml.j2|yaml.j2`

**Example:**

```yaml
name: "registry-1"
credentialsId: "registry-cred"
mavenConfig:
  repositoryDomainName: "{{ regdefs.overrides.maven.RepositoryDomainName | default('maven.qubership.org') }}"
  fullRepositoryUrl: "{{ regdefs.overrides.maven.fullRepositoryUrl | default('https://maven.qubership.org/repository') }}"
  targetSnapshot: "snapshot"
  targetStaging: "staging"
  targetRelease: "release"
dockerConfig:
  snapshotUri: "{{ regdefs.overrides.docker.snapshotUri | default('docker.qubership.org/snapshot') }}"
  stagingUri: "{{ regdefs.overrides.docker.stagingUri | default('docker.qubership.org/staging') }}"
  releaseUri: "{{ regdefs.overrides.docker.releaseUri | default('docker.qubership.org/release') }}"
  groupUri: "{{ regdefs.overrides.docker.groupUri | default('docker.qubership.org/group') }}"
  snapshotRepoName: "docker-snapshot"
  stagingRepoName: "docker-staging"
  releaseRepoName: "docker-release"
  groupName: "docker-group"
```

#### Application Definition Template

This is a Jinja template file used to render the [Application Definition](#application-definition) object.

In addition to other macros, [`appdefs.overrides`](/docs/template-macros.md#appdefsoverrides) is available when rendering the Application Definition Template.

**Location:** `/templates/appdefs/<application-name>.yaml|yml|yml.j2|yaml.j2`

**Example:**

```yaml
name: "application-1"
registryName: "{{ appdefs.overrides.registryName | default('registry-1') }}"
artifactId: "application-1"
groupId: "org.qubership"
```

### System Credentials File (in Template repository)

This file contains [Credential](#credential) objects used by EnvGene to integrate with external systems like artifact registries, GitLab, GitHub, and others.

**Location:** `/environments/configuration/credentials/credentials.yml|yaml`

**Example:**

```yaml
artifactory-cred:
  type: usernamePassword
  data:
    username: "user-placeholder-123"
    password: "pass-placeholder-123"
gitlab-token-cred:
  type: secret
  data:
    secret: "token-placeholder-123"
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

TBD

#### Cloud

TBD

#### Namespace

The Namespace object contains namespace-level parameters — parameters that are specific to all applications within this namespace.

The Namespace object is used to generate Effective Set

The Namespace object is generated during Environment Instance generation based on:

- [Namespace Template](#namespace-template)
- [Template ParamSet](#template-parameterset)
- [Instance ParamSet](#environment-specific-parameterset)

For each parameter in the Namespace, a comment is added indicating the source Parameter Set from which this parameter originated. This is used for traceability in the generation of the environment instance.

**Location:** `/environments/<cluster-name>/<environment-name>/Namespaces/<deploy-postfix>/namespace.yml`.

```yaml
# Mandatory
# The name of the namespace
# The same as the Kubernetes namespace name
name: string
# Optional
# Pointer to the credentials ID for accessing the namespace
# Used for authentication when performing deployment in this namespace
credentialsId: string
# Optional
# List of labels for the namespace
# Used for filtering, organization, and grouping
labels: list
# Mandatory
# Whether to perform parameter merging on the server side
# Controls where parameter merging happens during deployment
isServerSideMerge: boolean
# Mandatory
# Whether clean installations require approval
# Controls the approval workflow for clean installations in this namespace
cleanInstallApprovalRequired: boolean
# Mandatory
# Whether to merge deployParameters and e2eParameters
# Controls parameter merging behavior during effective set generation
mergeDeployParametersAndE2EParameters: boolean
# Optional
# Resource profile configuration for the namespace
# Used to manage performance parameters of applications in this namespace
profile:
  # Mandatory
  # The name of the resource profile override to use
  # Used to determine which resource profile override to apply to applications in this namespace
  name: string
  # Mandatory
  # The baseline profile to use
  # Used as the base resource profile before applying overrides
  baseline: string
# Optional
# Key-value pairs of deployment parameters at the namespace level
# Used to set parameters that will be used for rendering Helm charts of applications for this namespace
deployParameters: hashmap
# Optional
# Key-value pairs of e2e parameters at the namespace level
# Used to configure the systems/pipelines managing the Environment lifecycle for this namespace
e2eParameters: hashmap
# Optional
# Key-value pairs of technical configuration parameters at the namespace level
# Used to set parameters that can be applied to the application at runtime
# without redeployment for this namespace
technicalConfigurationParameters: hashmap
# Optional
# List of deployment Parameter Set names to include at the namespace level
# Used to set parameters that will be used for rendering Helm charts of applications for this namespace
deployParameterSets: list
# Optional
# List of e2e Parameter Set names to include at the namespace level
# Used to configure the systems/pipelines managing the Environment lifecycle for this namespace
e2eParameterSets: list
# Optional
# List of technical configuration Parameter Set names to include at the namespace level
# Used to include predefined sets of parameters that can be applied to the application at runtime
# without redeployment for this namespace
technicalConfigurationParameterSets: list
```

**Example:**

```yaml
# The contents of this file is generated from template artifact: sample-template:v1.2.3.
# Contents will be overwritten by next generation.
# Please modify this contents only for development purposes or as workaround.
name: "env-1-core"
credentialsId: ""
isServerSideMerge: false
labels:
  - "solutionInstance-env-1-core"
cleanInstallApprovalRequired: false
mergeDeployParametersAndE2EParameters: false
deployParameters:
  AIRFLOW_REDIS_DB: "1"
  ARTIFACTORY_BASE_URL: "https://artifactory.qubership.org" # paramset: Namespace-common version: 23.4 source: template
  ESCAPE_SEQUENCE: "true"
e2eParameters:
  QTP_DYNAMIC_PARAMETERS: "" # paramset: nightly-parameters version: 23.4 source: template
technicalConfigurationParameters:
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: "${DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD}" # paramset: Namespace-commom-technicalConfiguration version: 23.4 source: template
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: "${DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME}" # paramset: Namespace-commom-technicalConfiguration version: 23.4 source: template
  DBAAS_TEMP_PASS: "${DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD}" # paramset: Namespace-commom-technicalConfiguration version: 23.4 source: template
  MAAS_DEPLOYER_CLIENT_PASSWORD: "${MAAS_CREDENTIALS_PASSWORD}" # paramset: Namespace-commom-technicalConfiguration version: 23.4 source: template
  MAAS_DEPLOYER_CLIENT_USERNAME: "${MAAS_CREDENTIALS_USERNAME}" # paramset: Namespace-commom-technicalConfiguration version: 23.4 source: template
deployParameterSets: []
e2eParameterSets: []
technicalConfigurationParameterSets: []
```

[Namespace JSON schema](/schemas/namespace.schema.json)

#### Application

The Application object defines parameters that are specific to a particular application. These parameters are isolated to the application and do not affect other applications.

The Application object is generated during the Environment Instance generation process, based on ParameterSets that contain an `applications` section. Generation occurs from both [ParameterSets in the template repository](#template-parameterset) and [ParameterSets in the instance repository](#environment-specific-parameterset).

For each parameter in the Application, a comment is added indicating the source Parameter Set from which this parameter originated. This is used for traceability in the generation of the environment instance.

The Application object is used to generate Effective Set by providing application-specific parameters.

**Location:** Depends on which object the ParameterSet was associated with:

- Cloud: `/environments/<cluster-name>/<environment-name>/Applications/<application-name>.yml`
- Namespace: `/environments/<cluster-name>/<environment-name>/Namespaces/<deploy-postfix>/Applications/<application-name>.yml`

```yaml
# Mandatory
# The name of the Application, generated based on the `applications[].appName`
# attribute of Parameter Set
name: string
# Optional
# Key-value pairs of deployment parameters at the application level
# If the Parameter Set is associated in `deployParameterSets`, then the parameters
# from `application[].parameters` will be set in this section
deployParameters: hashmap
# Optional
# Key-value pairs of technical configuration parameters at the application level
# If the Parameter Set is associated in `technicalConfigurationParameterSets`, then the parameters
# from `application[].parameters` will be set in this section
technicalConfigurationParameters: hashmap
```

**Example:**

```yaml
# The contents of this file is generated from template artifact: sample-template:v1.2.3
# Contents will be overwritten by next generation.
# Please modify this contents only for development purposes or as workaround.
name: "Core"
deployParameters:
  DBAAS_ISOLATION_ENABLED: "false"  # paramset: wa version: 23.3
  global.secrets.password: "${creds.get(\"streaming-cred\").password}" # paramset: management version: 23.3
  global.secrets.username: "${creds.get(\"streaming-cred\").username}" # paramset: management version: 23.3
technicalConfigurationParameters: {}

```

[Application JSON schema](/schemas/application.schema.json)

#### Resource Profile Override

These are customizations for performance parameters, over a Baseline Resource Profile.

During the generation of an Environment Instance, resource profiles that are associated with the [Cloud](#cloud) and [Namespace](#namespace) are merged or replaced with the [Environment Specific Resource Profile Override](#environment-specific-resource-profile-override) and become part of the [Resource Profile Override](#resource-profile-override) (part of the environment instance).

See details in [resource-profile](/docs/features/resource-profile.md)

[Resource Profile Override JSON schema](/schemas/resource-profile.schema.json)

**Location:** `/environments/<cluster-name>/<environment-name>/Profiles`

```yaml
# Mandatory
# Resource profile override name
# Must match the filename without extension
name: string
# Optional
# Deprecated
# Not processed by Envgene 
version: string
# Optional
# Name of the resource profile baseline that this override modifies
# Not processed by EnvGene
baseline: string
# Optional
# Override description
description: string
# Mandatory
applications:
- # Mandatory
  # Application name to which the override applies
  # Must exactly match the application name
  name: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  version: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  sd: string
  # Optional
  services:
  - # Mandatory
    # Service name to which the override applies
    # Must exactly match the service name
    name: string
    # Mandatory
    parameters:
    - # Mandatory
      # Parameter key
      # Точки в ключе параметры рассматриваются как маркер вложенной структуры
      # See details in [resource-profile](/docs/features/resource-profile.md)
      name: string
      # Mandatory
      # Parameter value
      value: string OR integer OR boolean
```

**Example:**

```yaml
name: "dev_core_override"
baseline: "dev"
applications:
- name: "Cloud-Core"
  services:
  - name: "facade-operator"
    parameters:
    - name: "FACADE_GATEWAY_MEMORY_LIMIT"
      value: "96Mi"
    - name: "FACADE_GATEWAY_CPU_REQUEST"
      value: "50m"
  - name: "tenant-manager"
    parameters:
    - name: "MEMORY_LIMIT"
      value: "512Mi"
  - name: "identity-provider"
    parameters:
    - name: "PG_MAX_POOL_SIZE"
      value: "30"
```

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

**Location:** `/configuration/environments/<CLUSTER-NAME>/<ENV-NAME>/composite_structure.yml`

[Composite Structure JSON schema](/schemas/composite-structure.schema.json)

**Example:**

```yaml
name: "clusterA-env-1-composite-structure"
baseline:
  name: "env-1-core"
  type: "namespace"
satellites:
  - name: "env-1-api"
    type: "namespace"
  - name: "env-1-ui"
    type: "namespace"
```

#### BG Domain

The BG Domain object defines the Blue-Green Domain structure and namespace mappings for environments that use BGD support. This object is used for alias resolution in the `NS_BUILD_FILTER` parameter and BGD lifecycle management.

The BG Domain object is generated during Environment Instance generation based on:

- [BG Domain Template](#bg-domain-template)

**Location:** `/environments/<cluster-name>/<environment-name>/bg_domain.yml`

```yaml
# Mandatory
# The name of the BG Domain object
# Used to identify the BGD configuration
name: <environment-name>-bg-domain
# Mandatory
# The type of the object
# Always set to 'bgdomain' for BG Domain objects
type: bgdomain
# Mandatory
# Origin namespace definition
# Used to define the currently active BGD namespace
origin:
  # Mandatory
  # The name of the origin namespace
  # Used for BGD alias resolution and lifecycle operations
  name: <origin-namespace-name>
  # Mandatory
  # The type of the namespace object
  # Always set to 'namespace'
  type: namespace
# Mandatory
# Peer namespace definition
# Used to define the standby BGD namespace
peer:
  # Mandatory
  # The name of the peer namespace
  # Used for BGD alias resolution and lifecycle operations
  name: <peer-namespace-name>
  # Mandatory
  # The type of the namespace object
  # Always set to 'namespace'
  type: namespace
# Mandatory
# Controller namespace definition
# Used for BGD lifecycle management and coordination
controller:
  # Mandatory
  # The name of the controller namespace
  # Used by BGD operations for lifecycle coordination
  name: <controller-namespace-name>
  # Mandatory
  # The type of the namespace object
  # Always set to 'namespace'
  type: namespace
  # Mandatory
  # Credentials for accessing the BGD controller
  # Used for authentication with BG-Operator
  credentialsIs: <bgd-controller-credentials>
  # Mandatory
  # URL of the BG-Operator service
  # Used for BGD lifecycle operations
  url: <bg-operator-url>
```

**BGD Alias Resolution:** Used by `NS_BUILD_FILTER` parameter to resolve BGD aliases:

- `${controller}` → controller namespace
- `${origin}` → origin namespaces
- `${peer}` → peer namespaces

### Solution Descriptor

The Solution Descriptor (SD) defines the application composition of a solution. In EnvGene it serves as the primary input for EnvGene's Effective Set calculations. The SD can also be used for template rendering through the [`current_env.solution_structure`](/docs/template-macros.md#current_envsolution_structure) variable.

Other systems can use it for other reasons, for example as a deployment blueprint for external systems.

Only SD versions 2.1 and 2.2 can be used by EnvGene for the purposes described above, as their `application` list elements contain the `deployPostfix` and `version` attributes.

For details on how EnvGene processes SD, refer to the [SD Processing documentation](/docs/features/sd-processing.md).

SD in EnvGene can be introduced either through a manual commit to the repository or by running the Instance repository pipeline. The parameters of this [pipeline](/docs/instance-pipeline-parameters.md) that start with `SD_` relate to SD processing.

In EnvGene, there are:

**Full SD**: Defines the complete application composition of a solution. There can be only one Full SD per environment, located at the path `/environments/<cluster-name>/<environment-name>/Inventory/solution-descriptor/sd.yml`

**Delta SD**: A partial Solution Descriptor that contains incremental changes to be applied to the Full SD. Delta SDs enable selective updates to solution components without requiring a complete SD replacement. There can be only one Delta SD per environment, located at the path `/environments/<cluster-name>/<environment-name>/Inventory/solution-descriptor/delta_sd.yml`

Only Full SD is used for Effective Set calculation. The Delta SD is only needed for troubleshooting purposes.

**Example:**

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

This object is used by EnvGene to manage sensitive parameters. It is generated during environment instance creation for each `<cred-id>` specified in [Credential macros](/docs/template-macros.md#credential-macro)

There are two Credential types with different structures:

#### `usernamePassword`

Used for credentials requiring username/password pairs. Contains two mandatory credentials fields(`username` and `password`):

```yaml
<cred-id>:
  type: usernamePassword
  data:
    username: string
    password: string
```

#### `secret`

Used for single-secret credentials. Contains one mandatory credentials field(`secret`):

```yaml
<cred-id>:
  type: secret
  data:
    secret: string
```

After generation, `<value>` is set to `envgeneNullValue`. The user must manually set the actual value.

[Credential JSON schema](/schemas/credential.schema.json)

### Environment Credentials File

This file stores all [Credential](#credential) objects of the Environment upon generation

**Location:** `/environments/<cloud-name>/<environment-name>/Credentials/credentials.yml`

**Example:**

```yaml
db_cred:
  type: usernamePassword
  data:
    username: "user-placeholder-123"
    password: "pass-placeholder-123"
token:
  type: secret
  data:
    secret: "token-placeholder-123"
```

### Shared Credentials File

This file provides centralized storage for [Credential](#credential) values that can be shared across multiple environments. During Environment Instance generation, EnvGene automatically copies relevant Credential objects from these shared files into the [Environment Credentials File](#environment-credentials-file)

The relationship between Shared Credentials and Environment is established through:

- The `envTemplate.sharedMasterCredentialFiles` property in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- The property value should be the filename (without extension) of the Shared Credentials File

Credentials can be defined at three scopes with different precedence:

1. **Environment-level**
   **Location:** `/environments/<cluster-name>/<environment-name>/Inventory/credentials/`
2. **Cluster-level**
   **Location:** `/environments/<cluster-name>/credentials/`
3. **Site-level**
   **Location:** `/environments/credentials/`

EnvGene checks these locations in order (environment → cluster → site) and uses the first matching file found.

Any YAML file located in these folders is treated as a Shared Credentials File.

**Example:**

```yaml
db_cred:
  type: usernamePassword
  data:
    username: "user-placeholder-123"
    password: "pass-placeholder-123"
token:
  type: secret
  data:
    secret: "token-placeholder-123"
```

### System Credentials File (in Instance repository)

This file contains [Credential](#credential) objects used by EnvGene to integrate with external systems like artifact registries, GitLab, GitHub, and others.

Location:

- `/environments/configuration/credentials/credentials.yml|yaml`
- `/environments/<cluster-name>/app-deployer/<any-string>-creds.yml|yaml`

**Example:**

```yaml
registry-cred:
  type: usernamePassword
  data:
    username: "user-placeholder-123"
    password: "pass-placeholder-123"
gitlab-token-cred:
  type: secret
  data:
    secret: "token-placeholder-123"
```

### Environment Specific ParameterSet

TBD

### Environment Specific Resource Profile Override

These are customizations for performance parameters, over a Baseline Resource Profile and Template Resource Profile Override.
Such overrides are created by the configurator in the Instance repository, to further adjust performance parameters on top of the Baseline Resource Profile and Template Resource Profile Override.

The Environment-Specific Resource Profile Override is specified individually for each Namespace or Cloud via `envTemplate.envSpecificResourceProfiles` parameter of the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

During the generation of an Environment Instance, resource profiles that are associated with the [Cloud](#cloud) and [Namespace](#namespace) are merged or replaced with the [Environment Specific Resource Profile Override](#environment-specific-resource-profile-override) and become part of the [Resource Profile Override](#resource-profile-override) (part of the environment instance).

Environment Specific Resource Profile Override can be parameterized using Jinja and [macros](/docs/template-macros.md). In this case, the file should be named `<resource-profile-override-name>.yaml.j2` or `<resource-profile-override-name>.yml.j2`.

In Environment Specific Resource Profile Override, you can set nested parameter values using dots in the parameter name (dot notation). For example:

```yaml
...
applications:
  - name: "my-app"
    services:
      - name: "nginx"
        parameters:
          - name: "resources.limits.cpu"
            value: "1000m"
          - name: "resources.limits.memory"
            value: "512Mi"
```

See details in [resource-profile](/docs/features/resource-profile.md)

[Environment Specific Resource Profile Override JSON schema](/schemas/resource-profile.schema.json)

**Location:**

When an Environment Specific Resource Profile Override is referenced, EnvGene searches for the corresponding YAML file in the Instance repository using the following location priority (from highest to lowest):

1. `/environments/<cluster-name>/<environment-name>/Inventory/resource_profiles` — Environment-specific, highest priority  
2. `/environments/<cluster-name>/resource_profiles` — Cluster-wide, applies to all environments in the cluster  
3. `/environments/resource_profiles` — Global, common for the entire repository  

The first match found is used as the environment-specific override for the given Cloud or Namespace.

```yaml
# Mandatory
# Resource profile override name
# Must match the filename without extension
name: string
# Optional
# Deprecated
# Not processed by Envgene 
version: string
# Optional
# Name of the resource profile baseline that this override modifies
# Not processed by EnvGene
baseline: string
# Optional
# Override description
description: string
# Mandatory
applications:
- # Mandatory
  # Application name to which the override applies
  # Must exactly match the application name
  name: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  version: string
  # Optional
  # Deprecated
  # Not processed by Envgene 
  sd: string
  # Optional
  services:
  - # Mandatory
    # Service name to which the override applies
    # Must exactly match the service name
    name: string
    # Mandatory
    parameters:
    - # Mandatory
      # Parameter key
      # Точки в ключе параметры рассматриваются как маркер вложенной структуры
      # See details in [resource-profile](/docs/features/resource-profile.md)
      name: string
      # Mandatory
      # Parameter value
      value: string OR integer OR boolean
```

**Example:**

```yaml
name: "dev_core_override"
baseline: "dev"
applications:
- name: "Cloud-Core"
  services:
  - name: "facade-operator"
    parameters:
    - name: "FACADE_GATEWAY_MEMORY_LIMIT"
      value: "96Mi"
    - name: "FACADE_GATEWAY_CPU_REQUEST"
      value: "50m"
  - name: "tenant-manager"
    parameters:
    - name: "MEMORY_LIMIT"
      value: "512Mi"
  - name: "identity-provider"
    parameters:
    - name: "PG_MAX_POOL_SIZE"
      value: "30"
```

### Cloud Passport

Cloud Passport is contracted set of environment-specific deployment parameters that enables a business solution instance's (Environment) applications to access cloud infrastructure resources from a platform solution instance (Environment).

A Cloud Passport can be obtained either through cloud discovery (using the Cloud Passport Discovery Tool) or manually gathered.

#### Main File

Contains non-sensitive Cloud Passport parameters

**Location:** `/environments/<cluster-name>/cloud-passport/<any-string>.yml|yaml`

#### Credential File

Contains sensitive Cloud Passport parameters

**Location:** `/environments/<cluster-name>/cloud-passport/<any-string>-creds.yml|yaml`

### Artifact Definition

This object describes where the **environment template artifact** is stored in the registry. It is used to convert the `application:version` format of an artifact template into the registry and Maven artifact parameters needed to download it.

**Location:** `/configuration/artifact_definitions/<artifact-definition-name>.yaml`

The filename must match the value of the `name` attribute.

```yaml
# Mandatory
# Name of the artifact template. This corresponds to the `application` part in the `application:version` notation.
name: string
# Mandatory
# Artifact template Maven group id
groupId: string
# Mandatory
# Artifact template Maven artifact id
artifactId: string
# Mandatory
registry:
  # Mandatory
  # Name of the registry where the artifact is stored
  name: string
  # Mandatory
  # Pointer to the EnvGene Credential object.
  # Credential with this ID must be located in /configuration/credentials/credentials.yml
  credentialsId: string
  # Mandatory
  mavenConfig:
    # Mandatory
    # URL of the registry where the artifact is stored
    repositoryDomainName: string
    # Mandatory
    # Snapshot repository name
    # EnvGene checks repositories in this order: release -> staging -> snapshot
    # It stops when it finds the artifact
    targetSnapshot: string
    # Mandatory
    # Staging repository name
    targetStaging: string
    # Mandatory
    # Release repository name
    targetRelease: string
```

**Example:**

```yaml
name: "env-template"
groupId: "org.qubership"
artifactId: "env-template"
registry:
  name: "sandbox"
  credentialsId: "artifactory-cred"
  mavenConfig:
    repositoryDomainName: "https://artifactory.qubership.org"
    targetSnapshot: "mvn.snapshot"
    targetStaging: "mvn.staging"
    targetRelease: "mvn.release"
```

[Artifact Definition JSON schema](/schemas/artifact-definition.schema.json)

### Registry Definition

This object describes registry where artifacts (other than environment template artifacts) are stored.

It is used by **external systems** to convert the `application:version` format of an artifact template into the registry and Maven artifact parameters required to download it.

A separate definition file is used for each individual registry. Each Environment uses its own set of Registry Definitions.

The filename must match the value of the `name` attribute.

**Location:** `/environments/<cluster-name>/<environment-name>/RegDefs/<registry-name>.yml`

Two versions of this object are supported

#### Registry Definition v1.0

```yaml
# Mandatory
# Name of the registry
name: string
# Mandatory
# Pointer to the EnvGene Credential object.
# Credential with this ID must be located in /environments/<cluster-name>/<environment-name>/Credentials/credentials.yml
credentialsId: string
# Mandatory
mavenConfig:
  # Mandatory
  # Domain name of the Maven registry
  repositoryDomainName: string
  # Mandatory
  # Full URL of the Maven registry
  fullRepositoryUrl: string
  # Mandatory
  # Snapshot Maven repository name
  targetSnapshot: string
  # Mandatory
  # Staging Maven repository name
  targetStaging: string
  # Mandatory
  # Release Maven repository name
  targetRelease: string
  # Mandatory
  # Snapshot Maven repository name
  snapshotGroup: string
  # Mandatory
  # Release Maven repository name
  releaseGroup: string
# Mandatory
dockerConfig:
  # Mandatory
  # URI for Docker snapshot registry
  snapshotUri: string
  # Mandatory
  # URI for Docker staging repository
  stagingUri: string
  # Mandatory
  # URI for Docker release repository
  releaseUri: string
  # Mandatory
  # URI for Docker group repository
  groupUri: string
  # Mandatory
  # Name of Docker snapshot repository
  snapshotRepoName: string
  # Mandatory
  # Name of Docker staging repository
  stagingRepoName: string
  # Mandatory
  # Name of Docker release repository
  releaseRepoName: string
  # Mandatory
  # Name of Docker group
  groupName: string
  # Optional
helmConfig:
  # Mandatory
  # Helm staging repository name
  helmTargetStaging: string
  # Mandatory
  # Helm release repository name
  helmTargetRelease: string
# Optional
helmAppConfig:
  # Mandatory
  # Helm staging repository name for application charts
  helmStagingRepoName: string
  # Mandatory
  # Helm release repository name for application charts
  helmReleaseRepoName: string
  # Mandatory
  # Helm group repository name for application charts
  helmGroupRepoName: string
  # Mandatory
  # Helm dev repository name for application charts
  helmDevRepoName: string
# Optional
goConfig:
  # Mandatory
  # Go snapshot repository name
  goTargetSnapshot: string
  # Mandatory
  # Go release repository name
  goTargetRelease: string
  # Mandatory
  # Go proxy repository URL
  goProxyRepository: string
# Optional
rawConfig:
  # Mandatory
  # Raw snapshot repository name
  rawTargetSnapshot: string
  # Mandatory
  # Raw release repository name
  rawTargetRelease: string
  # Mandatory
  # Raw staging repository name
  rawTargetStaging: string
  # Mandatory
  # Raw proxy repository name
  rawTargetProxy: string
# Optional
npmConfig:
  # Mandatory
  # npm snapshot repository name
  npmTargetSnapshot: string
  # Mandatory
  # npm release repository name
  npmTargetRelease: string
```

**Example:**

```yaml
name: sandbox
credentialsId: nexus-credentials
mavenConfig:
  repositoryDomainName: nexus.qubership.org
  fullRepositoryUrl: https://nexus.qubership.org/repository
  targetSnapshot: maven-snapshots
  targetStaging: maven-staging
  targetRelease: maven-releases
  snapshotGroup: maven-snapshots-group
  releaseGroup: maven-releases-group
dockerConfig:
  snapshotUri: docker.qubership.org/snapshots
  stagingUri: docker.qubership.org/staging
  releaseUri: docker.qubership.org/releases
  groupUri: docker.qubership.org/group
  snapshotRepoName: docker-snapshots
  stagingRepoName: docker-staging
  releaseRepoName: docker-releases
  groupName: docker-group
```

[Registry Definition v1.0 JSON schema](/schemas/regdef.schema.json)

#### Registry Definition v2.0

```yaml
# Mandatory
# Registry Definition object version
version: "2.0"
# Mandatory
# Name of the registry
name: string
# Optional
# Authentication configs
authConfig:
  <auth-config-name>:
    # Mandatory
    # Name of the credential in the credential storage
    # The credential type can be either `usernamePassword` or `secret`
    # Depending on `authType`, it can be:
    # access key (username) + secret (password) for longLived
    # or different authentication credential components for shortLived
    credentialsId: string 
    # Optional
    # Public cloud registry authentication strategy
    # Used in case of public cloud registries
    authType: enum [ shortLived, longLived ]
    # Optional
    # Public cloud registry type
    # Used in case of public cloud registries
    provider: enum [ aws, azure, gcp ]
    # Optional
    # In case of non-cloud public registries, `user_pass` is used
    # In case of public cloud registries valid values, depends on `provider`:
    # `aws`: `secret` or `assume_role`
    # `gcp`: `federation` or `service_account`
    # `azure`: `oauth2`
    authMethod: enum [ secret, assume_role, federation, service_account, oauth2, user_pass ]
    # Optional
    # Region of the AWS cloud
    # Used with `provider: aws` only
    awsRegion: string
    # Optional
    # Domain of the AWS cloud
    # Used with `provider: aws` only
    # Required for CodeArtifact
    awsDomain: string
    # Optional
    # Amazon Resource Name (ARN) of the role to assume
    # Used with `provider: aws` AND `authMethod: assume_role` only
    awsRoleARN: string
    # Optional
    # Constant session name part to be used to generate --role-session-name parameter for AssumeRole
    # Used with `provider: aws` AND `authMethod: assume_role` only
    awsRoleSessionPrefix: string
    # Optional
    # Section, that describes OIDC interaction
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpOIDC:
      # Mandatory
      # URL of external OIDC server
      URL: string
      # Optional
      # Custom parameters for external OIDC server
      customParams:
        - <key>: <value>
        - <keyN>: <valueN>
    # Optional
    # GCP project number
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegProject: string
    # Optional
    # Workload identity pool ID
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegPoolId: string
    # Optional
    # Workload identity Provider ID
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegProviderId: string
    # Optional
    # Service account email
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegSAEmail: string
    # Optional
    # Azure AD tenant ID
    # Used with `provider: azure` only
    azureTenantId: string
    # Optional
    # Target resource for ACR
    # Used with `provider: azure` only
    azureACRResource: string
    # Optional
    # Azure Container Registry name
    # Used with `provider: azure` only
    # Required for ACR
    azureACRName: string
    # Optional
    # Target resource for Azure Artifacts
    # Used with `provider: azure` only
    azureArtifactsResource: string
# Mandatory
mavenConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # Snapshot Maven repository name
  targetSnapshot: string
  # Mandatory
  # Staging Maven repository name
  targetStaging: string
  # Mandatory
  # Release Maven repository name
  targetRelease: string
  # Mandatory
  # Snapshot Maven repository name
  snapshotGroup: string
  # Mandatory
  # Release Maven repository name
  releaseGroup: string
# Mandatory
dockerConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # URI for Docker snapshot registry
  snapshotUri: string
  # Mandatory
  # URI for Docker staging repository
  stagingUri: string
  # Mandatory
  # URI for Docker release repository
  releaseUri: string
  # Mandatory
  # URI for Docker group repository
  groupUri: string
  # Mandatory
  # Name of Docker snapshot repository
  snapshotRepoName: string
  # Mandatory
  # Name of Docker staging repository
  stagingRepoName: string
  # Mandatory
  # Name of Docker release repository
  releaseRepoName: string
  # Mandatory
  # Name of Docker group
  groupName: string
# Optional
helmConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # Helm staging repository name
  helmTargetStaging: string
  # Mandatory
  # Helm release repository name
  helmTargetRelease: string
# Optional
helmAppConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # Helm staging repository name for application charts
  helmStagingRepoName: string
  # Mandatory
  # Helm release repository name for application charts
  helmReleaseRepoName: string
  # Mandatory
  # Helm group repository name for application charts
  helmGroupRepoName: string
  # Mandatory
  # Helm dev repository name for application charts
  helmDevRepoName: string
# Optional
goConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  goTargetSnapshot: string
  # Mandatory
  # Go release repository name
  goTargetRelease: string
  # Mandatory
  # Go proxy repository URL
  goProxyRepository: string
# Optional
npmConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # npm snapshot repository name
  npmTargetSnapshot: string
  # Mandatory
  # npm release repository name
  npmTargetRelease: string
# Optional
rawConfig:
  # Optional
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  authConfig: string
  # Mandatory
  # Domain name of the registry
  repositoryDomainName: string
  # Mandatory
  # Pointer to authentication config described in `authConfig` section
  # Cannot be set in if anonymous access is used
  rawTargetSnapshot: string
  # Mandatory
  # Raw release repository name
  rawTargetRelease: string
  # Mandatory
  # Raw staging repository name
  rawTargetStaging: string
  # Mandatory
  # Raw proxy repository name
  rawTargetProxy: string
```

**Examples of different auth sections**:

```yaml
authConfig:
  maven-aws-secret:
    authType: longLived
    provider: aws
    authMethod: secret
    credentialsId: aws-key-secret
    awsRegion: aws-region
    awsDomain: codeartifact-domain

  maven-aws-assume-role:
    authType: shortLived
    provider: aws
    authMethod: assume_role
    credentialsId: aws-key-secret
    awsRoleARN: arn:aws:iam::123456789012:role/YourRole
    awsRegion: aws-region
    awsDomain: codeartifact-domain
    awsRoleSessionPrefix: devops-custom-session-prefix

  maven-gcp-federation:
    authType: shortLived
    provider: gcp
    authMethod: federation
    credentialsId: oidc-token
    gcpOIDC:
      URL: https://external-oidc-server-url
      customParams:
        - key1: value1
        - key2: value2
    gcpRegProject: 123456789012
    gcpRegPoolId: idp-pool-id
    gcpRegProviderId: idp-provider
    gcpRegSAEmail: test@test.iam.gserviceaccount.com

  maven-gcp-sa:
    authType: shortLived
    provider: gcp
    authMethod: service_account
    credentialsId: sa-json

  maven-azure-oauth2:
    authType: shortLived
    provider: azure
    authMethod: oauth2
    credentialsId: azure-ad
    azureTenantId: tenant-id
    azureACRResource: management
    azureACRName: acr-name
    azureArtifactsResource: 499b84ac-1321-427f-aa17-267ca6975798

  helm-nexus:
    authType: longLived
    authMethod: user_pass
    credentialsId: cred-nexus
```

**Example:**

```yaml
version: "2.0"
name: registry
authConfig:
  aws:
    authType: shortLived
    provider: aws
    authMethod: assume_role
    credentialsId: role-aws
    awsRegion: eu-west-1
    awsDomain: codeartifact.eu-west-1.amazonaws.com
    awsRoleARN: arn:aws:iam::123456789012:role/YourRole
  helm:
    authType: longLived
    authMethod: user_pass
    credentialsId: cred-nexus
mavenConfig:
  authConfig: aws
  repositoryDomainName: https://codeartifact.eu-west-1.amazonaws.com/maven/app
  targetSnapshot: snapshots
  targetStaging: staging
  targetRelease: releases
  snapshotGroup: snapshot-group
  releaseGroup: staging-group
dockerConfig:
  authConfig: aws
  snapshotUri: 123456789.dkr.ecr.eu-west-1.amazonaws.com:18080
  stagingUri: 123456789.dkr.ecr.eu-west-1.amazonaws.com:18081
  releaseUri: 123456789.dkr.ecr.eu-west-1.amazonaws.com:18082
  groupUri: 123456789.dkr.ecr.eu-west-1.amazonaws.com:18083
  snapshotRepoName: docker-snapshots
  stagingRepoName: docker-staging
  releaseRepoName: docker-releases
  groupName: docker
helmConfig:
  authConfig: helm
  repositoryDomainName: https://nexus.mycompany.internal/repository/helm-charts
  helmTargetStaging: helm-staging
  helmTargetRelease: helm-releases
helmAppConfig:
  authConfig: helm
  repositoryDomainName: https://nexus.mycompany.internal/repository/helm-charts
  helmDevRepoName: helm-dev
  helmStagingRepoName: helm-staging
  helmReleaseRepoName: helm-releases
  helmGroupRepoName: helm-group
goConfig:
  repositoryDomainName: https://nexus.mycompany.internal/repository/go
  goTargetSnapshot: go-snapshots
  goTargetRelease: go-releases
  goProxyRepository: https://goproxy.internal/go/
npmConfig:
  repositoryDomainName: https://mycompany.internal
  npmTargetSnapshot: npm-snapshots
  npmTargetRelease: npm-releases
rawConfig:
  repositoryDomainName: https://proxy.raw.local/raw
  rawTargetSnapshot: raw/snapshots
  rawTargetRelease: raw/releases
  rawTargetStaging: raw/staging
  rawTargetProxy: https://proxy.raw.local/
```

[Registry Definition v2.0 JSON schema](/schemas/regdef-v2.schema.json)

### Application Definition

This object describes application artifact parameters - artifact ID, group ID and pointer to [Registry Definition](#registry-definition)

It is used by **external systems** to convert the `application:version` format of an artifact template into the registry and Maven artifact parameters required to download it.

A separate definition file is used for each individual application. Each Environment uses its own set of Application Definitions.

The filename must match the value of the `name` attribute.

**Location:** `/environments/<cluster-name>/<environment-name>/AppDefs/<application-name>.yml`

```yaml
# Mandatory
# Name of the artifact application. This corresponds to the `application` part in the `application:version` notation.
name: string
# Mandatory
# Reference to Registry Definition
registryName: string
# Mandatory
# Application artifact ID
artifactId: string
# Mandatory
# Application group ID
groupId: string
```

**Example:**

```yaml
name: qip
registryName: sandbox
artifactId: qip
groupId: org.qubership
```

[Application Definition JSON schema](/schemas/appdef.schema.json)

## Discovery Repository Objects

### Cloud Passport Template

TBD
