# How to Configure Different Namespace Names for Different Sites

- [How to Configure Different Namespace Names for Different Sites](#how-to-configure-different-namespace-names-for-different-sites)
  - [Why Different Namespace Names?](#why-different-namespace-names)
  - [Option 1: Namespace Name in the Template Descriptor Under the `namespaces` Block](#option-1-namespace-name-in-the-template-descriptor-under-the-namespaces-block)
  - [Option 2: Namespace Name Directly in Namespace object](#option-2-namespace-name-directly-in-namespace-object)
  - [Example Environment Inventory (`env_definition.yml`) for Both Options](#example-environment-inventory-env_definitionyml-for-both-options)
    - [Onsite Example](#onsite-example)
    - [Offsite Example](#offsite-example)
  - [How It Works](#how-it-works)

This guide explains how to set different [Namespace](/docs/envgene-objects.md#namespace) names for different sites (for example onsite or offsite) using EnvGene templates.

## Why Different Namespace Names?

Sometimes, onsite and offsite environments need different namespace names due to company policy, multi-tenant setups, or integration requirements. You can handle this using Jinja2 logic in your templates and by passing variables from your inventory.

## Option 1: Namespace Name in the Template Descriptor Under the `namespaces` Block

```yaml
...
namespaces:
  - template_path: <template_path>
    {% if current_env.additionalTemplateVariables.onsite %}
    template_override:
      name: "{{ current_env.additionalTemplateVariables.ns_names.kafka }}"
    {% endif %}
...
```

- Changes should be made in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor)

## Option 2: Namespace Name Directly in Namespace object

```yaml
{% if current_env.additionalTemplateVariables.onsite %}
name: "{{ current_env.additionalTemplateVariables.ns_names.kafka }}"
{% else %}
name: "{{ current_env.name }}-core"
{% endif %}
...
```

- Changes should be made in the [Namespace](/docs/envgene-objects.md#namespace)

## Example Environment Inventory (`env_definition.yml`) for Both Options

### Onsite Example

```yaml
...
envTemplate:
  additionalTemplateVariables:
    onsite: true
    ns_names:
      kafka: KAFKA-main
...
```

### Offsite Example

```yaml
...
envTemplate:
  additionalTemplateVariables: {}
...
```

- [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- Set `onsite: true` for onsite, and provide the `ns_names` mapping as needed.

## How It Works

- EnvGene checks if the Environment is onsite using `current_env.additionalTemplateVariables.onsite`.
- If yes, it uses the custom namespace from `ns_names.kafka`.
- If no, it uses the default naming scheme (like `{{ current_env.name }}-core`).
- You can add more keys under `ns_names` for other components as needed.
