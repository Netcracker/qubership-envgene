# ADR-0009: Download the app chart for SBOM generation instead of the DD ZIP

Status: Proposed

## Context

SBOM generation reads each application's resource-profile baselines from the Deployment Descriptor (DD) ZIP part. The
ZIP is a full deployment bundle that also carries binaries, scripts, and other artifacts, so it is far larger than the
baselines need, which inflates download time and load on the registry. The baselines also live in the application Helm
chart named in the DD, a much smaller artifact that the deploy side already fetches.

## Decision

We download the application Helm chart to read the resource-profile baselines, replacing the DD ZIP download, and
resolve the chart the same way the deploy side resolves it:

- When the DD still records the chart URL, we download it directly, because that recorded URL is the authoritative
  published location of the chart.
- When delivery has stripped the URL, we rebuild it from the Registry Definition Maven host and the Helm group
  repository, always the group repository regardless of the Maven channel, because the deploy side resolves it the
  same way and the SBOM must point at the identical chart.
- The `HELM_MAP_REPOSITORIES` parameter overrides that base per group repository, because the v1 Registry Definition
  cannot express a separate Helm host and that host is environment-specific.
- The app chart is required: its resource-profile baselines are needed to compute the Effective Set, so a missing or
  unfetchable chart fails generation.
- The Effective Set generator fails too when an application's SBOM has no app-chart component, because it reads
  committed SBOMs independently and must guard its own input rather than trust the upstream check.

Rejected:

- Keep downloading the DD ZIP, because it carries deployment artifacts unrelated to the baselines and is far larger.
- Select the Helm repository by Maven channel as Docker images do, because the SBOM would resolve a different chart
  than the deploy side, and the group repository already resolves any channel.
- Read the Helm repository index to locate the chart, because the index is large and the constructed URL covers the
  published layout.

## Consequences

- Resource profiles come from the artifact that is actually deployed, and the download is smaller and cheaper for the
  registry.
- We accept that a missing or unreachable app chart stops generation instead of yielding an incomplete SBOM or
  Effective Set.
- A chart published outside the constructed base-and-name layout is not found, because the index is not read.

See [SBOM generation](/docs/features/sbom-generation.md), [ADR-0001](/docs/adr/0001-adapt-registry-auth-from-e2e-parameters.md)
for the registry auth parameters, and [ADR-0003](/docs/adr/0003-derive-sbom-component-identity-from-dd-only.md) for the
DD-only component identity.
