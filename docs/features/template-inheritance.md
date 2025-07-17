# Template Inheritance

- [Template Inheritance](#template-inheritance)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Key Capabilities](#key-capabilities)
    - [Use Cases](#use-cases)
      - [Case 1](#case-1)
      - [Case 2](#case-2)
    - [Template Inheritance Configuration](#template-inheritance-configuration)
      - [Template Descriptor](#template-descriptor)
        - [Examples](#examples)
          - [Child Template Descriptor for One Namespace](#child-template-descriptor-for-one-namespace)
          - [Child Template Descriptor with Composite Structure and Several Namespaces](#child-template-descriptor-with-composite-structure-and-several-namespaces)

## Problem Statement

Managing configurations for complex solutions presents several challenges:

**Cross-Team Dependencies**: When multiple teams own configuration of different components:

- No standardized way to share configurations
- Changes require manual coordination across teams

**Configuration Duplication**: Teams repeatedly copy or re-invent similar configuration across projects, leading to:

- Maintenance overhead when updating common parameters
- Configuration drift as copies evolve independently

This creates inefficiencies in configuration management, increases error potential, and makes configuration updates across multiple templates difficult.

## Proposed Approach

Introduce **Template Inheritance** - a feature that enables the creation of child templates by inheriting some or all components from one or more parent templates. Supported inheritable components include:

- Tenant template
- Cloud template
- Namespace template

This diagram shows parent and child templates with their components. The color of component indicates its source:

![template-inheritance-1.png](./images/template-inheritance-1.png)

### Key Capabilities

1. **Selective Inheritance**:
   - Inherit some or all components from parents
   - Optionally override specific parameters of inherited components
   - Define new components in child template

2. **Component Inheritance Rules**:
   - **Inheritable Components**:
     - Tenant template (cannot be overridden)
     - Cloud template (override allowed)
     - Namespace template (override allowed)
   - **Overrideable Attributes** (for Cloud/Namespace templates only):
     - `profile`
     - `deployParameters`
     - `e2eParameters`
     - `technicalConfigurationParameters`
     - `deployParameterSets`
     - `e2eParameterSets`
     - `technicalConfigurationParameterSets`

3. **Inheritance Processing**:
   - Occurs during child template build in template repository pipeline
   - Process flow:
     1. Download parent template artifacts specified in `parent-templates` section
     2. For each child component:
        - Incorporate component from parent template if `parent` attribute specified
        - Apply any parameter overrides if `overrides-parent` attribute specified
        - Incorporate child-specific components (if `parent` attribute not specified)
     3. Generate final child template artifact with processed components

4. **Key Characteristics**:
   - Built child templates are regular EnvGene artifacts requiring no special handling
   - Parent templates are regular EnvGene templates needing no special configuration
   - Supports multi-level inheritance chains

### Use Cases

This feature can be used in scenarios where EnvGene manages configuration parameters for complex solutions consisting of multiple applications or application groups, with parameters developed and tested by different teams.

#### Case 1

A solution comprises multiple applications, where application's teams develop and provide their respective templates. The team responsible for the overall solution collects these templates, combines them into a product-level template, and adds necessary customizations.

![template-inheritance-2.png](./images/template-inheritance-2.png)

#### Case 2

A solution consists of application groups (domains). Domain teams develop and provide their templates. The product team aggregates these into a product-level template, adding for example integration parameters. Then, a project team customizes this product template for specific project needs. Here, the product template acts as both a parent and child template.

![template-inheritance-3.png](./images/template-inheritance-3.png)

### Template Inheritance Configuration

Template inheritance is configured in the [Template Descriptor](./envgene-objects.md#template-descriptor) in the child template repository. Below is a description of such a Template Descriptor

#### Template Descriptor

```yaml
---
# Optional
# If not set than no Templates Inheritance is assumed
parent-templates:
  # Кey is a parent template name
  # Value is a parent template artifact is a in app:ver notation. SNAPSHOT version is not supported 
  default-bss: bss-product-template:2.0.0
  basic-template: basic-product-template:10.1.3
# Optional
# If not set, the most recent Composite Structure found in the parent templates referenced by the `namespaces` attribute will be used
composite_structure: "{{ templates_dir }}/env_templates/composite/composite_structure.yml.j2"
# Optional
# If not set, the most recent Tenant found in the parent templates referenced by the `namespaces` attribute will be used
# It can be string or dict, if string is provide that means that no inheritance is needed and the exact template will be used
# example of string value
tenant: "{{ templates_dir }}/env_templates/default/tenant.yml.j2"
# example of dict value
tenant: 
  parent: basic-template
# Optional
# If not set, the most recent Cloud found in the parent templates referenced by the `namespaces` attribute will be used
# It can be string or dict, if string is provide that means that no inheritance is needed and the exact template will be used
# example of string value
cloud: "{{ templates_dir }}/env_templates/default/cloud.yml.j2"
# example of dict value
cloud: 
  parent: basic-template
  # Optional
  # Section with parameters that should override parent 
  overrides-parent:
    # Optional
    # Section to override resource profile
    profile:
      # Optional
      # The name of profile that will be used to override, file with this profile should be in current template repo
      override-profile-name: project_bss_override
      # Optional
      # If merge-with-parent is false or not specified, the name of profile from parent template to override
      parent-profile-name: default_bss_override
      # Optional
      # Baseline profile name to override
      baseline-profile-name: dev
      # Optional. Default value is `false`
      # Whether to merge parameters from override-profile-name to parent-profile-name
      merge-with-parent: true
    # Optional
    # Parameters that extend/override the parent template's values
    deployParameters:
      DEPLOY_PARAM1: "DEPLOY_PARAM1_VALUE"
    # Optional
    # Parameters that extend/override the parent template's values
    e2eParameters:
      E2E_PARAM1: "E2E_PARAM1_VALUE"
    # Optional
    # Parameters that extend/override the parent template's values
    technicalConfigurationParameters:
      TECH_CONF_PARAM1: "TECH_CONF_PARAM1_VALUE"
    # Optional
    # Parameters that extend/override the parent template's values
    deployParameterSets:
      - "bss-overrides"
    # Optional
    # Parameters that extend/override the parent template's values
    e2eParameterSets: 
      - "bss-e2e-overrides"
    # Optional
    # Parameters that extend/override the parent template's values
    technicalConfigurationParameterSets:
      - "bss-runtime-overrides"
namespaces:
  # Name of the namespace template in parent template. Here should be exact alignment with the name of namespace template in parent template
  - name: "{env}-bss"
    # Optional
    # Required when multiple `parent-templates` exist or template_path is specified and you want to override
    parent: default-bss
    # Optional
    # Section with parameters that override the parent template's values
    overrides-parent:
      # Optional
      # Section to override resource profile
      profile:
        # Optional
        # The name of profile that will be used to override. File with this profile should be in current template repo
        override-profile-name: project_bss_override
        # Optional
        # If merge-with-parent is false or not specified. The name of profile from parent template to override
        parent-profile-name: default_bss_override
        # Optional
        # Baseline profile name to override
        baseline-profile-name: dev
        # Optional. Default value is `false`
        # Whether to merge parameters from override-profile-name to parent-profile-name
        merge-with-parent: true
      # Optional
      # Parameters that extend/override the parent template's values
      deployParameters:
        DEPLOY_PARAM1: "DEPLOY_PARAM1_VALUE"
      # Optional
      # Parameters that extend/override the parent template's values
      e2eParameters:
        E2E_PARAM1: "E2E_PARAM1_VALUE"
      # Optional
      # Parameters that extend/override the parent template's values
      technicalConfigurationParameters:
        TECH_CONF_PARAM1: "TECH_CONF_PARAM1_VALUE"
      # Optional
      # Parameter Sets that extend/override the parent template's values
      deployParameterSets:
        - "bss-overrides"
      # Optional
      # Parameters Sets that extend/override the parent template's values
      e2eParameterSets: 
        - "bss-e2e-overrides"
      # Optional
      # Parameters Sets that extend/override the parent template's values
      technicalConfigurationParameterSets:
        - "bss-runtime-overrides"
```

##### Examples

###### Child Template Descriptor for One Namespace

```yaml
---
parent-templates:
  basic-cloud: basic-product-template:10.1.3
tenant: 
  parent: basic-cloud
cloud:
  parent: basic-cloud
namespaces:
  - name: "{env}-billing"
    template_path: "{{ templates_dir }}/env_templates/default/Namespaces/billing.yml.j2"
```

###### Child Template Descriptor with Composite Structure and Several Namespaces

```yml
---
parent-templates:
  basic-cloud: basic-product-template:10.1.3
  default-oss: core-product-templates:1.5.3
  default-billing: billing-product-templates:3.7.12
  default-bss: bss-product-templates:2.0.0
tenant: 
  parent: basic-cloud
cloud: "{{ templates_dir }}/env_templates/composite/cloud.yml.j2"
composite_structure: "{{ templates_dir }}/env_templates/composite/composite_structure.yml.j2"
namespaces:
  - name: "{env}-oss"
    parent: default-oss
  - name: "{env}-billing"
    parent: default-billing
  - name: "{env}-bss"
    parent: default-bss
```
