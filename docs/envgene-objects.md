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
tenant: "<path-to-the-tenant-template-file>"
# Cloud configuration can be specified either as direct template path (string) 
# or as an object with template_path and optional overrides
cloud: "<path-to-the-cloud-template-file>"
# or
cloud:
  template_path: "<path-to-the-cloud-template-file>"
  # Optional
  # See details https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
  template_override:     
    "<yaml or jinja expression>"
composite_structure: "<path-to-the-composite-structure-template-file>"
namespaces:
  - template_path: "<path-to-the-namespace-template-file>"
    # Optional
    # See details https://github.com/Netcracker/qubership-envgene/blob/main/docs/template-override.md
    template_override:
      "<yaml or jinja expression>"
```

[Template Descriptor JSON schema](/schemas/template-descriptor.schema.json)

Any YAML file located in the `/templates/env_templates/` folder is considered a Template Descriptor.

The name of this file serves as the name of the Environment Template. In the Environment Inventory, this name is used to specify which Environment Template from the artifact should be used.

#### Tenant Template

TBD

#### Cloud Template

TBD

#### Namespace Template

TBD

#### ParameterSet

TBD

#### Resource Profile Override (in Template)

TBD

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

TBD

#### Cloud

TBD

#### Namespace

TBD

#### Application

TBD

#### Resource Profile Override (in Instance)

TBD

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

[Solution Descriptor JSON schema](/schemas/TBD)

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
