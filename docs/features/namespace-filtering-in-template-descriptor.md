# Namespace Filtering in Template Descriptor

- [Namespace Filtering in Template Descriptor](#namespace-filtering-in-template-descriptor)
  - [Overview](#overview)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Example (cluster type filtering)](#example-cluster-type-filtering)
  - [File Resolution Priority](#file-resolution-priority)
  - [Behavior During Environment Generation](#behavior-during-environment-generation)
    - [Scenario: Generating an Environment with namespace filtering](#scenario-generating-an-environment-with-namespace-filtering)
    - [What happens when a namespace condition is `false`](#what-happens-when-a-namespace-condition-is-false)
  - [How-To](#how-to)

## Overview

Namespace Filtering in Template Descriptor allows generating an Environment that includes only a selected subset of namespaces from a unified Environment Template.

This feature works during Environment Instance generation, and defines the structural composition of the generated Environment.

## Problem Statement

We have been using a unified Environment Template for different projects. This template contains all possible namespaces, but during deployment we often need only a subset of available namespaces.

Currently, there is no possibility to filter namespaces during Environment Instance generation. This leads to the following:

- The `Namespaces/` folder in the EnvGene Instance Repository contains non-relevant namespaces
- The Effective Set includes namespaces that are not required for the target deployment
- We cannot include/exclude namespaces specific to the cluster type (k8s or ocp)

It prevents using a single unified Environment Template

## Proposed Approach

Treat the Template Descriptor (TD) as a Jinja template while keeping backward compatibility for non-Jinja TD.

This enables filtering individual namespaces during Environment generation using Jinja `if` expressions.

You can use different filtering approaches depending on your use case:

- **Cluster-type filtering**: Use a variable to include/exclude namespaces based on cluster type (k8s/ocp)
- **Explicit namespace list**: Use shared template variables (e.g., `ns_list`) to control which namespaces are enabled
- **Solution-based filtering**: Use `current_env.solution_structure` for solution-descriptor–based scenarios

### Example (cluster type filtering)

```jinja
{% if current_env.additionalTemplateVariables.env_type == "ocp" %}
  - template_path: "{{ templates_dir }}/env_templates/Namespaces/ingress-nginx.yml.j2"
    name: ingress-nginx
{% endif %}
```

## File Resolution Priority

If multiple Template Descriptor files exist, EnvGene selects them in descending priority order:

1. `yml.j2`
2. `yaml.j2`
3. `yml`
4. `yaml`

Jinja-based descriptors take precedence over static ones.

## Behavior During Environment Generation

### Scenario: Generating an Environment with namespace filtering

1. EnvGene starts Environment Instance generation.
2. EnvGene reads the Template Descriptor (TD).
3. If the TD is a Jinja template (`*.yml.j2` / `*.yaml.j2`), EnvGene renders it first.
4. While rendering, EnvGene evaluates all Jinja `if` conditions for namespaces.
5. EnvGene keeps only the namespaces where the condition is `true`.
6. EnvGene generates the Environment Instance using the final (rendered) TD.

### What happens when a namespace condition is `false`

If a namespace is disabled by a condition:

- EnvGene does **not** create the namespace folder in the Instance Repository
- EnvGene does **not** generate the namespace object
- The namespace does **not** appear in the Effective Set

> [!NOTE]
> If you are using `NS_BUILD_FILTER`, keep in mind that this parameter only limits which namespaces are processed during a specific pipeline run — it does not add namespaces to the Environment structure.
>
> If a namespace is excluded during Template Descriptor rendering (Jinja condition = `false`), it will not be generated and will not appear in the Instance Repository or Effective Set.
>
> Therefore, such a namespace cannot be processed via `NS_BUILD_FILTER`, because it does not exist in the Environment model.
> For details about `NS_BUILD_FILTER` syntax and usage, see: [Namespace Render Filter](../features/namespace-render-filtering.md)

## How-To

For step-by-step instructions, see:  
[How to filter namespaces in an Environment Template](/docs/how-to/filter-ns-in-template-descriptor.md)
