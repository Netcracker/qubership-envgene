# Namespace map

- [Namespace map](#namespace-map)
  - [Description](#description)
  - [Namespace map file](#namespace-map-file)
  - [Resolution without a BG Domain](#resolution-without-a-bg-domain)
  - [Resolution with a BG Domain](#resolution-with-a-bg-domain)
  - [Role of `BG_NS_TARGET`](#role-of-bg_ns_target)
  - [Consumers](#consumers)
  - [Validation](#validation)
  - [Out of scope](#out-of-scope)
  - [Related documentation](#related-documentation)

## Description

The namespace map resolves a
[`deployPostfix`](/docs/glossary.md#deploy-postfix) from a
[Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) (or an equivalent application
list) to the [Namespace](/docs/envgene-objects.md#namespace) `name` in the Environment Instance.

EnvGene builds the map in `compute_namespace_map` and writes
[`namespace-map.yml`](/docs/envgene-objects.md#namespace-map). Downstream components consume the file.
They do not re-derive Blue-Green (BG) roles from pipeline parameters.

In a [BG Domain](/docs/envgene-objects.md#bg-domain), origin and peer Namespaces often share one
`deployPostfix` while their Namespace `name` values differ. The map uses
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) to choose which side to bind.

`BG_NS_TARGET` names the static BG Domain role (`origin` or `peer`). It is not a lifecycle state such
as `ACTIVE`, `IDLE`, or `CANDIDATE`. Namespace-map resolution does not read BG state files.

## Namespace map file

**Location:** `/environments/<cluster-name>/<environment-name>/Inventory/namespace-map.yml`

Flat map:

```yaml
<deployPostfix>: <namespace-name>
```

Example without a BG Domain:

```yaml
core: env-1-core
bss: env-1-bss
```

Example with a BG Domain and [`BG_NS_TARGET: peer`](/docs/instance-pipeline-parameters.md#bg_ns_target):

```yaml
bss: env-1-bss-peer
```

The map value is the `name` field from `Namespaces/<folder>/namespace.yml`, not the folder name
alone. For BG origin and peer folders the folder name is typically
`<deployPostfix>-origin` or `<deployPostfix>-peer`. See
[Namespace Folder Name Generation](/docs/features/environment-instance-generation.md#namespace-folder-name-generation).

## Resolution without a BG Domain

Each `deployPostfix` maps to exactly one Namespace `name`.
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) is not required.

## Resolution with a BG Domain

1. EnvGene lists Environment Namespaces and reads the BG Domain object.
2. For each Namespace it derives the `deployPostfix` (folder name without a trailing
   `-origin` or `-peer` suffix when the Namespace is an origin or peer member).
3. It compares the Namespace `name` to `originNamespace.name` and `peerNamespace.name` in
   the BG Domain.
4. When a `deployPostfix` matches both origin and peer members:
   - [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) must be `origin` or `peer`
   - the map entry uses `originNamespace.name` or `peerNamespace.name` for that role
5. Namespaces that are not origin or peer members (including the controller) keep a one-to-one
   mapping and do not require `BG_NS_TARGET`.

### Peer example

Pipeline:

```yaml
BG_NS_TARGET: peer
```

Solution Descriptor applications use:

```yaml
deployPostfix: bss
```

BG Domain:

```yaml
originNamespace:
  name: env-1-bss-origin
peerNamespace:
  name: env-1-bss-peer
```

Resulting map entry:

```yaml
bss: env-1-bss-peer
```

### Origin example

With the same BG Domain and `BG_NS_TARGET: origin`:

```yaml
bss: env-1-bss-origin
```

## Role of `BG_NS_TARGET`

| Situation                                       | `BG_NS_TARGET`                 |
|-------------------------------------------------|--------------------------------|
| No BG Domain                                    | Not required                   |
| `deployPostfix` not shared by origin/peer     | Not required for that postfix  |
| One `deployPostfix` shared by origin and peer | Mandatory (`origin` or `peer`) |
| Invalid value                                   | Pipeline fails                 |

The Solution Descriptor keeps the `deployPostfix` only. It does not store `BG_NS_TARGET` and does
not name `originNamespace.name` or `peerNamespace.name`.

## Consumers

- **Deployment Plan Generator** reads `namespace-map.yml` and sets the `namespace` field on each
  Deployment Plan entry from `deployPostfix`. It does not interpret `BG_NS_TARGET` again.
- Other modern-pipeline steps that need `deployPostfix` → Namespace `name` use the same map.

Namespace-map resolution is separate from
[Namespace Render Filter](/docs/features/namespace-render-filtering.md), which limits which
Namespaces `env_build` re-renders.

## Validation

EnvGene fails `compute_namespace_map` when:

- a `deployPostfix` matches both BG origin and peer and `BG_NS_TARGET` is missing
- `BG_NS_TARGET` is set to a value other than `origin` or `peer`
- the selected BG Domain role has no matching Namespace in the Environment Instance
- the BG Domain configuration is incomplete or ambiguous for the Namespaces being mapped

Example error intent:

```text
BG_NS_TARGET is required to resolve deployPostfix 'bss': both origin and peer Namespaces
belong to the BG Domain.
```

## Out of scope

- BGD lifecycle operations and state-file transitions
- Interpreting `ACTIVE`, `IDLE`, or `CANDIDATE` as `BG_NS_TARGET`
- Changing the Solution Descriptor schema
- Effective Set folder-selection internals beyond consuming an already resolved Deployment Plan
  namespace (see open Effective Set work)

## Related documentation

- [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target)
- [Namespace map object](/docs/envgene-objects.md#namespace-map)
- [BG Domain](/docs/envgene-objects.md#bg-domain)
- [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor)
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md)
- [Namespace Render Filter](/docs/features/namespace-render-filtering.md)
