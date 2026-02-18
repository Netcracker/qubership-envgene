# AMv2 to DD Transformation

- [AMv2 to DD Transformation](#amv2-to-dd-transformation)
  - [Principles](#principles)
  - [AMv2 Assumptions](#amv2-assumptions)
  - [AMv2 to DD Transformation Algorithm](#amv2-to-dd-transformation-algorithm)
    - [Inputs](#inputs)
    - [Output](#output)
    - [Algorithm Steps](#algorithm-steps)
      - [Step 1: Identify Service Charts and Associated Docker Images](#step-1-identify-service-charts-and-associated-docker-images)
      - [Step 2: Extract Services from Docker Images](#step-2-extract-services-from-docker-images)
      - [Step 3: Extract App-Chart](#step-3-extract-app-chart)
      - [Step 4: Build DD Structure](#step-4-build-dd-structure)
    - [PURL Conversion](#purl-conversion)

This document describes the transformation rules from [Application Manifest v2 (AMv2)](/docs/analysis/application-manifest-v2-specification.md) to Deployment Descriptor (DD).

## Principles

1. AMv2 is the **source of truth** - DD is reconstructed from AMv2 structure and values
2. `application/vnd.docker.image` components are transformed into `DD.services[]` entries:
   - Standalone Docker images (no associated Helm chart) → `image_type = "image"`
   - Docker images with associated service charts → `image_type = "service"`
3. `application/vnd.nc.helm.chart` components are transformed into:
   - `DD.charts[]` entry if it's an app-chart (root-level Helm chart with nested service charts)
   - Part of `DD.services[]` entry if it's a service chart (nested in app-chart)
4. Only components that can be represented in DD are processed (others are ignored)
5. PURL values are converted back to DD artifact reference format using Registry Definition

## AMv2 Assumptions

1. AMv2 contains only one `application/vnd.nc.standalone-runnable` component
2. All `application/vnd.docker.image` components are at root level
3. App-chart is identified as root-level `application/vnd.nc.helm.chart` with nested components
4. Service charts are nested inside app-chart `components` array

## AMv2 to DD Transformation Algorithm

### Inputs

1. **AMv2 JSON document** conforming to [JSON schema](/schemas/application-manifest-v2.schema.json)
2. **Registry Definition** (required for PURL → DD artifact reference conversion)

### Output

1. **DD JSON document** with populated `services[]` and `charts[]` sections

### Algorithm Steps

#### Step 1: Identify Service Charts and Associated Docker Images

1. Find app-chart component:
   - Locate `application/vnd.nc.helm.chart` at root level with non-empty `components` array
2. For each service chart in app-chart `components` array:
   - Extract service chart `bom-ref`
   - Find `nc:helm.values.artifactMappings` property
   - Extract Docker image `bom-ref` from artifact mappings
   - Store mapping: `service_chart_ref → docker_image_ref`
3. Build set of Docker images with associated service charts

#### Step 2: Extract Services from Docker Images

For each `application/vnd.docker.image` component at root level:

**If Docker image has NO associated service chart (standalone image):**

1. Create `DD.services[]` entry with `image_type = "image"`
2. Set `image_name` = AMv2 `name`
3. Set `docker_repository_name` = AMv2 `group`
4. Set `docker_tag` = AMv2 `version`
5. Convert AMv2 `purl` to `full_image_name` using Registry Definition (see [PURL Conversion](#purl-to-dd-artifact-reference-conversion))
6. Convert AMv2 `hashes[0]` to `docker_digest`:
   - If hash exists and alg is "SHA-256": `docker_digest = hash.content` (without `sha256:` prefix)
   - If no hash: omit `docker_digest` field
7. Set `docker_registry` = extracted from PURL (registry host:port)
8. Omit fields with `null` values - only include fields that have actual values

**If Docker image HAS associated service chart:**

1. Find corresponding service chart component in app-chart
2. Create `DD.services[]` entry with `image_type = "service"`
3. Set `image_name` = AMv2 Docker image `name`
4. Set `docker_repository_name` = AMv2 Docker image `group`
5. Set `docker_tag` = AMv2 Docker image `version`
6. Convert AMv2 Docker image `purl` to `full_image_name` using Registry Definition
7. Convert AMv2 Docker image `hashes[0]` to `docker_digest`:
   - If hash exists and alg is "SHA-256": `docker_digest = hash.content` (without `sha256:` prefix)
   - If no hash: omit `docker_digest` field
8. Set `docker_registry` = extracted from PURL
9. Set `service_name` = service chart `name`
10. Set `version` = service chart `version`
11. Omit fields with `null` values - only include fields that have actual values

#### Step 3: Extract App-Chart

1. Find app-chart component (identified in Step 1)
2. If found:
   - Create `DD.charts[]` entry
   - Set `helm_chart_name` = AMv2 `name`
   - Set `helm_chart_version` = AMv2 `version`
   - Convert AMv2 `purl` to `full_chart_name` using Registry Definition (see [PURL Conversion](#purl-to-dd-artifact-reference-conversion))
   - Set `helm_registry` = extracted from PURL (registry URL)
   - Set `type` = `"app-chart"`
   - Omit fields with `null` values - only include fields that have actual values
3. If not found:
   - `DD.charts[]` = empty array `[]`

#### Step 4: Build DD Structure

1. Create root DD object:
   - Set `services` = array of all `DD.services[]` entries from Step 2
   - Set `charts` = array from Step 3
   - Initialize other DD sections as empty:
     - `metadata` = `{}`
     - `include` = `[]`
     - `infrastructures` = `[]`
     - `configurations` = `[]`
     - `frontends` = `[]`
     - `smartplug` = `[]`
     - `jobs` = `[]`
     - `libraries` = `[]`
     - `complexes` = `[]`
     - `additionalArtifacts` = `{}`
     - `descriptors` = `[]`

### PURL Conversion

PURL values are converted to DD artifact references using the [PURL → Artifact Reference](/docs/analysis/application-manifest-build-cli.md#purl---artifact-reference) algorithm.

**Artifact Reference to DD Mapping:**

| Artifact Reference Result                        | Maps to DD Field  |
|--------------------------------------------------|-------------------|
| `{REGISTRY}/{NAMESPACE}/{IMAGE}:{TAG}`           | `full_image_name` |
| `https://{REGISTRY}/{PATH}/{NAME}-{VERSION}.tgz` | `full_chart_name` |

**Conversion Process:**

```text
PURL with registry_name → [Official Algorithm] → Artifact Reference → DD field
```

**Examples:**

Docker:

```text
pkg:docker/cloud-core/image@build2?registry_name=artifactory-netcracker
  → Apply PURL → Artifact Reference algorithm
  → "artifactorycn.netcracker.com:17004/cloud-core/image:build2"
  → DD.full_image_name
```

Helm (File registry):

```text
pkg:helm/chart@1.0.0?registry_name=artifactory-netcracker
  → Apply PURL → Artifact Reference algorithm
  → "https://artifactorycn.netcracker.com/nc.helm.charts/chart-1.0.0.tgz"
  → DD.full_chart_name
```

**Note:** Registry Definition is required for `registry_name` resolution.
