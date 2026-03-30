# Template placeholders

Replace each `{{ NAME }}` after copying a `.template` file. Values must stay consistent across Application SBOM, `sd.yaml`, and Solution SBOM for the same environment.

| Placeholder                         | Example                                      | Description                                        |
|-------------------------------------|----------------------------------------------|----------------------------------------------------|
| `SBOM_SERIAL_NUMBER_URN_UUID`       | `urn:uuid:8f4c2e10-9a3b-4d1e-8c7f-0a1b2c3d4e50` | Unique BOM serial (RFC 4122 UUID in `urn:uuid:`) |
| `SOLUTION_SBOM_SERIAL_NUMBER_URN_UUID` | `urn:uuid:7e3b1a90-5c2d-4e8f-9a0b-1c2d3e4f5060` | Separate serial for Solution SBOM               |
| `ISO_8601_TIMESTAMP`                | `2026-03-30T12:00:00Z`                       | BOM timestamp                                      |
| `APPLICATION_NAME`                  | `postgres`                                   | Name before `:` in SD `applications[].version`     |
| `APPLICATION_VERSION`               | `16.4-oss-1`                                 | Version after `:` in SD                            |
| `DEPLOY_POSTFIX`                    | `pg`                                         | Namespace role in your instance                    |
| `SBOM_GENERATOR_TOOL_VERSION`       | `0.1.0`                                      | Tool version in metadata                           |
| `BOM_REF_*`                         | `BomRef.oss.meta.postgres.0001`              | Unique `bom-ref` values                            |
| `MAVEN_STYLE_GROUP_ID`              | `org.example.oss`                            | Deployment descriptor Maven-style group              |
| `DEPLOYMENT_DESCRIPTOR_NAME`        | `postgres-application`                       | Deployment descriptor artifact name                |
| `SERVICE_NAME`                      | `postgres`                                   | Top-level service component name                   |
| `DOCKER_REGISTRY_HOST`              | `docker.io`                                  | Registry for `docker_registry` property            |
| `FULL_IMAGE_NAME`                   | `docker.io/library/postgres:16-alpine`       | Value for `full_image_name`                        |
| `SOURCE_REPO_URL`                   | `https://github.com/docker-library/postgres` | Upstream source URL                                |
| `GIT_BRANCH`                        | `16`                                         | Optional branch label                              |
| `GIT_REVISION`                      | ``                                           | Optional commit (empty if unknown)                 |
| `IMAGE_GROUP`                       | `library`                                    | Docker image namespace                             |
| `IMAGE_NAME`                        | `postgres`                                   | Docker image name                                  |
| `IMAGE_TAG`                         | `16-alpine`                                  | Docker image tag                                   |
| `IMAGE_DIGEST_SHA256_HEX_64`        | (64 hex chars)                               | SHA-256 digest of the deployed image               |
| `IMAGE_PURL` (optional standalone)  | (see docker purl below)                      | Use full purl including `registry_id` / `repository_id` |
| `REGISTRY_ID`                       | `registry-1`                                 | Key in `configuration/registry.yml`                |
| `MAVEN_REPOSITORY_ID`               | `targetRelease`                              | Maps to Maven repo in registry config                |
| `DOCKER_REPOSITORY_ID`              | `releaseUri`                                 | Maps to Docker repo URI in registry config           |
| `BOM_REF_HELM_CHART`                | `BomRef.oss.chart.postgres.0006`             | Helm chart component (`application/vnd.qubership.app.chart`) |
| `RESOURCE_PROFILE_DEV_JSON_BASE64`  | `e30=`                                       | Base64 of `{}` for minimal `dev.json`              |
| `APPLICATION_SBOM_FILENAME`         | `postgres-16.4-oss-1.sbom.json`              | File name for `file://`; equals SD version with `:` replaced by `-`, plus `.sbom.json` |

## File naming

Instance repositories often store Application SBOMs as:

```text
sboms/<application-name>/<sd-version-with-colons-as-dashes>.sbom.json
```

Example: SD entry `postgres:16.4-oss-1` maps to `sboms/postgres/postgres-16.4-oss-1.sbom.json`.

Keep `file://` in Solution SBOM aligned with that file name.
