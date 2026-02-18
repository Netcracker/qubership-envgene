# Application Manifest v2 Specification

## Table of Contents

- [Application Manifest v2 Specification](#application-manifest-v2-specification)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Key Principles](#key-principles)
  - [Format and Structure](#format-and-structure)
  - [Metadata](#metadata)
  - [Components](#components)
    - [Common Component Structure](#common-component-structure)
      - [Property Attributes](#property-attributes)
      - [Hash Attributes](#hash-attributes)
      - [Data Attributes](#data-attributes)
      - [Component Attributes](#component-attributes)
    - [Component Types](#component-types)
      - [Application Components](#application-components)
        - [`application/vnd.nc.standalone-runnable`](#applicationvndncstandalone-runnable)
        - [`application/vnd.nc.smartplug`](#applicationvndncsmartplug)
        - [`application/vnd.nc.samplerepo`](#applicationvndncsamplerepo)
        - [`application/vnd.nc.cdn`](#applicationvndnccdn)
        - [`application/vnd.nc.crd`](#applicationvndnccrd)
        - [`application/vnd.nc.job`](#applicationvndncjob)
      - [Artifact Components](#artifact-components)
        - [`application/vnd.docker.image`](#applicationvnddockerimage)
        - [`application/vnd.nc.helm.chart`](#applicationvndnchelmchart)
        - [`application/zip`](#applicationzip)
        - [`application/java-archive`](#applicationjava-archive)
      - [Data Components](#data-components)
        - [`application/vnd.nc.helm.values.schema`](#applicationvndnchelmvaluesschema)
        - [`application/vnd.nc.resource-profile-baseline`](#applicationvndncresource-profile-baseline)
  - [Dependencies](#dependencies)
  - [Validation Rules](#validation-rules)
  - [References](#references)

## Overview

AMv2 extends the CycloneDX format (version 1.6) and provides hierarchical component structure. Main components (standalone-runnable, Helm charts, Docker images) are at the top level, while others charts can contain child components (other Helm charts, helm values schema, resource-profile-baseline) in their `components` array. Relationships between top-level components are expressed through the `dependencies` array.

### Key Principles

1. **Hierarchical Component Structure**: Main components are at the top level in the `components` array. Helm charts can contain child components (other Helm charts, helm values schema, resource-profile-baseline) in their `components` array
2. **Explicit Dependencies**: Relationships between top-level components are expressed through the `dependencies` array

## Format and Structure

AMv2 follows the CycloneDX 1.6 specification with the following structure:

| Attribute      | Type    | Mandatory | Description                                                                  |
|----------------|---------|-----------|------------------------------------------------------------------------------|
| `$schema`      | string  | Yes       | JSON Schema reference for AMv2                                               |
| `bomFormat`    | string  | Yes       | BOM format identifier. Must be `CycloneDX`                                   |
| `specVersion`  | string  | Yes       | CycloneDX specification version. Must be `1.6`                               |
| `serialNumber` | string  | Yes       | Unique BOM identifier. Must conform to RFC 4122 UUID format                  |
| `version`      | integer | Yes       | BOM version number. Starts from 1, increments when BOM is modified           |
| `metadata`     | object  | Yes       | BOM metadata (see [Metadata](#metadata))                                     |
| `components`   | array   | Yes       | Array of component objects (see [Components](#components))                   |
| `dependencies` | array   | Yes       | Array of dependency relationship objects (see [Dependencies](#dependencies)) |

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "serialNumber": "urn:uuid:...",
  "version": 1,
  "metadata": { ... },
  "components": [ ... ],
  "dependencies": [ ... ]
}
```

## Metadata

The `metadata` section describes the AMv2 itself and the tooling used to create it.

| Field                        | Type              | Mandatory | Description                                                                   |
|------------------------------|-------------------|-----------|-------------------------------------------------------------------------------|
| `timestamp`                  | string (ISO 8601) | Yes       | Timestamp when the BOM was created. Format: `YYYY-MM-DDTHH:mm:ssZ`            |
| `component`                  | object            | Yes       | Describes the application this BOM represents                                 |
| `component.type`             | string            | Yes       | Component type. Must be `application`                                         |
| `component.mime-type`        | string            | Yes       | MIME type. Must be `application/vnd.nc.application`                           |
| `component.bom-ref`          | string            | Yes       | Unique reference identifier for this component. Must be unique within the BOM |
| `component.name`             | string            | Yes       | Name of the application                                                       |
| `component.version`          | string            | Yes       | Version of the application                                                    |
| `tools`                      | object            | Yes       | Information about tools used to generate the BOM                              |
| `tools.components`           | array             | Yes       | Array of tool component objects                                               |
| `tools.components[].type`    | string            | Yes       | Tool component type. Must be `application`                                    |
| `tools.components[].name`    | string            | Yes       | Tool name (e.g., `am-build-cli`)                                              |
| `tools.components[].version` | string            | Yes       | Tool version                                                                  |

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "component": {
    "type": "application",
    "mime-type": "application/vnd.nc.application",
    "bom-ref": "app-ref-123",
    "name": "application-name",
    "version": "1.2.3"
  },
  "tools": {
    "components": [
      {
        "type": "application",
        "name": "am-build-cli",
        "version": "2.0.0"
      }
    ]
  }
}
```

## Components

Components in AMv2 are organized in a hierarchical structure. Main components (standalone-runnable, Helm charts, Docker images) are at the top level in the `components` array. Helm charts can contain child components (other Helm charts, helm values schema, resource-profile-baseline) in their `components` array. Relationships between top-level components are expressed through the `dependencies` array.

### Common Component Structure

All components share the following base structure:

```json
{
  "type": "application" | "container" | "data",
  "mime-type": "application/vnd.nc.*",
  "bom-ref": "unique-ref-id",
  "name": "component-name",
  "version": "component-version",
  "group": "component-group",
  "properties": [ ... ],
  "purl": "pkg:...",
  "hashes": [ ... ],
  "components": [ ... ],
  "data": [ ... ]
}
```

| Attribute    | Type   | Mandatory | Description                                                                                           |
|--------------|--------|-----------|-------------------------------------------------------------------------------------------------------|
| `type`       | string | Yes       | Component type. Must be one of: `application`, `container`, `data`                                    |
| `mime-type`  | string | Yes       | MIME type identifying the component type (e.g., `application/vnd.nc.standalone-runnable`)             |
| `bom-ref`    | string | Yes       | Unique reference identifier for the component within the BOM. Must be unique across all components    |
| `name`       | string | Yes       | Name of the component                                                                                 |
| `version`    | string | No        | Version of the component                                                                              |
| `group`      | string | No        | Grouping name (e.g., repository group for Docker images)                                              |
| `properties` | array  | No        | Array of property objects providing additional metadata                                               |
| `purl`       | string | No        | Package URL (purl) for component identification. Must conform to Package URL specification            |
| `hashes`     | array  | No        | Array of hash objects for component verification                                                      |
| `components` | array  | No        | Array of child components (for hierarchical structure, e.g., Helm charts containing child components) |
| `data`       | array  | No        | Array of data objects (for data components like helm values schema, resource-profile-baseline)        |

#### Property Attributes

Properties are key-value pairs stored in the `properties` array:

| Attribute | Type                                   | Mandatory | Description                                  |
|-----------|----------------------------------------|-----------|----------------------------------------------|
| `name`    | string                                 | Yes       | Property name                                |
| `value`   | string\|number\|boolean\|object\|array | Yes       | Property value. Type depends on the property |

#### Hash Attributes

Hashes are used for component verification:

| Attribute | Type   | Mandatory | Description                      |
|-----------|--------|-----------|----------------------------------|
| `alg`     | string | Yes       | Hash algorithm                   |
| `content` | string | Yes       | Hash value in hexadecimal format |

#### Data Attributes

[Data components](#data-components) contain a `data` array:

| Attribute                         | Type   | Mandatory | Description                                                                 |
|-----------------------------------|--------|-----------|-----------------------------------------------------------------------------|
| `type`                            | string | Yes       | Type of data. Must be `configuration`                                       |
| `name`                            | string | Yes       | Name of the data file (e.g., `values.schema.json`, `dev.yaml`)              |
| `contents`                        | object | Yes       | Contents object containing the data                                         |
| `contents.attachment`             | object | Yes       | Attachment object with encoded content                                      |
| `contents.attachment.contentType` | string | Yes       | MIME type of the content (e.g., `application/json`, `application/yaml`)     |
| `contents.attachment.encoding`    | string | Yes       | Encoding method. Must be `base64`                                           |
| `contents.attachment.content`     | string | Yes       | Base64-encoded content                                                      |

#### Component Attributes

The `components` array contains child component objects that form a hierarchical structure. Each element in the `components` array is a component object that follows the [Common Component Structure](#common-component-structure).

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.helm.chart",
  "bom-ref": "parent-chart-ref",
  "name": "parent-chart",
  "components": [
    {
      "type": "data",
      "mime-type": "application/vnd.nc.helm.values.schema",
      "bom-ref": "values-schema-ref",
      "name": "values.schema.json",
      "data": [ ... ]
    },
    {
      "type": "application",
      "mime-type": "application/vnd.nc.helm.chart",
      "bom-ref": "nested-chart-ref",
      "name": "nested-chart",
      "components": [ ... ]
    }
  ]
}
```

### Component Types

#### Application Components

Application Components are components that aggregate and orchestrate components of other types (artifacts, data components, etc.) to form complete applications or application extensions.

##### `application/vnd.nc.standalone-runnable`

Represents an application component that, after deployment to the cloud, runs continuously and remains operational for an extended period (e.g., web services, databases, message queues).

**Location:**

- Located at top-level in the `components` array

**Characteristics:**

- **Standalone**: The application is independent and self-contained, though it may have dependencies on other services (e.g., a web service may depend on a database)
- **Runnable**: After deployment, the application starts and runs continuously in the cloud, providing persistent services

**Dependencies:**

- Relationships with Helm charts and Docker images are established through the `dependencies` array
- One standalone-runnable can reference multiple Helm charts and Docker images through dependencies
- Standalone-runnable `dependsOn` app-chart (if exists) or all service Helm charts (if no app-chart)
- Standalone-runnable `dependsOn` all Docker images that are not associated with service Helm charts

**Pattern**: Standalone-runnable → Helm Chart → Docker image

| Attribute       | Type   | Mandatory | Default                                  | Description                               |
|-----------------|--------|-----------|------------------------------------------|-------------------------------------------|
| `type`          | string | yes       | `application`                            | Component type                            |
| `mime-type`     | string | yes       | `application/vnd.nc.standalone-runnable` | Component MIME type                       |
| `bom-ref`       | string | yes       | None                                     | Unique component identifier within the AM |
| `name`          | string | yes       | None                                     | Component name                            |
| `version`       | string | yes       | None                                     | Component version                         |
| `properties`    | array  | no        | `[]`                                     | Always `[]`                               |
| `components`    | array  | yes       | `[]`                                     | Always `[]`                               |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.standalone-runnable",
  "bom-ref": "standalone-runnable-ref-123",
  "name": "application-name",
  "version": "application-version",
  "properties": [],
  "components": []
}
```

##### `application/vnd.nc.smartplug`

Represents an application extension component that extends the functionality of a core Java application through pluggable Java code extensions. The extension is applied to the core application

**Location:**

- Located at top-level in the `components` array

**Characteristics:**

- **Not Standalone**: The extension depends on a core Java application that provides extension points
- **Not Runnable**: After the extension is applied to the core application, it does not run independently in the cloud; it becomes part of the core application

**Dependencies:**

- Relationships with Helm charts and JAR artifacts are established through the `dependencies` array
- Smartplug `dependsOn` Helm chart, which `dependsOn` JAR artifact

**Pattern**: Smartplug → Helm Chart → JAR

| Attribute       | Type   | Mandatory | Default                          | Description                                |
|-----------------|--------|-----------|----------------------------------|--------------------------------------------|
| `type`          | string | yes       | `application`                    | Component type                             |
| `mime-type`     | string | yes       | `application/vnd.nc.smartplug`   | Component MIME type                        |
| `bom-ref`       | string | yes       | None                             | Unique component identifier within the AM  |
| `name`          | string | yes       | None                             | Component name                             |
| `version`       | string | yes       | None                             | Component version                          |
| `properties`    | array  | yes       | `[]`                             | Always `[]`                                |
| `components`    | array  | yes       | `[]`                             | Always `[]`                                |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.smartplug",
  "bom-ref": "smartplug-ref-123",
  "name": "smartplug-name",
  "version": "smartplug-version",
  "properties": [],
  "components": []
}
```

##### `application/vnd.nc.samplerepo`

Represents a configuration application component that applies configuration to an existing application.

**Location:**

- Located at top-level in the `components` array

**Characteristics:**

- **Not Standalone**: The configuration depends on the application it configures
- **Not Runnable**: After the configuration is applied, it does not run independently in the cloud; it modifies the target application's configuration

**Dependencies:**

- Relationships with Helm charts and ZIP artifacts are established through the `dependencies` array
- Samplerepo `dependsOn` Helm chart, which `dependsOn` ZIP artifact

**Pattern**: Samplerepo → Helm Chart → ZIP

**Structure:**

| Attribute       | Type   | Mandatory | Default                          | Description                                |
|-----------------|--------|-----------|----------------------------------|--------------------------------------------|
| `type`          | string | yes       | `application`                    | Component type                             |
| `mime-type`     | string | yes       | `application/vnd.nc.samplerepo`  | Component MIME type                        |
| `bom-ref`       | string | yes       | None                             | Unique component identifier within the AM  |
| `name`          | string | yes       | None                             | Component name                             |
| `version`       | string | yes       | None                             | Component version                          |
| `properties`    | array  | yes       | `[]`                             | Always `[]`                                |
| `components`    | array  | yes       | `[]`                             | Always `[]`                                |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.samplerepo",
  "bom-ref": "samplerepo-ref-123",
  "name": "samplerepo-name",
  "version": "samplerepo-version",
  "properties": [],
  "components": []
}
```

##### `application/vnd.nc.cdn`

Represents a CDN application component that uses ZIP-based artifacts for content delivery.

**Location:**

- Located at top-level in the `components` array

**Dependencies:**

- Relationships with Helm charts and ZIP artifacts are established through the `dependencies` array
- CDN references a Helm chart, which in turn references a ZIP artifact
- CDN `dependsOn` Helm chart, which `dependsOn` ZIP artifact

**Pattern**: CDN → Helm Chart → ZIP

| Attribute       | Type   | Mandatory | Default                        | Description                                |
|-----------------|--------|-----------|--------------------------------|--------------------------------------------|
| `type`          | string | yes       | `application`                  | Component type                             |
| `mime-type`     | string | yes       | `application/vnd.nc.cdn`       | Component MIME type                        |
| `bom-ref`       | string | yes       | None                           | Unique component identifier within the AM  |
| `name`          | string | yes       | None                           | Component name                             |
| `version`       | string | yes       | None                           | Component version                          |
| `properties`    | array  | yes       | `[]`                           | Always `[]`                                |
| `components`    | array  | yes       | `[]`                           | Always `[]`                                |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.cdn",
  "bom-ref": "cdn-ref-123",
  "name": "cdn-name",
  "version": "cdn-version",
  "properties": [],
  "components": []
}
```

##### `application/vnd.nc.crd`

Represents a Custom Resource Definition (CRD) application component that defines Kubernetes custom resources.

**Location:**

- Located at top-level in the `components` array

**Dependencies:**

- Relationships with Helm charts are established through the `dependencies` array
- CRD `dependsOn` Helm chart containing CRD definitions

**Pattern**: CRD → Helm Chart

| Attribute       | Type   | Mandatory | Default                        | Description                                |
|-----------------|--------|-----------|--------------------------------|--------------------------------------------|
| `type`          | string | yes       | `application`                  | Component type                             |
| `mime-type`     | string | yes       | `application/vnd.nc.crd`       | Component MIME type                        |
| `bom-ref`       | string | yes       | None                           | Unique component identifier within the AM  |
| `name`          | string | yes       | None                           | Component name                             |
| `version`       | string | yes       | None                           | Component version                          |
| `properties`    | array  | yes       | `[]`                           | Always `[]`                                |
| `components`    | array  | yes       | `[]`                           | Always `[]`                                |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.crd",
  "bom-ref": "crd-ref-123",
  "name": "crd-name",
  "version": "crd-version",
  "properties": [],
  "components": []
}
```

##### `application/vnd.nc.job`

Represents a Kubernetes Job application component that executes a one-time task in the cluster (e.g., migrations, data initialization).

**Location:**

- Located at top-level in the `components` array

**Dependencies:**

- Relationships with Helm charts and Docker images are established through the `dependencies` array
- Job `dependsOn` Helm chart, which `dependsOn` Docker image

**Pattern**: Job → Helm Chart → Docker Image

| Attribute       | Type   | Mandatory | Default                        | Description                                |
|-----------------|--------|-----------|--------------------------------|--------------------------------------------|
| `type`          | string | yes       | `application`                  | Component type                             |
| `mime-type`     | string | yes       | `application/vnd.nc.job`       | Component MIME type                        |
| `bom-ref`       | string | yes       | None                           | Unique component identifier within the AM  |
| `name`          | string | yes       | None                           | Component name                             |
| `version`       | string | yes       | None                           | Component version                          |
| `properties`    | array  | yes       | `[]`                           | Always `[]`                                |
| `components`    | array  | yes       | `[]`                           | Always `[]`                                |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.job",
  "bom-ref": "job-ref-123",
  "name": "job-name",
  "version": "job-version",
  "properties": [],
  "components": []
}
```

#### Artifact Components

##### `application/vnd.docker.image`

Represents a Docker image artifact that contains containerized application code.

**Location:**

- Located at top-level in the `components` array

**Dependencies:**

- Relationships with `application/vnd.nc.helm.chart` are established through the `dependencies` array
- Service Helm charts `dependsOn` corresponding Docker images
- If app-chart exists, app-chart `dependsOn` all Docker images that are not associated with service Helm charts
- Uses PURL for identification

| Attribute       | Type   | Mandatory | Default                        | Description                                                |
|-----------------|--------|-----------|--------------------------------|------------------------------------------------------------|
| `type`          | string | yes       | `container`                    | Component type                                             |
| `mime-type`     | string | yes       | `application/vnd.docker.image` | Component MIME type                                        |
| `bom-ref`       | string | yes       | None                           | Unique component identifier within the AM                  |
| `name`          | string | yes       | None                           | Docker image name                                          |
| `group`         | string | yes       | `""`                           | Group or namespace for the image (empty string if none)    |
| `version`       | string | yes       | None                           | Docker image version (tag)                                 |
| `purl`          | string | yes       | None                           | Package URL (PURL) for the image                           |
| `hashes`        | array  | no        | None                           | List of hashes for the image (optional)                    |
| `hashes.alg`    | string | yes       | None                           | Hash algorithm, e.g., "SHA-256" (required if hash present) |
| `hashes.content`| string | yes       | None                           | Hash value as a hex string (required if hash present)      |

```json
{
  "type": "container",
  "mime-type": "application/vnd.docker.image",
  "bom-ref": "docker-image-ref-123",
  "name": "image-name",
  "group": "repository-group",
  "version": "image-tag",
  "purl": "pkg:docker/group/image-name@version?registry_id=registry",
  "hashes": [
    {
      "alg": "SHA-256",
      "content": "abc123..."
    }
  ]
}
```

##### `application/vnd.nc.helm.chart`

Represents a Helm chart, which can either be an umbrella (app-chart) chart that nests other charts or a standalone (service) chart without nested charts.

**App-chart:**

- App-chart is an umbrella chart that physically contains service Helm charts as child components
- This represents the physical structure where the umbrella chart artifact contains sub-charts
- Located is at top-level in the `components` array

**Service Helm Charts:**

- Service Helm charts are child components of app-chart (if app-chart exists) via `components` array
- Linked to Docker images through the `dependencies` array (Helm chart `dependsOn` Docker image)
- If no app-chart exists, service Helm charts are at top-level in the `components` array

**Child Components:**

- Helm charts may contain child components in the `components` array:
  - Service Helm charts (for app-chart only, representing sub-charts in umbrella chart)
  - Library Helm charts - `application/vnd.nc.helm.chart`
  - Helm values schema - `application/vnd.nc.helm.values.schema`
  - Resource profile baselines - `application/vnd.nc.resource-profile-baseline`
- May contain `nc:helm.values.artifactMappings` property for mapping Docker images to Helm values paths

**Dependencies:**

- Service Helm charts `dependsOn` corresponding Docker images
- If app-chart exists, app-chart `dependsOn` all Docker images that are not associated with service Helm charts
- Standalone-runnable `dependsOn` app-chart (if exists) or all service Helm charts (if no app-chart)

Root components of this type describe Helm Chart artifact, nested helm charts describe abstract helm charts (this is necessary to properly form values.yaml)

| Attribute             | Type    | Mandatory | Default                         | Description                                                |
|-----------------------|---------|-----------|---------------------------------|------------------------------------------------------------|
| `type`                | string  | yes       | `application`                   | Component type                                             |
| `mime-type`           | string  | yes       | `application/vnd.nc.helm.chart` | Component MIME type                                        |
| `bom-ref`             | string  | yes       | None                            | Unique component identifier within the AM                  |
| `name`                | string  | yes       | None                            | Helm chart name                                            |
| `version`             | string  | yes       | None                            | Helm chart version                                         |
| `purl`                | string  | no        | None                            | Package URL (PURL) for the chart                           |
| `hashes`              | array   | no        | None                            | List of hashes for the chart (empty array if none)         |
| `hashes.alg`          | string  | yes       | None                            | Hash algorithm, e.g., "SHA-256" (required if hash present) |
| `hashes.content`      | string  | yes       | None                            | Hash value as a hex string (required if hash present)      |
| `properties`          | array   | yes       | None                            | List of additional properties. See Properties below        |
| `components`          | array   | no        | `[]`                            | Nested components. See Components below                    |

**Components:**

| Child Component       | Type    | Mandatory | Default | Description                                                    |
|-----------------------|---------|-----------|---------|----------------------------------------------------------------|
| `components[0]`       | object  | no        | None    | Child `application/vnd.nc.helm.values.schema` component        |
| `components[1]`       | object  | no        | None    | Child `application/vnd.nc.resource-profile-baseline` component |
| `components[n]`       | object  | no        | None    | Child `application/vnd.nc.helm.chart` component                |

**Properties:**

| Property Name                            | Type    | Mandatory | Description                                                                                                                                                              |
|------------------------------------------|---------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `isLibrary`                              | boolean | Yes       | Indicates if the chart is a library chart. Value `true` for library charts, `false` for application charts                                                               |
| `nc:helm.values.artifactMappings`        | object  | No        | Maps Docker image bom-refs to Helm values paths. Used to specify how Docker images should be referenced in Helm chart values. See nc:helm.values.artifactMappings bellow |

```json
{
  "type": "application",
  "mime-type": "application/vnd.nc.helm.chart",
  "bom-ref": "helm-chart-ref-123",
  "name": "chart-name",
  "version": "chart-version",
  "properties": [
    {
      "name": "isLibrary",
      "value": false
    },
    {
      "name": "nc:helm.values.artifactMappings",
      "value": {
        "docker-image-bom-ref-1": {
          "valuesPathPrefix": "images.service1"
        }
      }
    }
    }
  ],
  "components": [
    {
      "type": "data",
      "mime-type": "application/vnd.nc.helm.values.schema",
      ...
    }
  ]
}
```

**nc:helm.values.artifactMappings:**

[`nc:helm.values.artifactMappings`](/docs/analysis/application-manifest-build-cli.md#artifactmappings-processing) maps Docker images to Helm values paths. It is used to specify how Docker images should be referenced in Helm chart values.

```json
{
  "properties": [
    {
      "name": "nc:helm.values.artifactMappings",
      "value": {
        "docker-image-bom-ref-1": {
          "valuesPathPrefix": "images.service1"
        },
        "docker-image-bom-ref-2": {
          "valuesPathPrefix": "images.service2"
        }
      }
    }
  ]
}
```

##### `application/zip`

Represents a ZIP archive artifact that contains application files or resources packaged in a compressed format.

**Dependencies:**

- Relationships with Helm charts are established through the `dependencies` array
- Helm chart `dependsOn` ZIP artifact
- Used by Samplerepo and CDN application components

**Pattern**: Application → Helm Chart → ZIP

##### `application/java-archive`

Represents a Java Archive (JAR) artifact that contains compiled Java classes and resources.

**Dependencies:**

- Relationships with Helm charts are established through the `dependencies` array
- Helm chart `dependsOn` JAR artifact

**Pattern**: Smartplug → Helm Chart → JAR

#### Data Components

##### `application/vnd.nc.helm.values.schema`

Represents a JSON Schema for Helm chart values that defines the structure and validation rules for chart values.

**Location:**

- Appears as a child component in a `application/vnd.nc.helm.chart`'s `components` array

| Attribute                                 | Type   | Mandatory | Default                                 | Description                               |
|-------------------------------------------|--------|-----------|-----------------------------------------|-------------------------------------------|
| `type`                                    | string | yes       | `data`                                  | Component type                            |
| `mime-type`                               | string | yes       | `application/vnd.nc.helm.values.schema` | Component MIME type                       |
| `bom-ref`                                 | string | yes       | None                                    | Unique component identifier within the AM |
| `name`                                    | string | yes       | `values.schema.json`                    | Logical name                              |
| `data`                                    | array  | yes       | None                                    | List of configuration entries             |
| `data[0].type`                            | string | yes       | `configuration`                         | Entry type                                |
| `data[0].name`                            | string | yes       | `values.schema.json`                    | Filename of the schema                    |
| `data[0].contents`                        | object | yes       | None                                    | Wrapper for the attachment                |
| `data[0].contents.attachment`             | object | yes       | None                                    | Embedded file payload                     |
| `data[0].contents.attachment.contentType` | string | yes       | `application/json`                      | MIME of payload                           |
| `data[0].contents.attachment.encoding`    | string | no        | `base64`                                | Encoding of the payload                   |
| `data[0].contents.attachment.content`     | string | yes       | None                                    | Base64-encoded schema contents            |

```json
{
  "type": "data",
  "mime-type": "application/vnd.nc.helm.values.schema",
  "bom-ref": "values-schema-ref-123",
  "name": "values.schema.json",
  "data": [
    {
      "type": "configuration",
      "name": "values.schema.json",
      "contents": {
        "attachment": {
          "contentType": "application/json",
          "encoding": "base64",
          "content": "..."
        }
      }
    }
  ]
}
```

##### `application/vnd.nc.resource-profile-baseline`

Represents Resource Profile Baselines for different environments that define resource configurations for various deployment scenarios.

**Location:**

- Appears as a child component in a `application/vnd.nc.helm.chart`'s `components` array

| Attribute                                 | Type   | Mandatory | Default                                        | Description                                                  |
|-------------------------------------------|--------|-----------|------------------------------------------------|--------------------------------------------------------------|
| `type`                                    | string | yes       | `data`                                         | Component type                                               |
| `mime-type`                               | string | yes       | `application/vnd.nc.resource-profile-baseline` | Component MIME type                                          |
| `bom-ref`                                 | string | yes       | None                                           | Unique component identifier within the AM                    |
| `name`                                    | string | yes       | `resource-profile-baselines`                   | Logical name of the bundle                                   |
| `data`                                    | array  | yes       | None                                           | List of configuration entries                                |
| `data[n].type`                            | string | yes       | `configuration`                                | Entry type                                                   |
| `data[n].name`                            | string | yes       | None                                           | Filename of the baseline, e.g. `small.yaml`, `dev.yaml`      |
| `data[n].contents`                        | object | yes       | None                                           | Wrapper for the attachment                                   |
| `data[n].contents.attachment`             | object | yes       | None                                           | Embedded file payload                                        |
| `data[n].contents.attachment.contentType` | string | yes       | None                                           | MIME of payload, e.g. `application/yaml`, `application/json` |
| `data[n].contents.attachment.encoding`    | string | yes       | `base64`                                       | Encoding of the payload                                      |
| `data[n].contents.attachment.content`     | string | yes       | None                                           | Base64-encoded file contents                                 |

```json
{
  "type": "data",
  "mime-type": "application/vnd.nc.resource-profile-baseline",
  "bom-ref": "resource-profile-ref-123",
  "name": "resource-profile-baselines",
  "data": [
    {
      "type": "configuration",
      "name": "dev.yaml",
      "contents": {
        "attachment": {
          "contentType": "application/yaml",
          "encoding": "base64",
          "content": "..."
        }
      }
    },
    {
      "type": "configuration",
      "name": "prod.yaml",
      "contents": {
        "attachment": {
          "contentType": "application/yaml",
          "encoding": "base64",
          "content": "..."
        }
      }
    }
  ]
}
```

## Dependencies

The `dependencies` array describes relationships between components using `bom-ref` identifiers.

Dependencies describe relationships between components:

| Attribute   | Type   | Mandatory | Description                                                                      |
|-------------|--------|-----------|----------------------------------------------------------------------------------|
| `ref`       | string | Yes       | `bom-ref` of the component that has dependencies                                 |
| `dependsOn` | array  | Yes       | Array of `bom-ref` strings identifying components that this component depends on |

**Structure:**

```json
{
  "dependencies": [
    {
      "ref": "component-bom-ref",
      "dependsOn": [
        "dependency-bom-ref-1",
        "dependency-bom-ref-2"
      ]
    }
  ]
}
```

**Key Relationships:**

- **Standalone Runnable → Helm Charts**: Standalone-runnable `dependsOn` all Helm charts that belong to it
- **Standalone Runnable → Docker Images**: Standalone-runnable `dependsOn` all Docker images that belong to it
- **Helm Chart → Docker Image**: Service Helm charts `dependsOn` corresponding Docker images
- **Helm Charts → App-chart**: If app-chart exists, all service Helm charts `dependsOn` app-chart
- **App-chart → Docker Images**: If app-chart exists, app-chart `dependsOn` all Docker images that are not associated with service Helm charts

## Validation Rules

1. **CycloneDX Compliance**: AMv2 must conform to CycloneDX 1.6 specification
2. **JSON Schema Validation**: AMv2 must be valid according to [JSON Schema](/schemas/application-manifest-v2.schema.json)
3. **Unique bom-ref**: All `bom-ref` values must be unique within the BOM
4. **Dependency References**: All references in `dependencies` must correspond to existing `bom-ref` values
5. **Required Fields**: All mandatory fields must be present
6. **MIME Types**: All components must have valid `mime-type` values
7. **PURL Format**: If present, `purl` must conform to Package URL specification

## References

- [CycloneDX Specification 1.6](https://cyclonedx.org/specification/overview/)
- [JSON Schema for AMv2](../schemas/application-manifest-v2.schema.json)
- [Package URL Specification](https://github.com/package-url/purl-spec)
