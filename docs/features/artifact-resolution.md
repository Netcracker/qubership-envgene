# Artifact resolution

- [Artifact resolution](#artifact-resolution)
  - [Version forms](#version-forms)
  - [Processing](#processing)
    - [Traditional registries](#traditional-registries)
    - [Public cloud registries](#public-cloud-registries)

EnvGene resolves and downloads Maven artifacts in two flows:

1. Download an environment template.
2. Download an application artifact.

Both begin the same way. Each resolves and downloads a Deployment Descriptor (DD), then fetches the payload.
This document covers the shared DD-resolution logic.

The DD is a JSON artifact addressed by the artifact coordinates (`groupId:artifactId:version`). The
coordinates and registry endpoint and credentials come from objects that differ by flow:

1. [Artifact Definition](/docs/features/app-reg-defs.md) for the environment template
2. [Application Definition](/docs/features/app-reg-defs.md) and [Registry Definition](/docs/features/app-reg-defs.md)
   for the application artifact

## Version forms

The `version` in the coordinates takes one of three forms:

- **Non-unique snapshot version.** Ends with `-SNAPSHOT`. It denotes the latest snapshot build, not a specific
  one. For example: `1.0.0-SNAPSHOT`.

- **Unique snapshot version.** A build published under its timestamped name `<base>-<timestamp>-<buildNumber>`,
  matching `^(.*)-\d{8}\.\d{6}-\d+$`. It names one exact build. For example: `1.0.0-20260720.122600-1`.

- **Release version.** Any version that is neither of the above. It names one exact released artifact. For
  example: `1.0.0`.

These forms classify the version string, not the artifact behind it. The unique snapshot form is ambiguous:
the same string can name a snapshot build or a promoted release that kept the timestamped name. Resolution
therefore treats it as both.

## Processing

EnvGene searches the selected repositories concurrently, and the first to return the DD wins. If none returns
the DD, resolution fails.

The registry provider selects the repository model, traditional or public cloud. Registry Definition v2
declares the provider. Registry Definition v1 has no provider and always uses the traditional model. The model
sets where each version form is looked up.

### Traditional registries

Nexus and Artifactory. `repositoryDomainName` is a base URL, and `mavenConfig` names the candidate
repositories. The snapshot repositories are `targetSnapshot`, `targetStaging`, and `snapshotGroup`. The
release repositories are `targetRelease` and `releaseGroup`. Each version form sets the folder and the
repositories to search:

- **Non-unique snapshot version.** The folder is `<version>` (ending in `-SNAPSHOT`). EnvGene reads that
  folder's `maven-metadata.xml` to resolve `-SNAPSHOT` to the latest build and requests it from the snapshot
  repositories.
- **Unique snapshot version.** EnvGene resolves it as both a snapshot and a release. As a snapshot, the folder
  is `<base>-SNAPSHOT` (the `-<timestamp>-<buildNumber>` suffix replaced with `-SNAPSHOT`), requested directly
  from the snapshot repositories. As a release, the folder is `<version>`, requested directly from the release
  repositories.
- **Release version.** The folder is `<version>`, requested directly from the release repositories.

### Public cloud registries

AWS, GCP, and Azure. `repositoryDomainName` addresses one repository that holds every artifact, with no
snapshot, staging, release, or group separation. `mavenConfig` names no candidate repositories. Each version
form sets the folder to request from that single repository:

- **Non-unique snapshot version.** The folder is `<version>` (ending in `-SNAPSHOT`). EnvGene reads that
  folder's `maven-metadata.xml` to resolve `-SNAPSHOT` to the latest build and requests it.
- **Unique snapshot version.** EnvGene tries both folders, each requested directly: `<base>-SNAPSHOT` (the
  `-<timestamp>-<buildNumber>` suffix replaced with `-SNAPSHOT`) and `<version>`.
- **Release version.** The folder is `<version>`, requested directly.
