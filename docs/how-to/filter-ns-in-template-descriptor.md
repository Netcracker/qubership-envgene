# How to filter namespaces in an Environment Template

- [How to filter namespaces in an Environment Template](#how-to-filter-namespaces-in-an-environment-template)
  - [Overview](#overview)
  - [Step 1. Convert Template Descriptor to a Jinja Template](#step-1-convert-template-descriptor-to-a-jinja-template)
  - [Step 2. Wrap namespaces in Jinja conditions](#step-2-wrap-namespaces-in-jinja-conditions)
    - [Generic pattern](#generic-pattern)
    - [Example](#example)
  - [Step 3. Create the namespace list file](#step-3-create-the-namespace-list-file)
    - [Example ns-list.yaml](#example-ns-listyaml)
  - [Step 4. Reference the file in env\_definition.yml](#step-4-reference-the-file-in-env_definitionyml)
  - [Step 5. Run Environment Instance generation](#step-5-run-environment-instance-generation)
  - [Step 6. Verify the result](#step-6-verify-the-result)
  - [See also](#see-also)

## Overview

This guide explains how to generate an Environment that includes only a selected subset of namespaces from a unified Environment Template. It follows the feature described in [Namespace Filtering in Template Descriptor](/docs/features/namespace-filtering-in-template-descriptor.md).

Use this approach if:

- You use a unified Environment Template with multiple namespaces
- You need to include or exclude namespaces depending on specific environment need

---

## Step 1. Convert Template Descriptor to a Jinja Template

Find the Template Descriptor file:

`/templates/env_templates/<env-template-name>.yaml`

Rename it to one of the following:

- `<env-template-name>.yaml.j2`
or  
- `<env-template-name>.yml.j2`

After renaming, EnvGene will treat the Template Descriptor as a Jinja template and render it before Environment generation.

---

## Step 2. Wrap namespaces in Jinja conditions

Each namespace can be conditionally included using a Jinja `if` expression.

### Generic pattern

```jinja
namespaces:
{% if current_env.additionalTemplateVariables.ns_list.get('namespace-key', false) %}
  - template_path: {{ templates_dir }}/env_templates/Namespaces/<namespace-template-file>.yml.j2
    deploy_postfix: <deploy-postfix>
{% endif %}
```

**Parameters**:

- namespace-key - key in `ns_list` used to enable or disable the namespace
- template_path - path to the Namespace Template file
- deploy_postfix - folder name in Instance Repository (`/Namespaces/<deploy_postfix>/`)

### Example

```jinja
namespaces:
{% if current_env.additionalTemplateVariables.ns_list.get('postgresql', false) %}
  - template_path: {{ templates_dir }}/env_templates/Namespaces/postgresql.yml.j2
    deploy_postfix: postgresql
{% endif %}

{% if current_env.additionalTemplateVariables.ns_list.get('postgresql-dbaas', false) %}
  - template_path: {{ templates_dir }}/env_templates/Namespaces/postgresql-dbaas.yml.j2
    deploy_postfix: postgresql-dbaas
{% endif %}

{% if current_env.additionalTemplateVariables.ns_list.get('kafka', false) %}
  - template_path: {{ templates_dir }}/env_templates/Namespaces/kafka.yml.j2
    deploy_postfix: kafka
{% endif %}

{% if current_env.additionalTemplateVariables.ns_list.get('platform-monitoring', false) %}
  - template_path: {{ templates_dir }}/env_templates/Namespaces/platform-monitoring.yml.j2
    deploy_postfix: platform-monitoring
{% endif %}
```

If the key is missing or set to false, the namespace will not be generated.

---

## Step 3. Create the namespace list file

Create a YAML file that defines which namespaces are enabled. The file must be in a location where EnvGene resolves [shared template variable files](/docs/envgene-configs.md#env_definitionyml) (for example, under `/environments/` or per-cluster/per-environment, depending on your Instance Repository layout). The filename (without extension) is what you will reference in `env_definition.yml` in Step 4.

Example: if the file is named `ns-list.yaml`, use the name `ns-list` in `sharedTemplateVariables`.

```yaml
# Example path: /environments/shared-template-variables/ns-list.yaml
# The top-level key (ns_list) becomes available as current_env.additionalTemplateVariables.ns_list

ns_list:
  <namespace-name>: <boolean>
  <another-namespace-name>: <boolean>
```

### Example ns-list.yaml

```yaml
# /environments/shared-template-variables/ns-list.yaml

ns_list:
  platform-monitoring: true
  postgresql: true
  postgresql-dbaas: true
  kafka: false
```

Set `true` for namespaces that must be generated.

## Step 4. Reference the file in env_definition.yml

In the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) for the environment, add the shared template variable by **filename without extension** (e.g. `ns-list` for `ns-list.yaml`):

```yaml
envTemplate:
  sharedTemplateVariables:
    - ns-list
```

The content of the file is merged into `additionalTemplateVariables`, so `ns_list` from the YAML is available during Template Descriptor rendering as `current_env.additionalTemplateVariables.ns_list`.

## Step 5. Run Environment Instance generation

Run the Environment Instance generation process using the standard EnvGene pipeline.

During generation:

- The Template Descriptor is rendered  
- Jinja conditions are evaluated  
- Only enabled namespaces are included  

If a condition evaluates to `false`:

- The namespace folder is not created  
- The namespace object is not generated  

## Step 6. Verify the result

After generation, verify the directory: `/environments/<cluster>/<env-name>/Namespaces/`

Only namespaces that passed the Jinja conditions should be present.

---

## See also

- [Namespace Filtering in Template Descriptor](/docs/features/namespace-filtering-in-template-descriptor.md) - Feature overview, file resolution priority, and behavior when a condition is `false`
- [env_definition.yml](/docs/envgene-configs.md#env_definitionyml) - Environment Inventory and `sharedTemplateVariables`
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor) - Location and Jinja extensions
