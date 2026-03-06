# How to filter namespaces in an Environment Template

## Overview

This guide explains how to generate an Environment that includes only a selected subset of namespaces from a unified Environment Template.

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
  namespace-key — key in ns_list used to enable or disable the namespace
  template_path — path to the Namespace Template file
  deploy_postfix — folder name in Instance Repository (/Namespaces/<deploy_postfix>/)

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

## Step 3. Create ns_list.yaml

Create the following file:

```yaml
# /environments/shared-template-variables/ns-list.yaml

ns_list:
  <namespace-name>: <boolean>
  <another-namespace-name>: <boolean>
```

### Example ns_list.yaml

```yaml
# /environments/shared-template-variables/ns-list.yaml

ns_list:
  platform-monitoring: true
  postgresql: true
  postgresql-dbaas: true
  kafka: false
```

Set true for namespaces that must be generated.

## Step 4. Reference ns_list in env_definition.yml

Add the shared template variable:

```yaml
envTemplate:
  sharedTemplateVariables:
    - ns_list
```

This makes the ns_list variable available during Template Descriptor rendering.

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
