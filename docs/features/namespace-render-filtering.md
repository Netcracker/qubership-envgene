# Namespace render filtering

- [Namespace render filtering](#namespace-render-filtering)
  - [Description](#description)
  - [Flow](#flow)
  - [Behaviour](#behaviour)
  - [Role of `BG_NS_TARGET`](#role-of-bg_ns_target)
  - [Examples](#examples)
    - [One ordinary Namespace](#one-ordinary-namespace)
    - [Several applications](#several-applications)
    - [Template Namespaces outside the SD](#template-namespaces-outside-the-sd)
    - [BG Domain origin or peer](#bg-domain-origin-or-peer)
    - [No Solution Descriptor](#no-solution-descriptor)
  - [Error handling](#error-handling)
  - [Related documentation](#related-documentation)

## Description

When a pipeline run supplies a [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor)
(SD), EnvGene limits which Environment [Namespaces](/docs/envgene-objects.md#namespace) `env_build`
re-renders. Cloud, Tenant, and other non-Namespace objects are still rendered.

Selection is automatic. EnvGene does not accept a manual Namespace render filter parameter.

The selection answers which Namespaces `env_build` may rewrite. Resolution of SD
[`deployPostfix`](/docs/glossary.md#deploy-postfix) values to Namespace `name` values belongs to
[Namespace map](/docs/tech/namespace-map.md).

## Flow

```text
Solution Descriptor
    → Namespace map
    → list of selected Namespace.name values
    → env_build
    → render only the selected Namespaces
```

1. The run supplies an SD (applications and their `deployPostfix` values).
2. `compute_namespace_map` builds [`namespace-map.yml`](/docs/envgene-objects.md#namespace-map) and
   resolves each relevant `deployPostfix` to a Namespace `name`. For a
   [BG Domain](/docs/envgene-objects.md#bg-domain),
   [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) selects origin or peer at
   map-build time.
3. EnvGene passes the resulting list of Namespace `name` values into `env_build`.
4. `env_build` re-renders only those Namespaces. It does not re-derive `deployPostfix` →
   Namespace `name`, and it does not convert `BG_NS_TARGET` into a render filter expression.

## Behaviour

| Situation                                                         | Result                                              |
|-------------------------------------------------------------------|-----------------------------------------------------|
| SD has one ordinary Namespace                                     | Only that Namespace is rendered                     |
| SD has several applications                                       | Every Namespace mapped from those apps is rendered  |
| Environment Template has Namespaces not referenced by the SD      | Those Namespaces are not rendered                   |
| BG Domain and `BG_NS_TARGET=origin`                                | Namespace map selects origin; only origin is rendered |
| BG Domain and `BG_NS_TARGET=peer`                                  | Namespace map selects peer; only peer is rendered   |
| No SD for the run, and the process supports that scenario         | All Namespaces are rendered (unchanged default)     |

## Role of `BG_NS_TARGET`

[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) is an input to Namespace map
resolution when origin and peer share a `deployPostfix`. It is not a render filter and is not
translated into `@origin` or `@peer` selectors for `env_build`.

After the map contains concrete Namespace `name` values, `env_build` uses only that list.

## Examples

### One ordinary Namespace

SD applications use `deployPostfix: core`. The map contains `core: env-1-core`. `env_build`
renders only `env-1-core`.

### Several applications

SD applications use `deployPostfix` values `core` and `bss`. The map resolves both. `env_build`
renders the corresponding Namespace `name` values.

### Template Namespaces outside the SD

The Environment Template also defines a Namespace that no SD application maps to. That Namespace is
not rendered in this run.

### BG Domain origin or peer

Pipeline:

```yaml
BG_NS_TARGET: peer
```

SD applications use `deployPostfix: bss`. The map writes `bss: env-1-bss-peer`. `env_build`
renders only `env-1-bss-peer`. The origin Namespace is left unchanged.

With `BG_NS_TARGET: origin`, the map writes `bss: env-1-bss-origin` and `env_build` renders only
that Namespace.

### No Solution Descriptor

When the run does not supply an SD and that scenario is supported, EnvGene renders all Namespaces.

## Error handling

Unmapped or BG-ambiguous `deployPostfix` values follow the
[Namespace map validation](/docs/tech/namespace-map.md#validation) policy. `env_build` does not add
a separate duplicate error path for the same cases.

## Related documentation

- [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target)
- [Namespace map](/docs/tech/namespace-map.md)
- [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor)
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md)
- [Blue-Green Deployment deploy operations](/docs/how-to/blue-green-deployment-deploy-operations.md)
