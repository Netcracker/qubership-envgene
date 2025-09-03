
# Template Override

- [Template Override](#template-override)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Template Descriptor](#template-descriptor)
      - [Examples](#examples)
        - [Namespace override](#namespace-override)
        - [Cloud override](#cloud-override)

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

If `template_override` contains Jinja expressions, it must be declared as a multi-line string, for example, using the [literal style](https://yaml.org/spec/1.2.2/#812-literal-style) in YAML.

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
