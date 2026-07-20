# Artifact resolution

- [Artifact resolution](#artifact-resolution)
  - [Version forms](#version-forms)
  - [Processing](#processing)
    - [Traditional registries](#traditional-registries)
    - [Public cloud registries](#public-cloud-registries)
    - [Version resolution](#version-resolution)

EnvGene resolves and downloads Maven artifacts in two flows:

1. Download an environment template.
2. Download an application artifact.

Both begin the same way. Each resolves and downloads a Deployment Descriptor (DD), then fetches the payload.
This document covers the shared DD-resolution logic.

The DD is a JSON artifact addressed by the artifact coordinates (`groupId:artifactId:version`). The
coordinates and registry endpoint and credentials come from objects that differs by flow:

1. [Artifact Definition](/docs/features/app-reg-defs.md) for the environment template
2. [Application Definition](/docs/features/app-reg-defs.md) and [Registry Definition](/docs/features/app-reg-defs.md)
   for the application artifact

## Version forms

The `version` in the coordinates takes one of two forms:

- **Snapshot version.** Ends with `-SNAPSHOT`. It denotes the latest non-released build, not a specific one.

  For example: `1.0.0-SNAPSHOT` or `20260720.122600-SNAPSHOT`.

- **Fixed version.** Has no `-SNAPSHOT` suffix. It names one exact artifact, which can be a release or a
  pinned snapshot build.

  For example: `1.0.0` or `1.0.0-20260720.122600-1`.

Maven publishes each snapshot build under a unique timestamped version, for example `1.0.0-20260720.122600-1`,
inside the `1.0.0-SNAPSHOT/` folder. The version-level `maven-metadata.xml` maps `1.0.0-SNAPSHOT` to the
latest build. A pinned snapshot build is a fixed version that names one such build.

## Processing

EnvGene searches the selected repositories concurrently, and the first to return the DD wins. If none returns
the DD, resolution fails.

The registry provider determines which repositories the search probes. Registry Definition v2 declares the
provider. Registry Definition v1 has no provider and always uses the traditional model.

### Traditional registries

Nexus and Artifactory. `repositoryDomainName` is a base URL, and `mavenConfig` names the candidate
repositories: `targetSnapshot`, `targetStaging`, `targetRelease`, `snapshotGroup`, and `releaseGroup`. The
version form selects which the search probes:

- For a snapshot version - `targetSnapshot`, `targetStaging`, and `snapshotGroup`.
- For a fixed version - all candidate repositories.

### Public cloud registries

AWS, GCP, and Azure. `repositoryDomainName` addresses one repository that holds every artifact, with no
snapshot, staging, release, or group separation. `mavenConfig` sets no candidate repositories, and EnvGene
searches that single repository.

### Version resolution

Within each searched repository EnvGene builds the URL from the version form:

- **Snapshot version.** EnvGene reads `maven-metadata.xml` to resolve `-SNAPSHOT` to the latest build. The
  metadata records the latest build per artifact type, so EnvGene picks the one for the DD and requests it.
- **Fixed version.** EnvGene requests the file directly.
