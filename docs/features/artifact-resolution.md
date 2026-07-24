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
coordinates and registry endpoint and credentials come from objects that differ by flow:

1. [Artifact Definition](/docs/features/app-reg-defs.md) for the environment template
2. [Application Definition](/docs/features/app-reg-defs.md) and [Registry Definition](/docs/features/app-reg-defs.md)
   for the application artifact

## Version forms

The `version` in the coordinates takes one of three forms:

- **Non-unique snapshot version.** Ends with `-SNAPSHOT`. It denotes the latest snapshot build, not a specific
  one. For example: `1.0.0-SNAPSHOT`.

- **Unique snapshot version.** A snapshot build published under its timestamped name
  `<base>-<timestamp>-<buildNumber>`, matching `^(.*)-\d{8}\.\d{6}-\d+$`. It names one exact snapshot build.
  For example: `1.0.0-20260720.122600-1`.

- **Release version.** Any version that is neither of the above. It names one exact released artifact. For
  example: `1.0.0`.

Maven publishes each snapshot build under its unique timestamped name inside the `<base>-SNAPSHOT/` folder.

## Processing

EnvGene searches the selected repositories concurrently, and the first to return the DD wins. If none returns
the DD, resolution fails.

The registry provider selects the repository model, traditional or public cloud. Registry Definition v2
declares the provider. Registry Definition v1 has no provider and always uses the traditional model.

### Traditional registries

Nexus and Artifactory. `repositoryDomainName` is a base URL, and `mavenConfig` names the candidate
repositories: `targetSnapshot`, `targetStaging`, `targetRelease`, `snapshotGroup`, and `releaseGroup`. The
search probes all of them.

### Public cloud registries

AWS, GCP, and Azure. `repositoryDomainName` addresses one repository that holds every artifact, with no
snapshot, staging, release, or group separation. `mavenConfig` sets no candidate repositories, and EnvGene
searches that single repository.

### Version resolution

The version form sets the storage folder and how EnvGene picks the build within each searched repository:

- **Non-unique snapshot version.** The folder is the version itself. EnvGene reads that folder's
  `maven-metadata.xml` to resolve `-SNAPSHOT` to the latest build and requests it.
- **Unique snapshot version.** The folder is `<base>-SNAPSHOT`, derived by replacing the
  `-<timestamp>-<buildNumber>` suffix with `-SNAPSHOT`. The build is already named, so EnvGene requests it
  directly without reading metadata.
- **Release version.** The folder is the version itself, and EnvGene requests the file directly.
