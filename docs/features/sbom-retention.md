# SBOM Retention

- [SBOM Retention](#sbom-retention)
  - [Overview](#overview)
  - [Problem Statement](#problem-statement)
  - [Solution](#solution)
  - [When cleanup is triggered](#when-cleanup-is-triggered)
  - [Retention strategy](#retention-strategy)
    - [Per-application version retention](#per-application-version-retention)
    - [Total size limit](#total-size-limit)
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
- The `/sboms/` cache is committed to the repository and is included in the troubleshooting job artifact
- Without cleanup, the cache grows indefinitely and bloats both the repository and the artifact

## Solution

Automatic SBOM retention policy that:

- Runs during effective set generation when
  [GENERATE_EFFECTIVE_SET: true](/docs/instance-pipeline-parameters.md#generate_effective_set)
- Is activated by `sbom_retention.enabled: true`
- Applies [per-application version retention](#per-application-version-retention) to each
  subdirectory under `/sboms/`, when `keep_versions_per_app` is set
- Falls back to a [total size limit](#total-size-limit) step that keeps only the single most
  recently modified file in each per-application subdirectory if the total size of `/sboms/`
  still exceeds 50 MB after per-application SBOM retention

## When cleanup is triggered

Cleanup runs when both of the following conditions are true:

1. `GENERATE_EFFECTIVE_SET: true` (retention runs as part of the effective set job)
2. `sbom_retention.enabled: true` in `/configuration/config.yml`

Cleanup is **not** gated by repository size. The 50 MB limit is checked only by the
[total size limit](#total-size-limit) step, after per-application SBOM retention has run.

## Retention strategy

When cleanup is triggered, retention processes `/sboms/` in this order:

1. Any legacy flat SBOM files located directly under `/sboms/` (not inside a per-application
   subdirectory) are removed first. See
   [SBOM Storage Migration](/docs/how-to/sbom-storage-migration.md) for context.
2. [Per-application version retention](#per-application-version-retention) runs for each
   subdirectory under `/sboms/`.
3. [Total size limit](#total-size-limit) is evaluated on `/sboms/` as a whole.

### Per-application version retention

Per-application SBOM retention runs only when `keep_versions_per_app` is set to a positive
integer. If the field is omitted or set to `0`, this step is skipped and only the
[total size limit](#total-size-limit) step runs.

For each application subdirectory under `/sboms/`:

- Files are sorted by modification time, newest first
- The N most recent files are kept, where N = `keep_versions_per_app`
- Older files are deleted
- If the subdirectory already contains N or fewer files, no files are deleted from it

> [!NOTE]
> Ordering is by file modification time. Retention does not parse version strings from
> filenames and is not aware of SemVer semantics.

### Total size limit

After per-application SBOM retention, the total size of `/sboms/` is compared to the 50 MB
limit:

- If the total size is at or below 50 MB, no further action is taken
- If the total size exceeds 50 MB, retention runs over each per-application subdirectory and
  keeps only the single most recently modified file. Older files in each subdirectory are deleted

The 50 MB limit keeps the committed `/sboms/` cache bounded, so the repository and the
troubleshooting job artifact do not grow without limit. It is sized to stay a bounded share of the
work-directory artifact. See
[Troubleshooting artifacts](/docs/features/troubleshooting-artifacts.md) for the artifact budget.

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
  # Per-application SBOM retention runs only when this is set to a positive integer.
  # If the field is omitted or set to `0`, this step is skipped and only the total size
  # limit step runs (keeping the most recent file per application subdirectory when
  # /sboms/ exceeds 50 MB)
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
