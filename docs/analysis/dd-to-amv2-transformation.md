# DD to AMv2 Transformation

- [DD to AMv2 Transformation](#dd-to-amv2-transformation)
  - [Principles](#principles)
  - [DD Assumptions](#dd-assumptions)
  - [AMv2 Assumptions](#amv2-assumptions)
  - [DD to AMv2 Transformation Algorithm](#dd-to-amv2-transformation-algorithm)
    - [Inputs](#inputs)
    - [Output](#output)
    - [Algorithm Steps](#algorithm-steps)
      - [Step 0: Initialize AMv2 Root Structure](#step-0-initialize-amv2-root-structure)
      - [Step 1: Resolve and Download DD](#step-1-resolve-and-download-dd)
      - [Step 2: Create Application Components from Build Config](#step-2-create-application-components-from-build-config)
      - [Step 3: Transform Services](#step-3-transform-services)
      - [Step 4: Transform Charts](#step-4-transform-charts)
      - [Step 5: Extract Additional Components from ZIP](#step-5-extract-additional-components-from-zip)
      - [Step 6: Build Dependencies and Relationships from Build Config](#step-6-build-dependencies-and-relationships-from-build-config)
      - [Step 7: Generate Metadata](#step-7-generate-metadata)
    - [`service` to `application/vnd.docker.image` Mapping](#service-to-applicationvnddockerimage-mapping)
    - [`service` to `application/vnd.nc.helm.chart` Mapping](#service-to-applicationvndnchelmchart-mapping)
    - [`chart` to `application/vnd.nc.helm.chart` Mapping](#chart-to-applicationvndnchelmchart-mapping)
  - [PURL Conversion](#purl-conversion)

This document describes the transformation rules from Deployment Descriptor (DD) to [Application Manifest v2 (AMv2)](/docs/analysis/application-manifest-v2-specification.md).

## Principles

1. Only the following DD sections are processed, others are ignored:
   1. `services`
   2. `charts`
2. Among [Application components](/docs/analysis/application-manifest-v2-specification.md#application-components), only `application/vnd.nc.standalone-runnable` is supported
3. The number, type, and relationships with nested components of Application components in AMv2 are determined from [Build Config](/docs/analysis/application-manifest-build-cli.md#application-manifest-build-config)
4. Relationships between Docker images and Helm charts are determined from Build Config
5. A `DD.services[]` with `image_type = "service"` is transformed into:
   1. One `application/vnd.nc.helm.chart` component
   2. One `application/vnd.docker.image` component
6. A `DD.services[]` with `image_type = "image"` is transformed into:
   1. One `application/vnd.docker.image` component
7. The `DD.charts[]` is transformed into:
    1. One `application/vnd.nc.helm.chart` component
8. All charts obtained from `DD.services[]` become child charts for the chart obtained from `DD.charts[]`
9. Resource profile baselines are extracted from the ZIP part of the application and added as `application/vnd.nc.resource-profile-baseline` child components to the corresponding Helm chart
10. Helm values schema is extracted from the ZIP part of the application and added as `application/vnd.nc.helm.values.schema` child component to the corresponding Helm chart

## DD Assumptions

1. If `DD.charts[]` exists, it contains one or zero elements
2. The chart described in `DD.charts[]` is an umbrella chart (app-chart)
3. All service Helm charts from `DD.services[]` with `image_type = "service"` are sub-charts of this umbrella chart
4. All `DD.services[]` entries contain the following attributes:
   1. `full_image_name`, which conforms to the format `REGISTRY_HOST/NAMESPACE/REPOSITORY:TAG`
5. `DD.charts[]` contains the following attributes:
   1. `full_chart_name`, which conforms to the format `https://REGISTRY_HOST[:PORT]/PATH/IMAGE-VERSION.tgz`

## AMv2 Assumptions

1. AMv2 contains only one `application/vnd.nc.standalone-runnable` component

## DD to AMv2 Transformation Algorithm

### Inputs

1. app:ver of the DD
2. [Application Definition](/docs/envgene-objects.md#application-definition) for the Application
3. [Registry Definition](/docs/envgene-objects.md#registry-definition) for the Application
4. [Build Config](/docs/analysis/application-manifest-build-cli.md#application-manifest-build-config)

### Output

AMv2 JSON document conforming to [JSON schema](/schemas/application-manifest-v2.schema.json)

### Algorithm Steps

#### Step 0: Initialize AMv2 Root Structure

1. Create root AMv2 object
2. Set `$schema` = JSON schema reference (e.g., `"http://json-schema.org/draft-07/schema#"`)
3. Set `bomFormat` = `"CycloneDX"`
4. Set `specVersion` = `"1.6"`
5. Generate `serialNumber` = UUID in format `"urn:uuid:{UUID}"` (RFC 4122)
6. Set `version` = `1`

#### Step 1: Resolve and Download DD

1. Resolve `app:ver` of the DD using Application Definition and Registry Definition to obtain information sufficient for downloading DD JSON and DD ZIP
2. Download DD JSON file
3. Download DD ZIP part

#### Step 2: Create Application Components from Build Config

For the component in Build Config with `mimeType: application/vnd.nc.standalone-runnable`:

1. Create `application/vnd.nc.standalone-runnable` Application component
2. Set `type` = `"application"`
3. Set `mime-type` = `"application/vnd.nc.standalone-runnable"`
4. Generate unique `bom-ref` (e.g., based on component name and type, or UUID)
5. Set `name` = application name from `app:ver` of the DD
6. Set `version` = application version from `app:ver` of the DD
7. Initialize `properties` = empty array `[]`
8. Set `components` = empty array `[]`
9. Add component to root `components` array

#### Step 3: Transform Services

For each `service` in `DD.services[]`:

**If `image_type = "image"`:**

1. Create `application/vnd.docker.image` component
2. Set `type` = `"container"`
3. Set `mime-type` = `"application/vnd.docker.image"`
4. Generate unique `bom-ref`
5. Set `name` = `image_name` from `DD.services[]` entry
6. Set `group` = `docker_repository_name` from `DD.services[]` entry
7. Set `version` = `docker_tag` from `DD.services[]` entry
8. Convert `full_image_name` to PURL using Registry Definition according to [Artifact Reference -> PURL](/docs/analysis/application-manifest-build-cli.md#artifact-reference--purl) process
9. Set `purl` attribute
10. Convert `docker_digest` to hash object if available, otherwise set `hashes` = empty array `[]`
11. Add component to root `components` array

**If `image_type = "service"`:**

1. Create `application/vnd.docker.image` component
   - Set `type` = `"container"`
   - Set `mime-type` = `"application/vnd.docker.image"`
   - Generate unique `bom-ref`
   - Set `name` = `image_name` from `DD.services[]` entry
   - Set `group` = `docker_repository_name` from `DD.services[]` entry
   - Set `version` = `docker_tag` from `DD.services[]` entry
   - Convert `full_image_name` to PURL using Registry Definition according to [Artifact Reference -> PURL](/docs/analysis/application-manifest-build-cli.md#artifact-reference--purl) process
   - Set `purl` attribute
   - Convert `docker_digest` to hash object if available, otherwise set `hashes` = empty array `[]`
   - Add component to root `components` array
2. Create `application/vnd.nc.helm.chart` component
   - Set `type` = `"application"`
   - Set `mime-type` = `"application/vnd.nc.helm.chart"`
   - Generate unique `bom-ref` (e.g., based on chart name and type, or UUID)
   - Set `name` = `service_name` from `DD.services[]` entry
   - Set `version` = `version` from `DD.services[]` entry
   - Initialize `properties` array
   - Add property object to `properties`: `{"name": "isLibrary", "value": false}`
   - Initialize `components` = empty array `[]`
   - Do NOT add service attributes (they are on Docker image only)
   - Add component to root `components` array (if no app-chart exists) or keep reference for Step 4

#### Step 4: Transform Charts

If `DD.charts[]` exists and is not empty:

1. Create `application/vnd.nc.helm.chart` component
2. Set `type` = `"application"`
3. Set `mime-type` = `"application/vnd.nc.helm.chart"`
4. Generate unique `bom-ref`
5. Set `name` = `helm_chart_name` from `DD.charts[]` entry
6. Set `version` = `helm_chart_version` from `DD.charts[]` entry
7. Convert `full_chart_name` to PURL using Registry Definition according to [Artifact Reference -> PURL](/docs/analysis/application-manifest-build-cli.md#artifact-reference--purl) process
8. Set `purl` attribute
9. Set `hashes` = empty array `[]` (if no hash available)
10. Initialize `properties` array
11. Add property object to `properties` array: `{"name": "isLibrary", "value": false}`
12. Add all service Helm charts (from Step 3) as child components in `components` array
13. Add component to root `components` array

#### Step 5: Extract Additional Components from ZIP

**If app-chart exists (from Step 4):**

For the app-chart (umbrella chart) only:

1. Extract Helm values schema from the ZIP part of the application
   - If found, create `application/vnd.nc.helm.values.schema` component:
     - Set `type` = `"data"`
     - Set `mime-type` = `"application/vnd.nc.helm.values.schema"`
     - Generate unique `bom-ref`
     - Set `name` = `"values.schema.json"`
     - Create `data` array with entry:
       - Set `data[0].type` = `"configuration"`
       - Set `data[0].name` = `"values.schema.json"`
       - Set `data[0].contents.attachment.contentType` = `"application/json"`
       - Set `data[0].contents.attachment.encoding` = `"base64"`
       - Set `data[0].contents.attachment.content` = base64-encoded schema content
     - Add as child component to app-chart's `components` array
2. Extract resource profile baselines from the ZIP part of the application
   - For each baseline file found:
     - Create `application/vnd.nc.resource-profile-baseline` component:
       - Set `type` = `"data"`
       - Set `mime-type` = `"application/vnd.nc.resource-profile-baseline"`
       - Generate unique `bom-ref`
       - Set `name` = `"resource-profile-baselines"`
       - Create `data` array with entries for each baseline file:
         - Set `data[n].type` = `"configuration"`
         - Set `data[n].name` = baseline filename (e.g., `"dev.yaml"`, `"prod.yaml"`)
         - Set `data[n].contents.attachment.contentType` = content type (e.g., `"application/yaml"`)
         - Set `data[n].contents.attachment.encoding` = `"base64"`
         - Set `data[n].contents.attachment.content` = base64-encoded baseline content
       - Add as child component to app-chart's `components` array

**If app-chart does NOT exist:**

For each service Helm chart (created in Step 3):

1. Extract Helm values schema from the ZIP part of the application
   - If found, create `application/vnd.nc.helm.values.schema` component:
     - Set `type` = `"data"`
     - Set `mime-type` = `"application/vnd.nc.helm.values.schema"`
     - Generate unique `bom-ref`
     - Set `name` = `"values.schema.json"`
     - Create `data` array with entry:
       - Set `data[0].type` = `"configuration"`
       - Set `data[0].name` = `"values.schema.json"`
       - Set `data[0].contents.attachment.contentType` = `"application/json"`
       - Set `data[0].contents.attachment.encoding` = `"base64"`
       - Set `data[0].contents.attachment.content` = base64-encoded schema content
     - Add as child component to corresponding service Helm chart's `components` array
2. Extract resource profile baselines from the ZIP part of the application
   - For each baseline file found:
     - Create `application/vnd.nc.resource-profile-baseline` component:
       - Set `type` = `"data"`
       - Set `mime-type` = `"application/vnd.nc.resource-profile-baseline"`
       - Generate unique `bom-ref`
       - Set `name` = `"resource-profile-baselines"`
       - Create `data` array with entries for each baseline file:
         - Set `data[n].type` = `"configuration"`
         - Set `data[n].name` = baseline filename (e.g., `"dev.yaml"`, `"prod.yaml"`)
         - Set `data[n].contents.attachment.contentType` = content type (e.g., `"application/yaml"`)
         - Set `data[n].contents.attachment.encoding` = `"base64"`
         - Set `data[n].contents.attachment.content` = base64-encoded baseline content
       - Add as child component to corresponding service Helm chart's `components` array

#### Step 6: Build Dependencies and Relationships from Build Config

1. For each component in Build Config:
   - Find corresponding component in AMv2 by `name` and `mimeType`
   - For each `dependsOn` entry in Build Config:
     - Find dependency component by `name` and `mimeType`
     - Add dependency's `bom-ref` to `dependsOn` array
     - If `valuesPathPrefix` is specified in `dependsOn`, add to `helm.values.artifactMappings` property

2. For Helm charts with `helm.values.artifactMappings`:
   - Map Docker image `bom-ref` to `valuesPathPrefix` from Build Config
   - Add property: `{"name": "helm.values.artifactMappings", "value": {...}}` to Helm chart's `properties` array

3. For Application components (`application/vnd.nc.standalone-runnable`):
   - Based on `dependsOn` in Build Config, establish dependency relationships
   - All dependencies are expressed through the root `dependencies` array ONLY
   - The `components` array of standalone-runnable MUST remain empty `[]`
   - Standalone-runnable `dependsOn` app-chart (if exists) or all service Helm charts (if no app-chart)
   - Standalone-runnable `dependsOn` all Docker images that are not associated with service Helm charts

4. Build root-level dependencies array:
   - For each component that has dependencies:
     - Create dependency entry: `{"ref": component.bom-ref, "dependsOn": [dependency1.bom-ref, dependency2.bom-ref, ...]}`
     - Add to root `dependencies` array

#### Step 7: Generate Metadata

1. Parse `app:ver` of the DD to extract application name and version
2. Set `metadata.timestamp` = current time (ISO 8601)
3. Create `metadata.component` object:
   - Set `metadata.component.type` = `"application"`
   - Set `metadata.component.mime-type` = `"application/vnd.nc.application"`
   - Generate unique `metadata.component.bom-ref`
   - Set `metadata.component.name` = application name from `app:ver` of the DD
   - Set `metadata.component.version` = application version from `app:ver` of the DD
4. Create `metadata.tools` object:
   - Add tool component: `{"type": "application", "name": "tool-name", "version": "tool-version"}`
   - Add to `metadata.tools.components` array

### `service` to `application/vnd.docker.image` Mapping

| DD `service` attribute       | AMv2      | Notes                                           |
|------------------------------|-----------|-------------------------------------------------|
| `artifacts`                  | N/A       | **TBD**                                         |
| `build_id_dtrust`            | N/A       | Not used in CM and deployment cases             |
| `deploy_param`               | N/A       | **TBD**                                         |
| `docker_digest`              | `hashes`  | Converted to hash object if available           |
| `docker_registry`            | N/A       | Not used in CM and deployment cases             |
| `docker_repository_name`     | `group`   |                                                 |
| `docker_tag`                 | `version` |                                                 |
| `full_image_name`            | `purl`    | Converted to PURL using Registry Definition     |
| `git_branch`                 | N/A       | Not used in CM and deployment cases             |
| `git_revision`               | N/A       | Not used in CM and deployment cases             |
| `git_url`                    | N/A       | Not used in CM and deployment cases             |
| `image_name`                 | `name`    |                                                 |
| `image_type`                 | N/A       | Not used in CM and deployment cases             |
| `includeFrom`                | N/A       | Not used in CM and deployment cases             |
| `promote_artifacts`          | N/A       | Not used in CM and deployment cases             |
| `qualifier`                  | N/A       | **TBD**                                         |
| `service_name`               | N/A       | Not used in DD in case of `image_type: image`   |
| `version`                    | N/A       | Not used in DD in case of `image_type: image`   |

Where AMv2 shows N/A, that attribute is ignored. All other service attributes are ignored.

### `service` to `application/vnd.nc.helm.chart` Mapping

| DD `service` attribute       | AMv2      | Notes                                           |
|------------------------------|-----------|-------------------------------------------------|
| `artifacts`                  | N/A       | **TBD**                                         |
| `build_id_dtrust`            | N/A       | Not used in CM and deployment cases             |
| `deploy_param`               | N/A       | **TBD**                                         |
| `docker_digest`              | N/A       | Not used for `application/vnd.nc.helm.chart`    |
| `docker_registry`            | N/A       | Not used for `application/vnd.nc.helm.chart`    |
| `docker_repository_name`     | N/A       | Not used for `application/vnd.nc.helm.chart`    |
| `docker_tag`                 | N/A       | Not used for `application/vnd.nc.helm.chart`    |
| `full_image_name`            | N/A       | Not used for `application/vnd.nc.helm.chart`    |
| `git_branch`                 | N/A       | Not used in CM and deployment cases             |
| `git_revision`               | N/A       | Not used in CM and deployment cases             |
| `git_url`                    | N/A       | Not used in CM and deployment cases             |
| `image_name`                 | N/A       | Not used in DD in case of `image_type: service` |
| `image_type`                 | N/A       | Not used in CM and deployment cases             |
| `includeFrom`                | N/A       | Not used in CM and deployment cases             |
| `promote_artifacts`          | N/A       | Not used in CM and deployment cases             |
| `qualifier`                  | N/A       | **TBD**                                         |
| `service_name`               | `name`    |                                                 |
| `version`                    | `version` |                                                 |

Where AMv2 shows N/A, that attribute is ignored. All other service attributes are ignored.

### `chart` to `application/vnd.nc.helm.chart` Mapping

| DD `chart` attribute         | AMv2      | Notes                                           |
|------------------------------|-----------|-------------------------------------------------|
| `full_chart_name`            | `purl`    | Converted to PURL using Registry Definition     |
| `git_branch`                 | N/A       | Not used in CM and deployment cases             |
| `git_revision`               | N/A       | Not used in CM and deployment cases             |
| `git_url`                    | N/A       | Not used in CM and deployment cases             |
| `helm_chart_name`            | `name`    |                                                 |
| `helm_chart_version`         | `version` |                                                 |
| `helm_registry`              | N/A       | Not used in CM and deployment cases             |
| `promote_artifacts`          | N/A       | Not used in CM and deployment cases             |
| `qualifier`                  | N/A       | May be added in the future                      |
| `type`                       | N/A       | Not used in CM and deployment cases             |
| `version`                    | N/A       | Not used in CM and deployment cases             |

Where AMv2 shows N/A, that attribute is ignored. All other chart attributes are ignored.

## PURL Conversion

DD artifact references are converted to PURL using the [Artifact Reference → PURL](/docs/analysis/application-manifest-build-cli.md#artifact-reference--purl) algorithm.

**DD to Artifact Reference Mapping:**

| DD Field          | Maps to Artifact Reference                                             |
|-------------------|------------------------------------------------------------------------|
| `full_image_name` | Docker image reference: `{REGISTRY}/{NAMESPACE}/{IMAGE}:{TAG}`         |
| `full_chart_name` | Helm chart reference: `https://{REGISTRY}/{PATH}/{NAME}-{VERSION}.tgz` |

**Conversion Process:**

```text
DD field → Artifact Reference → [Official Algorithm] → PURL with registry_name
```

**Examples:**

Docker:

```text
full_image_name: "artifactorycn.netcracker.com:17004/cloud-core/image:build2"
  → Apply algorithm with Registry Definition
  → pkg:docker/cloud-core/image@build2?registry_name=artifactory-netcracker
```

Helm (File registry):

```text
full_chart_name: "https://artifactorycn.netcracker.com/nc.helm.charts/chart-1.0.0.tgz"
  → Apply algorithm with Registry Definition
  → pkg:helm/chart@1.0.0?registry_name=artifactory-netcracker
```

**Note:** Registry Definition is required for `registry_name` lookup.
