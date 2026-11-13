# Proposal

## Why

The SBOM generator builds the application SBOM from the Deployment Descriptor (DD) zip part, but after
delivery to an onsite site the DD is obfuscated and that archive layout no longer matches, so the build
reads the wrong source. Traversing the archive also risks pulling in helm libraries that are not
deployable components. The deployable component list already lives in the DD JSON, and the only extra
input the SBOM needs is the application chart named in the DD, for its resource profiles.

## What Changes

- The SBOM generator downloads the application chart `.tgz` named in the DD `charts[0]` instead of the
  DD zip part. The chart is read only for resource profiles.
- The application SBOM component list is taken strictly from the DD - services, configurations, and
  images - with each component named by its DD name and each image-type component carrying the
  `application/octet-stream` MIME type. The chart-tree traversal that extended the list is removed, so
  helm libraries are never added. **BREAKING**
- Chart coordinate resolution gains an obfuscated-onsite branch. When the DD carries a chart registry and
  a full chart name, they are used verbatim. When the chart registry is empty, the download URL is
  reconstructed from the chart's group repository, honoring a `HELM_MAP_REPOSITORIES` override so the
  SBOM resolves the identical chart the deploy side resolves.
- The application chart becomes a hard dependency. SBOM generation fails loud with a readable error when
  the DD names no chart, and when the named chart cannot be fetched. **BREAKING**
- The effective-set generator fails loud when a SBOM has no app-chart component, with a readable error
  naming the application, instead of silently writing per-service parameters under per-service-name
  directories. Per-service parameters are always written under the directory keyed by the normalized
  app-chart name, one section per service. **BREAKING**
- The `app_chart_validation` effective-set configuration toggle is removed. The app-chart requirement is
  unconditional. A still-present `app_chart_validation` entry is ignored and does not raise an
  unknown-option error. **BREAKING**

## Capabilities

### New Capabilities

- `sbom-application-chart-source`: how the application SBOM is sourced - the DD-plus-chart inputs, the
  strict DD component list, chart coordinate resolution across the offsite and obfuscated-onsite cases,
  and the hard-dependency failure modes.
- `effective-set-app-chart-requirement`: the effective-set generator's unconditional app-chart
  requirement - the fail-loud on a missing app-chart component, the single normalized-app-chart-name
  per-service layout, and the ignored legacy toggle.

### Modified Capabilities

<!-- No existing specs under openspec/specs/ cover these behaviors. -->

## Impact

- Objects and parameters: the `HELM_MAP_REPOSITORIES` cloud end-to-end parameter is consulted in the
  obfuscated branch. The `app_chart_validation` effective-set configuration entry is removed.
- Pipeline steps: SBOM generation and effective-set generation.
- Docs: the SBOM generation feature doc and the effective-set calculator doc.
- Decision record: [ADR-0012](../../../docs/adr/0012-source-application-sbom-from-dd-and-chart.md).
- Behavior detail: the delta specs under
  [specs/](specs/sbom-application-chart-source/spec.md) and
  [specs/](specs/effective-set-app-chart-requirement/spec.md).

Out of scope, each a separate follow-up change:

- Forcing the coordinate source from the registry definition even when the DD carries coordinates, an
  `artifact_coordinate_source` policy honored by both the SBOM and the deploy side.
- The registry-definition adapter falling back to the Maven domain for the helm section.
