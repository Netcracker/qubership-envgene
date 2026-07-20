# Artifact resolution

- [Artifact resolution](#artifact-resolution)
  - [Version forms](#version-forms)
  - [Processing](#processing)
    - [AWS and GCP registries](#aws-and-gcp-registries)
    - [Version resolution](#version-resolution)

EnvGene resolves and downloads Maven artifacts in two flows:

1. Download an environment template.
2. Download an application artifact.

Both begin the same way. Each resolves and downloads a Deployment Descriptor (DD), then fetches the payload.
This document covers the shared DD-resolution logic.

The DD is a JSON artifact addressed by the artifact coordinates (`groupId:artifactId:version`). The
coordinates come from a definition object that differs by flow:

1. [Artifact Definition](/docs/features/app-reg-defs.md) for the environment template
2. [Application Definition](/docs/features/app-reg-defs.md) for the application artifact

Both reference a [Registry Definition](/docs/features/app-reg-defs.md), which declares the repositories to
search.

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

EnvGene searches the candidate repositories concurrently, and the first to return the DD wins. If none returns
the DD, resolution fails. The version form does not affect which repositories are searched.

The candidate repositories come from the Registry Definition `mavenConfig`: `targetSnapshot`, `targetStaging`,
`targetRelease`, and `snapshotGroup`. The Nexus, Artifactory, and Azure providers and all Registry Definition
v1 registries use them. AWS and GCP are the exception.

### AWS and GCP registries

For the AWS and GCP providers, `repositoryDomainName` addresses one repository that holds every artifact, so
`mavenConfig` sets no candidate repositories and EnvGene searches that single repository. The provider is
declared in Registry Definition v2 `authConfig`.

### Version resolution

Within each searched repository EnvGene builds the URL from the version form:

- **Snapshot version.** EnvGene reads `maven-metadata.xml` to resolve `-SNAPSHOT` to the latest build. The
  metadata records the latest build per artifact type, so EnvGene picks the one for the DD and requests it.
- **Fixed version.** EnvGene requests the file directly.
