# Namespace Render Filter

- [Namespace Render Filter](#namespace-render-filter)
  - [Description](#description)
  - [Syntax](#syntax)
    - [BG Domain role aliases](#bg-domain-role-aliases)
    - [Direct namespace names](#direct-namespace-names)
    - [Operators](#operators)
  - [Derivation from `BG_NS_TARGET`](#derivation-from-bg_ns_target)
  - [Usage examples](#usage-examples)
    - [Update all except the peer NS](#update-all-except-the-peer-ns)
    - [Update only the peer NS](#update-only-the-peer-ns)
    - [Update all](#update-all)
    - [Multiple selection](#multiple-selection)
  - [Error handling](#error-handling)
  - [Related documentation](#related-documentation)

## Description

Namespace render filter selects which Environment
[Namespaces](/docs/envgene-objects.md#namespace) are rendered. It does not affect rendering of other
objects such as Cloud or Tenant.

The feature uses the [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#ns_build_filter)
Instance pipeline parameter during Environment Instance generation in the `env_build` job.

It lets you generate or update only specific Namespaces without changing the others. That matters
in Blue-Green deploy runs, where regenerating both origin and peer would rewrite the side you did
not intend to change.

This filter answers which Namespaces `env_build` may rewrite. It does not resolve Solution
Descriptor `deployPostfix` values to a Namespace `name`. That resolution belongs to
[Namespace map](/docs/tech/namespace-map.md).

## Syntax

You can set the value of `NS_BUILD_FILTER` in two ways:

### BG Domain role aliases

You can use BG Domain role aliases as namespace selectors:

- `@controller` - controller namespace
- `@origin` - origin namespace
- `@peer` - peer namespace

EnvGene resolves these aliases using the [BG Domain](/docs/envgene-objects.md#bg-domain) object. To
use aliases, the BG Domain object must exist in the Environment.

### Direct namespace names

You can specify the namespace name directly, as defined in the `name` attribute of the Namespace
object:

- `env-name-api` - full namespace name

### Operators

The following operators are available:

- `!` - exclusion operator. When used at the beginning, it excludes the specified namespaces from
  processing. The `!` operator applies to the entire expression, not to individual namespaces within
  a comma-separated list.
- `,` - multiple selection operator. Separates multiple namespace selectors

## Derivation from `BG_NS_TARGET`

When [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#ns_build_filter) is empty and
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) is set:

| `BG_NS_TARGET` | Effective filter |
|----------------|------------------|
| `peer`         | `@peer`          |
| `origin`       | `@origin`        |

When `NS_BUILD_FILTER` is set explicitly, EnvGene uses that value and does not derive a filter from
`BG_NS_TARGET`.

When both are empty, EnvGene renders all Namespaces (unchanged default behaviour).

## Usage examples

### Update all except the peer NS

```yaml
NS_BUILD_FILTER: "! @peer"
# or
NS_BUILD_FILTER: "! env-name-peer"
```

### Update only the peer NS

```yaml
NS_BUILD_FILTER: "@peer"
# or
NS_BUILD_FILTER: "env-name-peer"
# or, with an empty NS_BUILD_FILTER:
BG_NS_TARGET: peer
```

### Update all

```yaml
NS_BUILD_FILTER: ""
# or
NS_BUILD_FILTER is not provided
# and BG_NS_TARGET is not provided
```

### Multiple selection

```yaml
# Update peer and origin
NS_BUILD_FILTER: "@peer,@origin"

# Update all except peer and controller
NS_BUILD_FILTER: "! @peer,@controller"

# Update specific namespaces by name
NS_BUILD_FILTER: "env-name-api,env-name-frontend"
```

Mixed use of aliases and names is not allowed.

## Error handling

- Invalid or non-existent namespace names: pipeline fails
- Missing BG Domain: pipeline fails when using aliases without a BG Domain
- Invalid [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) when it is used to
  derive the filter: pipeline fails

## Related documentation

- [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#ns_build_filter)
- [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target)
- [Namespace map](/docs/tech/namespace-map.md)
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md)
