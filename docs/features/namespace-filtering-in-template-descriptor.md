# Namespace Filtering in Template Descriptor

## Overview

Namespace Filtering in Template Descriptor allows generating an Environment that includes only a selected subset of namespaces from a unified Environment Template.

This feature works at Template Descriptor rendering time and defines the structural composition of the generated Environment.

## How-To

For step-by-step instructions, see:  
[How to filter namespaces in an Environment Template](../how-to/namespace-filtering-in-template-descriptor(Jinja%20TD).md)

## Problem Statement

We have been using a unified platform template for different projects. This template contains namespaces for a Default Cloud Layout, but during deployment we often need only a subset of available namespaces.

Currently, there is no possibility to filter namespaces during Template Descriptor rendering. This leads to the following:

- The `Namespaces/` folder in the EnvGene Instance repository contains non-relevant namespaces
- The effective-set topology includes namespaces that are not required for the target deployment
- We cannot include/exclude namespaces specific to the cluster type (k8s or ocp)
- It prevents using a single unified platform template

## Proposed Approach

Treat the Template Descriptor (TD) as a Jinja template while keeping backward compatibility for non-Jinja TD.

This enables filtering individual namespaces during Environment generation using Jinja `if` expressions.

Filtering can be driven by:

- `current_env.solution_structure` (solution-descriptor–based scenarios)
- `env_type` (cluster-type–based include/exclude scenarios)
- shared template variables (e.g., `ns_list`)

### Example (cluster type filtering)

```jinja
{% if current_env.additionalTemplateVariables.env_type == "ocp" %}
  - template_path: "{{ templates_dir }}/env_templates/Namespaces/ingress-nginx.yml.j2"
    name: ingress-nginx
{% endif %}
```

## Supported Template Descriptor Formats

In addition to existing extensions:

- `yaml`
- `yml`

EnvGene also supports:

- `yaml.j2`
- `yml.j2`

---

## File Resolution Priority

If multiple Template Descriptor files exist, EnvGene selects them in descending priority order:

1. `yml.j2`
2. `yaml.j2`
3. `yml`
4. `yaml`

Jinja-based descriptors take precedence over static ones.

## Behavior During Environment Generation (Scenario)

### Scenario: Generating an Environment with namespace filtering

1. EnvGene starts Environment Instance generation.
2. EnvGene reads the Template Descriptor (TD).
3. If the TD is a Jinja template (`*.yml.j2` / `*.yaml.j2`), EnvGene renders it first.
4. While rendering, EnvGene evaluates all Jinja `if` conditions for namespaces.
5. EnvGene keeps only the namespaces where the condition is `true`.
6. EnvGene generates the Environment using the final (rendered) TD.

### What happens when a namespace condition is `false`

If a namespace is disabled by a condition:

- EnvGene does **not** create the namespace folder in the Instance repository
- EnvGene does **not** generate the namespace object
- The namespace does **not** appear in the effective-set topology

> [!IMPORTANT]
> If you are using `NS_BUILD_FILTER`, keep in mind that this parameter only limits which namespaces are processed during a specific pipeline run — it does not add namespaces to the Environment structure.
>
> If a namespace is excluded during Template Descriptor rendering (Jinja condition = `false`), it will not be generated and will not appear in the Instance repository or effective-set topology.
>
> Therefore, such a namespace cannot be processed via `NS_BUILD_FILTER`, because it does not exist in the Environment model.
> For details about `NS_BUILD_FILTER` syntax and usage, see:
[Namespace Render Filter](/docs/features/namespace-render-filtering.md)
