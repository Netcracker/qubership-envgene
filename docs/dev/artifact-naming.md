# EnvGene Artifacts Naming Conventions

- [EnvGene Artifacts Naming Conventions](#envgene-artifacts-naming-conventions)
  - [Artifact Names](#artifact-names)
  - [Artifact Versions](#artifact-versions)
    - [Release Versions](#release-versions)
    - [Non-Release Versions](#non-release-versions)

## Artifact Names

Artifact names (artifact ID for Maven artifacts, Docker image names, etc.) match the component name:

- `qubership-envgene`
- `qubership-pipegene`
- `qubership-effective-set-generator`
- `qubership-instance-repo-pipeline`

## Artifact Versions

### Release Versions

Format: `v<Major>.<Minor>.<Patch>` ([Semantic Versioning](https://semver.org/))

Example:

```yaml
# Docker
qubership-envgene:v1.2.3
# Maven  (GAV coordinates: GroupId:ArtifactId:Version)
org.qubership:envgene-template:1.2.3
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

> **Note:**
> When developing EnvGene extensions, it's strongly recommended to use the same naming conventions.
