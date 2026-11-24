
# Template Override

- [Template Override](#template-override)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Template Descriptor](#template-descriptor)
      - [Examples](#examples)
        - [Namespace override](#namespace-override)
        - [Cloud override](#cloud-override)
    - [How template_override is applied](#how-template_override-is-applied)
    - [template_override and overrides-parent](#template_override-and-overrides-parent)

## Problem Statement

When deploying the same Solution across multiple environment types (DEV, SVT, PROD, etc.), organizations face several pain points:

1. Template Duplication: Maintaining nearly identical copies of environment templates with minor variations leads to:
   1. Increased maintenance overhead
   2. Higher risk of configuration drift between environments

2. Inflexible Configuration: Existing templating mechanisms lack the ability to:
   1. Modify specific components without complete template duplication
   2. Dynamically adjust configurations based on environment type needs

Goals:

  1. Be able to define Resource Profile and Resource Profile Override via Environment Inventory
  2. Be able to create group Environment Templates with common and different parts

## Proposed Approach

In the Environment Descriptor, it becomes possible to describe the override of a Namespace or Cloud templates using the `template_override` attribute. This attribute allows defining the **entirety or a portion of the Namespace or Cloud objects**. When generating an Environment Instance, the content of `template_override` is merged into the Namespace or Cloud object.

`template_override` may contain Jinja expressions. In such cases, the content of `template_override` will be rendered using the same context as the Namespace or Cloud template and then merged into the rendered Namespace or Cloud during Environment Instance generation.

If `template_override` contains Jinja expressions, it must be declared as a multi-line string, for example, using the [literal style](https://spec.yaml.io/main/spec/1.2.2/#812-literal-style) in YAML.

### Template Descriptor

```yaml
tenant: "<path-to-the-tenant-template-file>"
# Cloud configuration can be specified either as direct template path (string)
# or as an object with template_path and optional overrides
cloud: "<path-to-the-cloud-template-file>"
# or
cloud:
  template_path: "<path-to-the-cloud-template-file>"
  template_override:
    <yaml or jinja expression> # entirety or a portion of the Cloud object or a Jinja expression that should render into entirety or a portion of the Cloud object
namespaces:
  - template_path: <path-to-ns-template>
    template_override:
      <yaml or jinja expression> # entirety or a portion of the Namespace object or a Jinja expression that should render into entirety or a portion of the Namespace object
```

#### Examples

##### Namespace override

```yaml
tenant: "{{ templates_dir }}/env_templates/dev/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/dev/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/dev/Namespaces/bss.yml.j2"
    template_override:
      profile:
        name: prod_bss_override
        baseline: prod
```

In this example, the generated Environment Instance will include a Namespace object based on the bss Namespace template, with the following attribute values under profile:

```yaml
profile:
  name: prod_bss_override
  baseline: prod
```

This will override any values defined in the original `bss.yml.j2` template.

##### Cloud override

```yaml
tenant: "{{ templates_dir }}/env_templates/dev/tenant.yml.j2"
cloud:
  template_path: "{{ templates_dir }}/env_templates/dev/cloud.yml.j2"
  template_override:
    <yaml or jinja expression> # entirety or a portion of the Cloud object or a Jinja expression that should render into entirety or a portion of the Cloud object
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/dev/Namespaces/bss.yml.j2"

```

In this example, the generated Environment Instance will include a Cloud object based on the Cloud template, with the following attribute values under profile:

```yaml
profile:
  name: prod_override
  baseline: prod
```

This will override any values defined in the original `cloud.yml.j2` template.

### How template_override is applied

EnvGene applies `template_override` during Environment Instance generation, after it renders the Namespace or Cloud
template:

1. EnvGene renders `template_override` with Jinja, with the same context as the Namespace or Cloud template. The result
   must be a YAML object.
2. EnvGene merges the result into the rendered Namespace or Cloud. The values from `template_override` win.

The rules for the merge:

- An attribute that the rendered object does not have is added.
- If the attribute is an object in both, EnvGene merges the two objects recursively.
- If the attribute is a list in both, EnvGene appends the entries that the list does not have yet. This applies to
  scalar and nested list entries. EnvGene appends object entries as they are.
- In every other case, the value from `template_override` replaces the value of the rendered object.

The Cloud must be an object with `template_path` to have `template_override`. A Cloud that is only a path string cannot
have it.

`template_override` can contain any attribute of the Namespace or Cloud object. For the attributes that
`overrides-parent` generates, see the [Template Descriptor](/docs/envgene-objects.md#template-descriptor) object.

### template_override and overrides-parent

`template_override` and `overrides-parent` both change a Namespace or a Cloud, but they act at different stages:

- `overrides-parent` is part of [Template Composition](/docs/features/template-composition.md). EnvGene resolves it when
  it builds a template that has a parent template, and writes the result into `template_override`. Use it to change a
  Namespace or Cloud that the template inherits with `parent`.
- `template_override` is applied when EnvGene generates the Environment Instance. Use it to change a Namespace or Cloud
  entry that has no `parent`.

In an entry that has `parent`, put the change in `overrides-parent`. When EnvGene builds the template, it ignores a
`template_override` that you set in that entry. It keeps the `template_override` of the parent template and adds the
result of `overrides-parent` to it.
