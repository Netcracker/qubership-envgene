# ADR-0003: Derive Application SBOM component identity from the DD only

Status: Proposed
Date: 2026-08-24

## Context

EnvGene builds the Application SBOM component list from the Deployment Descriptor (DD). For a DD service
of type `service` it also walks the application chart directory tree and adds one component per umbrella
sub-chart, copying the parent's identity and taking the component name from the chart directory. These
chart-derived components are not declared in the DD, they carry the parent's wrong image, and their names
follow the chart's separator convention rather than the DD's. Keeping chart and DD names aligned is the
DD builder's job, which EnvGene neither owns nor validates.

## Decision

We derive every Application SBOM component solely from the DD (`services`, `smartplug`, and
`configurations`), named by its DD name. We remove the chart directory scan and the sub-chart expansion
for all three component types, and we add no rollback toggle.

Rejected:

- Emit a warning for chart sub-charts missing from the DD, because producing it requires the chart scan
  we are removing.
- Gate the removal behind a temporary `config.yml` toggle, because temporary switches tend to become
  permanent, and the observed per-service entries only alias values Helm already propagates through
  `global`, so a lasting rollback surface is not warranted.

## Consequences

- SBOM identity becomes purely DD-driven. No chart traversal, less code, and the DD is the single source
  of truth. Removing the expansion also drops the dead `smartplug` and `configurations` branches that
  duplicated the parent component.
- Cost we accept: an umbrella chart whose sub-charts depend on the expanded chart-named per-service
  entries for their Helm value overrides can lose those overrides. The risk is real and cannot be
  verified across the whole chart fleet, and there is no runtime switch to restore the old behavior.
  Rollback means reverting the generator change.
- Per-application chart-versus-DD divergence is resolved by the DD builder aligning names, not by EnvGene.
