# EnvGene Artifacts Naming Conventions

- [EnvGene Artifacts Naming Conventions](#envgene-artifacts-naming-conventions)
  - [Artifact Names](#artifact-names)
  - [PyPI packages](#pypi-packages)
  - [GitHub Actions artifacts](#github-actions-artifacts)
  - [Artifact Versions](#artifact-versions)
    - [Release Versions](#release-versions)
    - [Non-Release Versions](#non-release-versions)

## Artifact Names

Artifact names (artifact ID for Maven artifacts, Docker image names, PyPI distribution names, etc.) match
the component name:

- `qubership-envgene`
- `qubership-pipegene`
- `qubership-effective-set-generator`
- `qubership-instance-repo-pipeline`
- `qubership-external-cred-provision`

The installed CLI command for `qubership-external-cred-provision` is `external-cred-provision` (shorter
than the PyPI distribution name).

## PyPI packages

EnvGene publishes the External Credentials provisioning CLI to the public PyPI index.

| Field             | Value                               |
|-------------------|-------------------------------------|
| Distribution name | `qubership-external-cred-provision` |
| CLI command       | `external-cred-provision`           |
| Source directory  | `/python/external-cred-provision/`  |

Published with [External Credentials CLI PyPI publish workflow](/docs/dev/external-cred-provision-pypi-publish-workflow.md).

Release versions use strict SemVer `X.Y.Z` with no `v` prefix and no prerelease suffix. That differs from
Docker image tags, which use a `v` prefix.

Install a released version:

```bash
pip install qubership-external-cred-provision==1.2.3
```

## GitHub Actions artifacts

Workflow-built artifacts follow `{distribution-name}-dist-{version}`.

Example for the External Credentials CLI publish workflow:

```text
qubership-external-cred-provision-dist-1.2.3
```

The artifact contains the wheel and sdist built for that release version. See
[External Credentials CLI PyPI publish workflow](/docs/dev/external-cred-provision-pypi-publish-workflow.md) for build-only vs publish mode.

## Artifact Versions

### Release Versions

Format: `v<Major>.<Minor>.<Patch>` ([Semantic Versioning](https://semver.org/)) for Docker images. PyPI and Maven use the numeric triplet without a `v` prefix.

Example:

```yaml
# Docker
qubership-envgene:v1.2.3
# Maven  (GAV coordinates: GroupId:ArtifactId:Version)
org.qubership:envgene-template:1.2.3
# PyPI
qubership-external-cred-provision==1.2.3
```

### Non-Release Versions

Format: `<branch-name>-<timestamp>`:

- Replace `[/#@ ]` with `_` in branch names (for example `feature/#123` → `feature__123`)
- Timestamp in UTC (`%Y%m%d_%H%M%S`) from build engine

Example:

```yaml
# Original branch: `feature/#123-aws` →
qubership-envgene:feature__123-aws-20240405_142030
# Maven
org.qubership:envgene-template:main-20240405_142030
```

> [!NOTE]
> When developing EnvGene extensions, it is strongly recommended to use the same naming conventions.
