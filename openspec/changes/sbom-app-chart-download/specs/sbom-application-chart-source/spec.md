# Spec Delta

## Purpose

This capability defines how the application SBOM is sourced - its inputs are the Deployment Descriptor
(DD) JSON and the application chart named in the DD, its component list is taken strictly from the DD,
its chart coordinates are resolved for both the offsite and the obfuscated-onsite cases, and the chart is
a hard dependency whose absence fails generation loud.

## ADDED Requirements

### Requirement: Application SBOM sourced from the DD and the application chart

The SBOM generator SHALL build the application SBOM from the DD JSON and the application chart `.tgz`
named in the DD `charts[0]`, downloading the chart in place of the DD zip part and reading the chart only
for resource profiles under `<helm-chart-name>/charts/<entity>/resource-profiles/`, where `<entity>` is
each deployable entity named in the DD (a service or a configuration).

#### Scenario: Chart is the source of resource profiles

- **WHEN** the SBOM generator builds the application SBOM and the DD names an application chart
- **THEN** it downloads the application chart `.tgz` named in `charts[0]`, not the DD zip part, and reads
  resource profiles from `<helm-chart-name>/charts/<entity>/resource-profiles/` in that chart

### Requirement: Component list taken strictly from the DD

The SBOM generator SHALL take the application SBOM component list strictly from the DD services,
configurations, and images, naming each component by its DD name, giving each image-type component the
`application/octet-stream` MIME type, and SHALL perform no chart-tree traversal so that helm libraries
are never added.

#### Scenario: Components are the DD entries only

- **WHEN** the application chart contains helm libraries that the DD does not declare
- **THEN** the application SBOM lists only the DD services, configurations, and images, each named by its
  DD name, each image-type component carries the `application/octet-stream` MIME type, and no helm library
  appears

### Requirement: Chart coordinate resolution across offsite and obfuscated onsite

The SBOM generator SHALL use the DD chart registry and full chart name when the DD carries them, and when
the chart registry is empty SHALL reconstruct the download URL as
`{base}/{helm-chart-name}-{helm-chart-version}.tgz` so the resolved chart is identical to the chart the
deploy side resolves.

#### Scenario: Offsite DD carries chart coordinates

- **WHEN** the DD carries a non-empty chart registry and a full chart name
- **THEN** the generator downloads the chart from those coordinates verbatim

#### Scenario: Obfuscated onsite with a group-repository override

- **WHEN** the DD chart registry is empty and `HELM_MAP_REPOSITORIES` sets a `url` for the chart's group
  repository
- **THEN** the generator downloads the chart from `{override-url}/{helm-chart-name}-{helm-chart-version}.tgz`

#### Scenario: Obfuscated onsite without an override

- **WHEN** the DD chart registry is empty and `HELM_MAP_REPOSITORIES` has no entry for the chart's group
  repository
- **THEN** the generator downloads the chart from
  `{maven-domain}/{group-repository-name}/{helm-chart-name}-{helm-chart-version}.tgz`, where the Maven
  repository domain and the group repository name are the ones the application's registry definition
  declares

### Requirement: HELM_MAP_REPOSITORIES structure

The SBOM generator SHALL read `HELM_MAP_REPOSITORIES` as a cloud end-to-end parameter that is an object,
or a YAML string parsed into an object, whose top-level key is a chart group repository name and whose
value is an object carrying a `url` field, and SHALL use that `url` as the whole base for charts in that
group repository, consulting the parameter only in the obfuscated branch.

#### Scenario: Override replaces the whole base for its group repository

- **WHEN** `HELM_MAP_REPOSITORIES` is set to the following and the DD chart registry is empty for a chart
  whose group repository is `helm-group-a`

  ```yaml
  helm-group-a:
    url: https://charts.example.com/helm-group-a
  ```

- **THEN** the generator uses `https://charts.example.com/helm-group-a` as the whole base for that chart,
  ignoring the Maven repository domain

### Requirement: Application chart is a hard dependency

The SBOM generator SHALL require the application chart and SHALL fail generation loud when the chart
cannot be obtained, with a readable error, rather than producing a partial SBOM.

#### Scenario: DD names no chart

- **WHEN** the DD names no application chart in `charts[0]`
- **THEN** SBOM generation fails with a readable error naming the application

#### Scenario: Named chart cannot be fetched

- **WHEN** the DD names an application chart but the chart `.tgz` cannot be fetched from its resolved
  coordinates
- **THEN** SBOM generation fails with a readable error naming the chart
