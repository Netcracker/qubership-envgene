# SBOM Retention

- [SBOM Retention](#sbom-retention)
  - [Overview](#overview)
  - [Problem Statement](#problem-statement)
  - [Solution](#solution)
  - [When cleanup is triggered](#when-cleanup-is-triggered)
  - [Retention strategy](#retention-strategy)
    - [Per-application version retention](#per-application-version-retention)
    - [Total size safety net](#total-size-safety-net)
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
- [Job artifacts](/docs/dev/job-artifacts.md) size limit is 1500 MB
- Without cleanup, the cache grows indefinitely and may reach the size limit

## Solution

Automatic SBOM retention policy that:

- Runs during effective set generation when
  [GENERATE_EFFECTIVE_SET: true](/docs/instance-pipeline-parameters.md#generate_effective_set)
- Is activated by `sbom_retention.enabled: true`
- Applies [per-application version retention](#per-application-version-retention) to each
  subdirectory under `/sboms/`, when `keep_versions_per_app` is set
- Falls back to a [total size safety net](#total-size-safety-net) that keeps only the single most
  recently modified file in each per-application subdirectory if the total size of `/sboms/`
  still exceeds 600 MB after per-application SBOM retention

## When cleanup is triggered

Cleanup runs when both of the following conditions are true:

1. `GENERATE_EFFECTIVE_SET: true` (retention runs as part of the effective set job)
2. `sbom_retention.enabled: true` in `/configuration/config.yml`

Cleanup is **not** gated by repository size. The 600 MB threshold is checked only by the
[total size safety net](#total-size-safety-net) step, after per-application SBOM retention
has run.

## Retention strategy

When cleanup is triggered, retention processes `/sboms/` in this order:

1. Any legacy flat SBOM files located directly under `/sboms/` (not inside a per-application
   subdirectory) are removed first. See
   [SBOM Storage Migration](/docs/how-to/sbom-storage-migration.md) for context.
2. [Per-application version retention](#per-application-version-retention) runs for each
   subdirectory under `/sboms/`.
3. [Total size safety net](#total-size-safety-net) is evaluated on `/sboms/` as a whole.

### Per-application version retention

This step runs only when `keep_versions_per_app` is set to a positive integer. When the value is
unset or `0`, per-application SBOM retention is skipped and only the
[total size safety net](#total-size-safety-net) is applied.

For each application subdirectory under `/sboms/`:

- Files are sorted by modification time, newest first
- The N most recent files are kept, where N = `keep_versions_per_app`
- Older files are deleted
- If the subdirectory already contains N or fewer files, no files are deleted from it

> [!NOTE]
> Ordering is by file modification time. Retention does not parse version strings from
> filenames and is not aware of SemVer semantics.

### Total size safety net

After per-application SBOM retention, the total size of `/sboms/` is compared to the 600 MB
threshold:

- If the total size is at or below 600 MB, no further action is taken
- If the total size exceeds 600 MB, retention runs over each per-application subdirectory and
  keeps only the single most recently modified file. Older files in each subdirectory are deleted

The 600 MB threshold sits well below the [job artifacts](/docs/dev/job-artifacts.md) 1500 MB
limit so that retention can keep the cache within bounds before the job artifact size becomes
a problem.

## Configuration

SBOM retention is configured in `/configuration/config.yml`.

### Parameters

```yaml
# Optional
# SBOM retention configuration
sbom_retention:
  # Optional
  # Default value: false
  enabled: bool
  # Optional
  # No default value
  # When unset or `0`, per-application SBOM retention is skipped and only the total size
  # safety net runs (keeping the most recent file per application subdirectory when /sboms/
  # exceeds 600 MB)
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

For detailed step-by-step scenarios demonstrating different SBOM retention configurations and
repository states, see [SBOM Retention Use Cases](/docs/use-cases/sbom-retention.md).
