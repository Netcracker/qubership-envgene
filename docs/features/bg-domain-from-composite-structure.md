# BG Domain from Composite Structure

- [BG Domain from Composite Structure](#bg-domain-from-composite-structure)
  - [Description](#description)
  - [Problem](#problem)
  - [Sources of `bg_domain.yml`](#sources-of-bg_domainyml)
  - [Generation from the Composite Structure](#generation-from-the-composite-structure)
  - [Which source EnvGene uses](#which-source-envgene-uses)
  - [Environment Instance generation order](#environment-instance-generation-order)
  - [Effect on consumers](#effect-on-consumers)
  - [Authoring guidance](#authoring-guidance)
  - [Validation](#validation)
  - [Related documentation](#related-documentation)

## Description

EnvGene can generate the standalone
[BG Domain](/docs/envgene-objects.md#bg-domain) file `bg_domain.yml` from an inline
`type: bgdomain` member of the
[Composite Structure](/docs/envgene-objects.md#composite-structure).

That keeps one authoring surface for solutions that embed the Blue-Green Domain in the composite
(for example as a satellite). Steps that already read `bg_domain.yml` keep working without a second
[BG Domain Template](/docs/envgene-objects.md#bg-domain-template).

The Composite Structure file remains in the Environment Instance. Generation from the composite
copies the domain into the standalone BG Domain object. It does not remove the inline member.

## Problem

Two objects can describe the same Blue-Green Domain:

- an inline `bgdomain` member inside `composite_structure.yml`
- a standalone `bg_domain.yml`

Without generation from the composite, authors must keep a Composite Structure Template and a BG
Domain Template aligned. Some EnvGene steps and Effective Set topology fields read only the
standalone file. When the domain exists only inline, those consumers see no BG Domain.

## Sources of `bg_domain.yml`

| Source                                                         | Role                                                                         |
|----------------------------------------------------------------|------------------------------------------------------------------------------|
| [BG Domain Template](/docs/envgene-objects.md#bg-domain-template) via the `bg_domain` key on the Environment Template descriptor | Explicit generation hook. EnvGene renders `bg_domain.yml` from the template  |
| Inline `type: bgdomain` in the rendered Composite Structure    | Fallback source when the `bg_domain` descriptor key is absent                |

Generation from the composite is a fallback. It runs only when the Environment Template descriptor
does not define `bg_domain`.

## Generation from the Composite Structure

1. EnvGene renders `composite_structure.yml` from the
   [Composite Structure Template](/docs/envgene-objects.md#composite-structure-template).
2. It searches `baseline` and each `satellites` member for `type: bgdomain`.
3. When generation from the composite applies, it writes
   `/environments/<cluster-name>/<environment-name>/bg_domain.yml` from that member.
4. The written object is a standalone
   [BG Domain](/docs/envgene-objects.md#bg-domain): `name`, `type: bgdomain`,
   `originNamespace`, `peerNamespace`, and `controllerNamespace`.
5. Fields present on the inline member are copied into `bg_domain.yml`.
6. The inline member stays in `composite_structure.yml`.

> [!NOTE]
> The [Composite Structure schema](/schemas/composite-structure.schema.json) currently allows
> `type: bgdomain` on `baseline` only. `satellites` items are limited to `type: namespace`, and the
> inline `controllerNamespace` object does not declare `credentials` or `url`. The object reference
> and this feature describe a satellite BG Domain and copy of those controller fields because
> standalone [BG Domain](/docs/envgene-objects.md#bg-domain) consumers require them. Extending the
> schema is part of implementing this feature.

### Example

Rendered Composite Structure (BG Domain as `baseline`; the same field copy applies when a satellite
`bgdomain` is supported by the schema):

```yaml
name: "clusterA-env-1-composite-structure"
baseline:
  type: bgdomain
  name: env-1-bss-bg-domain
  originNamespace:
    type: namespace
    name: env-1-bss-origin
  peerNamespace:
    type: namespace
    name: env-1-bss-peer
  controllerNamespace:
    type: namespace
    name: env-1-bss-controller
satellites:
  - name: env-1-api
    type: namespace
```

Generated `bg_domain.yml` (shape of the standalone object; `credentials` and `url` appear only when
present on the inline member after the schema allows them):

```yaml
name: env-1-bss-bg-domain
type: bgdomain
originNamespace:
  type: namespace
  name: env-1-bss-origin
peerNamespace:
  type: namespace
  name: env-1-bss-peer
controllerNamespace:
  type: namespace
  name: env-1-bss-controller
```

## Which source EnvGene uses

Decision order:

1. If the Environment Template descriptor has `bg_domain`, EnvGene renders `bg_domain.yml` from the
   BG Domain Template.
2. Else if the Composite Structure has exactly one inline `type: bgdomain` member, EnvGene generates
   `bg_domain.yml` from that member.
3. Else EnvGene does not write `bg_domain.yml`.

| Descriptor has `bg_domain` | Inline `bgdomain` in composite | `bg_domain.yml`                         | Extra behaviour                                      |
|----------------------------|--------------------------------|-----------------------------------------|------------------------------------------------------|
| Yes                        | No                             | From BG Domain Template                 | -                                                    |
| Yes                        | Yes                            | From BG Domain Template                 | Warning: inline domain is not used for this file     |
| No                         | Yes                            | Generated from the Composite Structure  | -                                                    |
| No                         | No                             | Not written                             | -                                                    |

Why this order:

- The `bg_domain` descriptor key is the existing explicit generation hook. Environments that already
  use a BG Domain Template keep the same result.
- Generation from the composite is only for Environments that omit that key and embed the domain in
  the composite (one authoring surface).
- When both are present, EnvGene does not silently overwrite the template result with the composite
  fallback. It keeps the template output and warns that the inline member is ignored for
  `bg_domain.yml`.

## Environment Instance generation order

Relative order for this feature:

1. Render Namespace, Cloud, and Tenant objects as today.
2. Render `composite_structure.yml`.
3. If the descriptor has no `bg_domain`, generate `bg_domain.yml` from the composite when an inline
   `bgdomain` member is present.
4. If the descriptor has `bg_domain`, render `bg_domain.yml` from the BG Domain Template. If an
   inline `bgdomain` member also exists, emit the warning from the table above.
5. Run BG Domain validation and downstream steps that read `bg_domain.yml` (for example credentials
   creation and namespace role resolution).

Exact job names differ between pipeline layouts. The observable rule is the decision order in
[Which source EnvGene uses](#which-source-envgene-uses).

## Effect on consumers

After EnvGene generates or renders standalone `bg_domain.yml`, consumers that read that file behave
as for any Environment with a BG Domain, including:

- [Blue-Green Deployment](/docs/features/blue-green-deployment.md) lifecycle (`bg_manage`)
- Namespace role aliases such as `@origin` / `@peer`
- Effective Set Topology Context `bg_domain` (see
  [calculator-cli](/docs/features/calculator-cli.md#version-20topology-context-bg_domain-example))

`composite_structure` in the Topology Context still carries the full composite, including the
inline `bgdomain` member when it is present.

## Authoring guidance

- Prefer a single authoring path: either embed the domain in the Composite Structure Template and
  omit the `bg_domain` descriptor key, or use a BG Domain Template and do not rely on generation
  from the composite for `bg_domain.yml`.
- Do not set both paths unless you accept that only the BG Domain Template feeds `bg_domain.yml`
  and EnvGene warns about the unused inline member.
- When you rely on generation from the composite, put every field required by standalone BG Domain
  consumers on the inline `bgdomain` member. Namespace names are always required. Controller
  credentials and URL are required when lifecycle or Effective Set need them, after the Composite
  Structure schema allows those fields.
- Do not expect generation from the composite to invent credentials or controller URL. Missing
  fields on the inline member stay missing on `bg_domain.yml`.

## Validation

EnvGene fails Environment Instance generation when:

- generation from the composite is selected and more than one `type: bgdomain` member exists in the
  composite (baseline and satellites together)
- generation from the composite is selected and the chosen member is missing required BG Domain
  fields for a standalone object (`name`, `type`, origin, peer, and controller names)
- the written `bg_domain.yml` fails existing BG Domain validation (for example referenced
  Namespaces are missing)

When the descriptor has `bg_domain` and the composite also has an inline `bgdomain` member, EnvGene
does not fail for that combination alone. It renders from the template and warns that the inline
member is not used for `bg_domain.yml`.

When the BG Domain Template path is selected, existing template-render validation applies
unchanged.

## Related documentation

- [Composite Structure](/docs/envgene-objects.md#composite-structure)
- [Composite Structure Template](/docs/envgene-objects.md#composite-structure-template)
- [BG Domain](/docs/envgene-objects.md#bg-domain)
- [BG Domain Template](/docs/envgene-objects.md#bg-domain-template)
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md)
- [Environment Instance generation](/docs/features/environment-instance-generation.md)
- [`bg_domain` Topology Context](/docs/features/calculator-cli.md#version-20topology-context-bg_domain-example)
