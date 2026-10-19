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

- When the DD still records the chart URL, we download it directly.
- When delivery has stripped the URL, we build it from the Registry Definition Maven host and the Helm group
  repository. The app chart always uses the group repository, regardless of the Maven channel the DD came from.
- The `HELM_MAP_REPOSITORIES` parameter overrides that base per group repository, so an environment can redirect
  chart downloads without editing the Registry Definition.
- The app chart is required. Generation fails when the DD names no chart, or names a chart that cannot be fetched.
- The Effective Set generator also fails when an application's SBOM has no app-chart component.

Rejected:

- Keep downloading the DD ZIP, because it carries deployment artifacts unrelated to the baselines and is far larger.
- Select the Helm repository by Maven channel as Docker images do, because the SBOM would resolve a different chart
  than the deploy side, and the group repository already resolves any channel.
- Read the Helm repository index to locate the chart, because the index is large and the constructed URL covers the
  published layout.

## Consequences

- Resource profiles come from the artifact that is actually deployed, and the download is smaller and cheaper for the
  registry.
- A missing or unreachable app chart fails generation, at SBOM generation and at the Effective Set generator, rather
  than emitting an incomplete SBOM or Effective Set. We accept a hard stop over a silent partial result.
- A chart published outside the constructed base-and-name layout is not found, because the index is not read.

See [SBOM generation](/docs/features/sbom-generation.md), [ADR-0001](/docs/adr/0001-adapt-registry-auth-from-e2e-parameters.md)
for the registry auth parameters, and [ADR-0003](/docs/adr/0003-derive-sbom-component-identity-from-dd-only.md) for the
DD-only component identity.
