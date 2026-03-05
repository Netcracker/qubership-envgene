# SBOM Retention

- [SBOM Retention](#sbom-retention)
  - [Overview](#overview)
  - [Problem Statement](#problem-statement)
  - [Solution](#solution)
  - [Retention Strategy](#retention-strategy)
    - [Version-Based Strategy](#version-based-strategy)
    - [When Cleanup is Triggered](#when-cleanup-is-triggered)
  - [Configuration](#configuration)
    - [Parameters](#parameters)
    - [Examples](#examples)
      - [No SBOM cleanup is performed](#no-sbom-cleanup-is-performed)
      - [Keep only n most recent versions per application](#keep-only-n-most-recent-versions-per-application)
  - [Use Cases](#use-cases)

## Overview

SBOM (Software Bill of Materials) files are cached in the Instance Repository to avoid expensive regeneration. This feature provides automatic cleanup of old SBOM files to manage repository size.

## Problem Statement

- SBOM generation is a computationally expensive operation
- SBOM files are cached in `/sboms/` directory for reuse
- [Job artifacts](/docs/dev/job-artifacts.md) size limit is 1500 GB
- Without cleanup, the cache grows indefinitely and may reach the size limit

## Solution

Automatic SBOM retention policy that:

- Runs during effective set generation when [GENERATE_EFFECTIVE_SET: true](/docs/instance-pipeline-parameters.md#generate_effective_set)
- Monitors repository size
- Triggers cleanup when size threshold is reached (1200 GB)
- Keeps N most recent versions per application
- Prevents cache growth beyond acceptable limits

## Retention Strategy

### Version-Based Strategy

The version-based strategy keeps the N most recent versions for each application:

- Groups SBOM files by application name
- Sorts versions by file creation time (newest first)
- Keeps the latest N versions
- Deletes all older versions

### When Cleanup is Triggered

Cleanup runs **only** when:

1. `GENERATE_EFFECTIVE_SET: true`
2. `sbom_retention.enabled: true` in configuration
3. Repository size reaches 1200 GB threshold

## Configuration

SBOM retention is configured in `/configuration/config.yml`.

### Parameters

```yaml
# Optional
# Triggers only when repository reaches 1200 GB
sbom_retention:
  # Optional
  # Default value: false
  enabled: bool
  # Optional
  # Default value: 10
  keep_versions_per_app: int
```

### Examples

#### No SBOM cleanup is performed

```yaml
# No sbom_retention section
```

or

```yaml
sbom_retention:
  enabled: false
```

#### Keep only n most recent versions per application

```yaml
sbom_retention:
  enabled: true
  keep_versions_per_app: n
```

## Use Cases

For detailed step-by-step scenarios demonstrating different SBOM retention configurations and repository states, see [SBOM Retention Use Cases](/docs/use-cases/sbom-retention.md).
