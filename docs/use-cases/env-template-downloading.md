# Environment Template Downloading Use Cases

- [Environment Template Downloading Use Cases](#environment-template-downloading-use-cases)
  - [Template Artifact Downloading Details](#template-artifact-downloading-details)
  - [Use Cases](#use-cases)

## Template Artifact Downloading Details

The process for downloading environment template artifacts in EnvGene can be categorized along four primary axes:

1. **Version Type:** Explicit version or `SNAPSHOT` version (latest available)

2. **Artifact Coordinate Notation:** Either GAV (Group, Artifact, Version) or app:ver notation.
  
    Template artifact can be specified in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) with:

    1. app:ver notation. To use this, [Artifact Definition](/docs/envgene-objects.md#artifact-definition) is needed.

        Example of `env_definition.yml`:

        ```yaml

        envTemplate:
          artifact: string
        ```

    2. GAV notation. To use this, [registry.yaml](/docs/envgene-configs.md#registryyml) is needed.

        Example of `env_definition.yml`:

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

3. **Artifact Source Registry:** Artifact repositories supported include:

    1. Artifactory
    2. Nexus
    3. AWS CodeArtifact
    4. Azure Artifacts
    5. GCP Artifact Registry

    The GAV form is limited to Artifactory/Nexus, while app:ver supports all.

4. **Artifact Content Type:** Either a ZIP archive or Delivery Unit (DU)

    > [!NOTE] The core EnvGene does not have built-in support for Delivery Unit (DU) processing; this is provided as an extension point.

## Use Cases

The use cases below enumerate combinations of these axes that EnvGene supports:

| Use Case | Coordinate Notation | Version Type | Registry Scope         | Artifact Type | Prerequisites                                                    | Result                                                                                                         |
|:--------:|:-------------------:|:------------:|:----------------------:|:-------------:|:-----------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------|
| UC-1-1   | GAV                 | Specific     | Artifactory/Nexus      | ZIP           | `registry.yml` must include registry configuration               | Retrieve a ZIP artifact by explicit GAV coordinates and fixed version from Artifactory or Nexus.               |
| UC-1-2   | GAV                 | Specific     | Artifactory/Nexus      | DU            | `registry.yml` must include registry configuration               | Retrieve a DU artifact by explicit GAV coordinates and fixed version from Artifactory or Nexus.                |
| UC-1-3   | GAV                 | SNAPSHOT     | Artifactory/Nexus      | ZIP           | `registry.yml` must include registry configuration               | Retrieve the latest available ZIP artifact by GAV coordinates with SNAPSHOT version from Artifactory or Nexus. |
| UC-1-4   | GAV                 | SNAPSHOT     | Artifactory/Nexus      | DU            | `registry.yml` must include registry configuration               | Retrieve the latest available DU artifact by GAV coordinates with SNAPSHOT version from Artifactory or Nexus.  |
| UC-2-1   | app:ver             | Specific     | Any supported registry | ZIP           | Artifact Definition must exist for the specified app:ver         | Retrieve a ZIP artifact by explicit app:ver notation and fixed version from any supported registry.            |
| UC-2-2   | app:ver             | Specific     | Any supported registry | DU            | Artifact Definition must exist for the specified app:ver         | Retrieve a DU artifact by explicit app:ver notation and fixed version from any supported registry.             |
| UC-2-3   | app:ver             | SNAPSHOT     | Any supported registry | ZIP           | Artifact Definition must exist for the specified app:ver         | Retrieve the latest available ZIP artifact by app:ver notation with SNAPSHOT version from any registry.        |
| UC-2-4   | app:ver             | SNAPSHOT     | Any supported registry | DU            | Artifact Definition must exist for the specified app:ver         | Retrieve the latest available DU artifact by app:ver notation with SNAPSHOT version from any registry.         |
