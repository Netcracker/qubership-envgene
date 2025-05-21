# EnvGene Objects

- [EnvGene Objects](#envgene-objects)
  - [Environment Template Objects](#environment-template-objects)
    - [Template Descriptor](#template-descriptor)
    - [Tenant Template](#tenant-template)
    - [Cloud Template](#cloud-template)
    - [Namespace Template](#namespace-template)
    - [ParameterSet](#parameterset)
    - [Resource Profile Override (in Template)](#resource-profile-override-in-template)
    - [Composite Structure Template](#composite-structure-template)
  - [Environment Instance Objects](#environment-instance-objects)
    - [Tenant](#tenant)
    - [Cloud](#cloud)
    - [Namespace](#namespace)
    - [Application](#application)
    - [Resource Profile Override (in Instance)](#resource-profile-override-in-instance)
    - [Composite Structure](#composite-structure)

## Environment Template Objects

An Environment Template is a file structure within the Envgene Template Repository that describes the structure of a solution — such as which namespaces are part of the solution, as well as environment-agnostic parameters, which are common to a specific type of solution.

The objects that make up the Environment Template extensively use the Jinja template engine. During the generation of an Environment Instance, Envgene renders these templates with environment-specific parameters, allowing a single template to be used for preparing configurations for similar but not entirely identical environment/solution instances.

The template repository can contain multiple Environment Templates describing configurations for different types of environments/solution instances, such as DEV, PROD, and SVT.

When a commit is made to the Template Repository, an artifact is built and published. This artifact contains all the Environment Templates located in the repository.

### Template Descriptor

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

### Tenant Template

TBD

### Cloud Template

TBD

### Namespace Template

TBD

### ParameterSet

TBD

### Resource Profile Override (in Template)

TBD

### Composite Structure Template

This is a Jinja template file used to render the [Composite Structure](#composite-structure) object.

Example:

```yaml
name: "{{ current_env.cloudNameWithCluster }}-composite-structure"
baseline:
  name: "{{ current_env.environmentName }}-core"
  type: "namespace"
satellites:
  - name: "{{ current_env.environmentName }}-bss"
    type: "namespace"
  - name: "{{ current_env.environmentName }}-oss"
    type: "namespace"
```

## Environment Instance Objects

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

### Tenant

TBD

### Cloud

TBD

### Namespace

TBD

### Application

TBD

### Resource Profile Override (in Instance)

TBD

### Composite Structure

This object describes the composite structure of a solution. It contains information about which namespace hosts the core applications that offer essential tools and services for business microservices (`baseline`), and which namespace contains the applications that consume these services (`satellites`). It has the following structure:

```yaml
name: <composite-structure-name>
# Envgene automatically adds `version`` attribute regardless of what is specified in the template
# Envgene always sets the value to 0
# If the attribute already exists in the template, it will be overwritten.
version: 0
# Envgene automatically adds `id`` attribute regardless of what is specified in the template
# Envgene sets this attribute's value to what is specified in `baseline.name`
# If the attribute already exists in the template, it will be overwritten
id: baseline.name
baseline:
  name: <baseline-namespace>
  type: "namespace"
satellites:
  - name: <satellite-namespace-1>
    type: "namespace"
  - name: <satellite-namespace-2>
    type: "namespace"
```

The Composite Structure is located in the path `/configuration/environments/<CLUSTER-NAME>/<ENV-NAME>/composite-structure.yml`

[Composite Structure JSON schema](/schemas/composite-structure.schema.json)

Example:

```yaml
name: "clusterA-env-1-composite-structure"
version: 0
id: "env-1-core"
baseline:
  name: "env-1-core"
  type: "namespace"
satellites:
  - name: "env-1-bss"
    type: "namespace"
  - name: "env-1-oss"
    type: "namespace"
```
