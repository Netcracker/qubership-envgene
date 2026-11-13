# ADR-0012: Source the application SBOM from the DD and the application chart

Status: Proposed

## Context and problem statement

EnvGene builds the application SBOM from the deployment-artifacts archive carried in the Deployment
Descriptor zip part. After a solution is delivered to an onsite site the Deployment Descriptor is
obfuscated, and that archive layout no longer matches what the build expects, so the SBOM is built from
the wrong source. Reading the archive is also risky even offsite, because traversing the chart tree can
pull in helm libraries that are not deployable components. The deployable component list already lives in
the Deployment Descriptor JSON, which is complete and stable across delivery, and the only extra input the
SBOM still needs is the application chart, for its resource profiles.

## Decision drivers

- The source must stay correct after onsite obfuscation, where the zip part no longer matches.
- The application SBOM must list only deployable components, and must not newly leak helm libraries.
- The SBOM must resolve the same application chart the deploy side resolves, so both read an identical
  chart.
- A missing input must surface as a readable stop, not a silently incomplete result consumed downstream.

## Considered options

- Source the application SBOM from the Deployment Descriptor JSON plus the application chart, with the
  component list taken strictly from the Deployment Descriptor (chosen).
- Keep reading the Deployment Descriptor zip part and building the SBOM from the extracted archive.
- Take the component list from a traversal of the application chart tree.

## Decision outcome

Chosen: source the application SBOM from the Deployment Descriptor JSON plus the application chart, taking
the component list strictly from the Deployment Descriptor, because the Deployment Descriptor is the
complete and delivery-stable record of the deployable components and the chart is needed only for the
resource profiles.

When the Deployment Descriptor carries a chart registry and a full chart name, those coordinates are used
as they stand. When the chart registry is empty after obfuscation, the chart download address is
reconstructed from the chart's group repository, honoring a per-group repository override when one is set
and otherwise falling back to the Maven repository domain joined with the group repository name. This
resolves to the identical chart the deploy side resolves, so the SBOM and the deploy read the same chart.

The application chart is a hard dependency. It fails loud at two independent points:

- When the Deployment Descriptor names no chart, SBOM generation stops with a readable error naming the
  application.
- When the chart is named but cannot be fetched, SBOM generation stops with a readable error naming the
  chart.

The effective-set generation also stops loud when a SBOM carries no application-chart component, with a
readable error naming the application, rather than silently changing the per-service parameter layout. The
per-service parameters are always written under one directory keyed by the normalized application-chart
name. The previous configuration toggle that guarded the application-chart presence check is removed, so
the requirement is unconditional, and a configuration that still carries the toggle loses its effect
silently.

## Pros and cons of the options

### Deployment Descriptor JSON plus application chart, component list strictly from the DD (chosen)

- Good, because the Deployment Descriptor is complete and stable across delivery, so the source stays
  correct after onsite obfuscation.
- Good, because taking the component list strictly from the Deployment Descriptor keeps the output
  identical to today and never leaks helm libraries, which a chart traversal would newly expose.
- Good, because reconstructing the chart address from the group repository resolves the same chart the
  deploy side resolves, so the two agree.
- Bad, because the application chart becomes a hard dependency, so a missing or unfetchable chart now
  stops the pipeline where a tolerant partial result was produced before.
- Bad, because removing the presence-check toggle means a site that still sets it silently loses that
  setting's effect.

### Keep reading the Deployment Descriptor zip part

- Good, because it changes nothing and keeps the current tolerant behavior.
- Bad, because the archive layout no longer matches an obfuscated onsite Deployment Descriptor, so the
  source is wrong exactly where it is now most needed.
- Bad, because traversing the archive can pull in non-deployable helm libraries.

### Take the component list from a chart-tree traversal

- Good, because the chart is already downloaded for its resource profiles, so no extra input is needed.
- Bad, because the chart carries helm libraries that the deployment-artifacts archive never exposed, so
  the component list would regress by listing non-deployable libraries absent from the Deployment
  Descriptor.

## Consequences

- Positive: the application SBOM is sourced from a delivery-stable record, stays correct after onsite
  obfuscation, lists only deployable components, and points at the same chart the deploy side resolves.
- Negative: the application chart becomes a hard dependency, so a missing or unfetchable chart stops the
  pipeline loud at both SBOM generation and effective-set generation, trading the former tolerant partial
  result for a hard stop. Removing the presence-check toggle also means a site that still sets it loses
  that setting's effect silently.

## More information

- Specs:
  [sbom-application-chart-source](../../openspec/changes/sbom-app-chart-download/specs/sbom-application-chart-source/spec.md),
  [effective-set-app-chart-requirement](../../openspec/changes/sbom-app-chart-download/specs/effective-set-app-chart-requirement/spec.md)
- Proposal: [sbom-app-chart-download](../../openspec/changes/sbom-app-chart-download/proposal.md)
- Builds on [ADR-0003](0003-derive-sbom-component-identity-from-dd-only.md), which decided the application
  SBOM component identity comes from the Deployment Descriptor only.
