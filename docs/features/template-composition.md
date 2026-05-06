# Template Composition

- [Template Composition](#template-composition)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Key Capabilities](#key-capabilities)
    - [Detailed Composition Algorithm](#detailed-composition-algorithm)
    - [Nested Application and Registry Definitions (appdefs / regdefs)](#nested-application-and-registry-definitions-appdefs--regdefs)
      - [Examples (app-reg-defs)](#examples-app-reg-defs)
    - [Use Cases](#use-cases)
      - [Case 1](#case-1)
      - [Case 2](#case-2)
    - [Template Composition Configuration](#template-composition-configuration)
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

Introduce **Template Composition** - a feature that enables the creation of child templates by composing some or all components from one or more parent templates. Supported components include:

- Tenant template
- Cloud template
- Namespace template

This diagram shows parent and child templates with their components. The color of component indicates its source:

template-composition-1.png

### Key Capabilities

1. **Selective Composition**:
  - Compose some or all components from parents
  - Optionally override specific parameters of inherited components
  - Define new components in child template
2. **Component Composition Rules**:
  - **Composable Components**:
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
3. **Composition Processing**:
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
  - Supports multi-level composition chains
5. **Application & Registry Definitions composition**:
  - `appdefs` and `regdefs` live under `templates/` like other resources. Template composition does not merge YAML across files: if the same path appears in more than one source, the file from the later source in copy order replaces the earlier file entirely.
  - See [Nested Application and Registry Definitions (appdefs / regdefs)](#nested-application-and-registry-definitions-appdefs--regdefs) below for precedence and how this differs from field-level merge.

### Detailed Composition Algorithm

The sequence below describes how composition is executed during template build.

1. **Discover descriptors**
  Read all `*.yml|*.yaml` files from `templates/env_templates` (top-level only, non-recursive).
   Each discovered file is processed as an independent child Template Descriptor.
2. **Check whether composition is needed**
  If a descriptor does not contain `parent-templates`, composition is skipped for that descriptor.
3. **Validate parent references**
  - `parent-templates` cannot be empty when declared.
  - If multiple parents are declared, each inheriting namespace must explicitly set `parent`.
4. **Resolve parent artifacts**
  - For each `app:version` in `parent-templates`, find matching Artifact Definition in `configuration/artifact_definitions`.
  - Download and unpack the parent template artifact into temporary storage.
5. **Prepare resource files (`templates/`*)**
  Copy resources in this order:
  - `templates/`* from parents referenced by `namespaces[].parent`
  - `templates/`* from `tenant.parent` (if used)
  - `templates/*` from `cloud.parent` (if used)
  - child `templates/*` (always last)
    > [!IMPORTANT]
    > The `templates/*` step is file-based and recursive. It includes all files and directories under `templates/`, including:
    >
    > - `env_templates`
    > - `resource_profiles`
    > - `parameters`
    > - `appdefs`
    > - `regdefs`
    >
    > If the same relative path exists in multiple sources, the later copy overwrites the earlier one.
6. **Build resulting Template Descriptor**
  - Create the resulting descriptor as a copy of the child descriptor, then remove `parent-templates` from that resulting descriptor.
  - If `tenant: { parent: <parent-key> }` is used, replace child `tenant` with the `tenant` value from the parent template descriptor referenced by `<parent-key>`.
  - If `cloud: { parent: <parent-key> }` is used, replace child `cloud` with the `cloud` value from the parent template descriptor referenced by `<parent-key>`.
  - If top-level `tenant`, `cloud` or `composite_structure` are missing in child, they are inherited from the first matching parent in namespace iteration order (`first parent wins`) and are not overwritten later.
7. **Process namespaces**
  - For each namespace with `parent`, find the parent namespace by exact `name` and use it as the base namespace entry in the resulting descriptor.
  - Then, if the child namespace defines `template_path`, overwrite the inherited `template_path` with the child value.
8. **Apply `overrides-parent` (Cloud and Namespace only)**
  - Parameter maps (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`) are merged into `template_override`.
  - Parameter set lists (`deployParameterSets`, `e2eParameterSets`, `technicalConfigurationParameterSets`) are appended into `template_override`.
  - `profile` override has two modes:
    - default mode (`merge-with-parent` is false or not set): use the override profile as the resulting profile reference;
    - merge mode (`merge-with-parent: true`): merge override profile content into the selected parent profile and use the merged result.
  - `tenant` does not support `overrides-parent` in template composition (inherit-only behavior).
9. **Persist output**
  - Save composed descriptor to output `env_templates`.
  - Save generated/merged resource profiles to output `resource_profiles`.
10. **Resulting artifact**
  The output is a regular EnvGene template artifact and does not require special runtime handling.

> [!IMPORTANT]
> File precedence is copy-order based. If the same file path exists in multiple sources, the last copied file wins.
> Effective precedence is:
> **namespace parents** - **tenant parent** - **cloud parent** - **child template files**.

### Nested Application and Registry Definitions (appdefs / regdefs)

Application Definitions (`appdefs`) and Registry Definitions (`regdefs`) can be shipped in parent templates, child templates, or both. Bringing them together during template composition is file-based, not a content merge: overlapping paths are resolved by replacement (last copy wins).

- **Different relative paths** (for example parent `.../billing-app.yml` and child `.../oss-app.yml`) all remain in the composed artifact; each file is kept as authored.
- **Same relative path** in more than one source (for example parent and child both ship `templates/appdefs/my-app.yml`): the whole file from the winning source replaces the other. There is **no** field-by-field merge of two YAML documents into one definition. To customize a parent's app or registry file in the child, provide the complete desired file at that path in a source that copies after the parent.
- Copy order matches template composition precedence: **namespace parents** → **tenant parent** → **cloud parent** → **child template files**. The last source in that order for a given path is what ends up in the built template artifact.

> [!NOTE]
> After composition, the instance pipeline still runs `app_reg_def_process` on the resulting definition files.
> That pipeline behavior is documented in [app-reg-defs](/docs/features/app-reg-defs.md).
> It does not reintroduce a cross-parent merge for two files that shared the same path.

#### Examples (app-reg-defs)

1. Parent ships `templates/appdefs/my-app.yml` and the child adds `templates/appdefs/my-app.yml` with the same relative path. The child's file replaces the parent's. If you only need a small change, duplicate the parent content into the child file and edit the full document there - partial overlays are not applied automatically.
2. Parent defines one application in `templates/appdefs/app-a.yml` and the child adds `templates/appdefs/app-b.yml`. Both paths are distinct, so both files appear in the composed template.

### Use Cases

This feature can be used in scenarios where EnvGene manages configuration parameters for complex solutions consisting of multiple applications or application groups, with parameters developed and tested by different teams.

#### Case 1

A solution comprises multiple applications, where application's teams develop and provide their respective templates. The team responsible for the overall solution collects these templates, combines them into a product-level template, and adds necessary customizations.

template-composition-2.png

#### Case 2

A solution consists of application groups (domains). Domain teams develop and provide their templates. The product team aggregates these into a product-level template, adding for example integration parameters. Then, a project team customizes this product template for specific project needs. Here, the product template acts as both a parent and child template.

template-composition-3.png

### Template Composition Configuration

Template composition is configured in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor) in the child template repository. Below is a description of such a Template Descriptor

#### Template Descriptor

```yaml
---
# Optional
# If not set than no Template Composition is assumed
parent-templates:
  # Key is a parent template name
  # Value is a parent template artifact in app:ver notation. SNAPSHOT version is not supported
  default-bss: bss-product-template:2.0.0
  basic-template: basic-product-template:10.1.3
# Optional
# If not set, inherit from the first matching parent encountered during namespace processing (`first parent wins`)
composite_structure: "{{ templates_dir }}/env_templates/composite/composite_structure.yml.j2"
# Optional
# If not set, inherit from the first matching parent encountered during namespace processing (`first parent wins`)
# It can be string or dict, if string is provide that means that no composition is needed and the exact template will be used
# example of string value
tenant: "{{ templates_dir }}/env_templates/default/tenant.yml.j2"
# example of dict value
tenant:
  parent: basic-template
# Optional
# If not set, inherit from the first matching parent encountered during namespace processing (`first parent wins`)
# It can be string or dict, if string is provide that means that no composition is needed and the exact template will be used
# example of string value
cloud: "{{ templates_dir }}/env_templates/default/cloud.yml.j2"
# example of dict value
cloud:
  parent: basic-template
  # Optional
  # Section with parameters that should override parent
  overrides-parent:
    # Optional
    # Override the name of the cloud in rendering result
    name: "override-cloud"
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
      # This mode does not support merging of Jinja template based resource profiles.
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
      # Override the name of the namespace in rendering result
      name: "override-ns"
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

