# Environment Template Downloading

- [Environment Template Downloading](#environment-template-downloading)
  - [Template artifact download aspects](#template-artifact-download-aspects)
  - [Use Cases](#use-cases)

## Template artifact download aspects

The process for downloading environment template artifacts in EnvGene can be categorized along four primary axes:

1. **Version Type:** Explicit version (immutable) or `SNAPSHOT` version (latest available)

2. **Artifact Coordinate Notation:** Either `GAV` (Group, Artifact, Version) or `app:ver` notation.
  
    Template artifact can be specified in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) with:

    1. `app:ver` notation. To use this, [Artifact Definition](/docs/envgene-objects.md#artifact-definition) is needed.

        ```yaml
        envTemplate:
          artifact: string
        ```

    2. `GAV` notation. To use this, [registry.yaml](/docs/envgene-configs.md#registryyml) is needed.

        ```yaml
        templateArtifact:
          registry: string
          repository: string
          templateRepository: string
          artifact:
            group_id: string
            artifact_id: string
            version: string
        ```

3. **Artifact Source Registry:** Artifact repositories supported include Artifactory, Nexus, AWS CodeArtifact, Azure Artifacts, and GCP Artifact Registry. The `GAV` form is limited to Artifactory/Nexus, while `app:ver` supports all.

4. **Artifact Content Type:** Either a standard template ZIP or a DD.

## Use Cases

The use cases below enumerate combinations of these axes that EnvGene is support:

| # | Coordinate Notation | Version Type | Registry Scope         | Artifact Type | Description                                                                                 |
|---|---------------------|--------------|------------------------|---------------|---------------------------------------------------------------------------------------------|
| 1 | GAV                 | Specific     | Artifactory/Nexus      | ZIP           | Retrieve a ZIP artifact by explicit GAV coordinates and fixed version from Artifactory or Nexus.         |
| 2 | GAV                 | Specific     | Artifactory/Nexus      | DD            | Retrieve a DD artifact by explicit GAV coordinates and fixed version from Artifactory or Nexus.           |
| 3 | GAV                 | SNAPSHOT     | Artifactory/Nexus      | ZIP           | Retrieve the latest available ZIP artifact by GAV coordinates with SNAPSHOT version from Artifactory or Nexus. |
| 4 | GAV                 | SNAPSHOT     | Artifactory/Nexus      | DD            | Retrieve the latest available DD artifact by GAV coordinates with SNAPSHOT version from Artifactory or Nexus.   |
| 5 | app:ver             | Specific     | Any supported registry | ZIP           | Retrieve a ZIP artifact by explicit `app:ver` notation and fixed version from any supported registry.      |
| 6 | app:ver             | Specific     | Any supported registry | DD            | Retrieve a DD artifact by explicit `app:ver` notation and fixed version from any supported registry.        |
| 7 | app:ver             | SNAPSHOT     | Any supported registry | ZIP           | Retrieve the latest available ZIP artifact by `app:ver` notation with SNAPSHOT version from any registry.   |
| 8 | app:ver             | SNAPSHOT     | Any supported registry | DD            | Retrieve the latest available DD artifact by `app:ver` notation with SNAPSHOT version from any registry.    |
