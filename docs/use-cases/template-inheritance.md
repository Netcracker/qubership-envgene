# Template Inheritance (Template Composition) Use Cases

- [Template Inheritance (Template Composition) Use Cases](#template-inheritance-template-composition-use-cases)
  - [Overview](#overview)
  - [Parent Templates Download and Selection](#parent-templates-download-and-selection)
    - [UC-TI-PT-1: Build child template using a single parent template](#uc-ti-pt-1-build-child-template-using-a-single-parent-template)
    - [UC-TI-PT-2: Build child template composed from multiple parent templates](#uc-ti-pt-2-build-child-template-composed-from-multiple-parent-templates)
  - [Composite Structure Selection](#composite-structure-selection)
    - [UC-TI-CS-1: Use explicit `composite_structure` from child Template Descriptor](#uc-ti-cs-1-use-explicit-composite_structure-from-child-template-descriptor)
  - [Overrides in Child Template](#overrides-in-child-template)
    - [UC-TI-OV-1: Override parent parameters for Cloud template](#uc-ti-ov-1-override-parent-parameters-for-cloud-template)
    - [UC-TI-OV-2: Override parent parameters for Namespace template](#uc-ti-ov-2-override-parent-parameters-for-namespace-template)

## Overview

This document describes use cases for [Template Inheritance](/docs/features/template-inheritance.md) - composing a child Environment Template from parent templates and optionally overriding selected parameters in child descriptor.

## Parent Templates Download and Selection

This section covers how `parent-templates` and `parent` references are resolved during child template build.

### UC-TI-PT-1: Build child template using a single parent template

**Pre-requisites:**

1. A child Template Repository exists and is configured to build an Environment Template artifact.
2. The child repository contains a Template Descriptor with a single parent template reference:

   ```yaml
   parent-templates:
     basic-cloud: basic-product-template:10.1.3
   tenant:
     parent: basic-cloud
   cloud:
     parent: basic-cloud
   namespaces:
     - name: "{env}-billing"
       parent: basic-cloud
   ```

**Trigger:**

Template repository pipeline is started to build the child template artifact.

**Steps:**

1. The build pipeline starts Template Inheritance processing.
2. The pipeline resolves `tenant.parent`, `cloud.parent`, and `namespaces[].parent` using alias `basic-cloud` from `parent-templates`.
3. The pipeline publishes a regular EnvGene child template artifact.

**Results:**

1. Child template artifact is created successfully.
2. Inherited components are taken from `basic-cloud` according to descriptor references.
дОБАВИТЬ ЧТО РОДИТЕЛЬСКИЕ ШАБЛОНЫ БУДЕТ В РЕПОЗИТОРИИ, БЕЗ ССЫЛОК НА АРТИФАКТ 



### UC-TI-PT-2: Build child template composed from multiple parent templates

**Pre-requisites:**

1. Child Template Repository contains a Template Descriptor that references multiple parent templates and composes namespaces from them:

   ```yaml
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

2. All referenced parent template artifacts are available and accessible to the pipeline.

**Trigger:**

Template repository pipeline is started to build the child template artifact.

**Steps:**

1. The build pipeline starts Template Inheritance processing.
2. The pipeline resolves `tenant.parent` and each `namespaces[].parent` by alias from `parent-templates`.
3. `cloud` and `composite_structure` are taken from child template paths defined in descriptor.
4. The pipeline publishes a regular EnvGene child template artifact.

**Results:**

1. Child template artifact is created successfully.
2. Tenant and namespaces are composed from referenced parent templates.
3. Cloud and composite structure are taken from child repository sources.

## Composite Structure Selection

This section covers how explicit `composite_structure` path is selected and used.

### UC-TI-CS-1: Use explicit `composite_structure` from child Template Descriptor

**Pre-requisites:**

1. Child Template Descriptor specifies `composite_structure` explicitly:

   ```yaml
   composite_structure: "{{ templates_dir }}/env_templates/composite/composite_structure.yml.j2"
   ```

2. The referenced file exists in the child repository template sources.

**Trigger:**

Template repository pipeline is started to build the child template artifact.

**Steps:**

1. The build pipeline reads `composite_structure` path from child descriptor.
2. The path value is saved in built template artifact and later used during instance generation to render `composite_structure.yml`.

**Results:**

1. Built artifact contains the explicit child `composite_structure` reference.
2. QA can verify generated instance contains `composite_structure.yml` rendered from that path.

## Overrides in Child Template

This section covers `overrides-parent` for Cloud and Namespace templates.

### UC-TI-OV-1: Override parent parameters for Cloud template

**Pre-requisites:**

1. Child Template Descriptor defines `cloud.parent` and includes `cloud.overrides-parent` section:

   ```yaml
   cloud:
     parent: basic-template
     overrides-parent:
       deployParameters:
         DEPLOY_PARAM1: "DEPLOY_PARAM1_VALUE"
       e2eParameters:
         E2E_PARAM1: "E2E_PARAM1_VALUE"
   ```

2. The parent template `basic-template` exists and contains a Cloud template.

**Trigger:**

Template repository pipeline is started to build the child template artifact.

**Steps:**

1. The pipeline loads Cloud template from parent `basic-template`.
2. The pipeline applies `cloud.overrides-parent` over inherited Cloud values.
3. The pipeline publishes a child artifact with merged Cloud template.

**Results:**

1. Child Cloud template is inherited from parent and overridden by child `cloud.overrides-parent`.
2. QA can verify only supported override sections are used (`profile`, parameter maps, parameter sets).

### UC-TI-OV-2: Override parent parameters for Namespace template

**Pre-requisites:**

1. Child Template Descriptor defines a namespace with `parent` and includes `overrides-parent` section:

   ```yaml
   namespaces:
     - name: "{env}-bss"
       parent: default-bss
       overrides-parent:
         technicalConfigurationParameters:
           TECH_CONF_PARAM1: "TECH_CONF_PARAM1_VALUE"
         deployParameterSets:
           - "bss-overrides"
   ```

2. The parent template `default-bss` exists and contains the referenced namespace template.

**Trigger:**

Template repository pipeline is started to build the child template artifact.

**Steps:**

1. The pipeline loads Namespace template from parent `default-bss`.
2. The pipeline applies `namespaces[].overrides-parent` over inherited Namespace values.
3. The pipeline publishes a child artifact with merged Namespace template.

**Results:**

1. Child namespace template is inherited from parent and overridden by `namespaces[].overrides-parent`.
2. QA can verify overridden parameter maps and parameter sets are present in produced template.
