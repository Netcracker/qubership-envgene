# SBOM Retention Use Cases

- [SBOM Retention Use Cases](#sbom-retention-use-cases)
  - [Overview](#overview)
  - [SBOM Cleanup Execution](#sbom-cleanup-execution)
    - [UC-SBOM-1: SBOM Retention Disabled - No Cleanup](#uc-sbom-1-sbom-retention-disabled---no-cleanup)
    - [UC-SBOM-2: Repository Below Threshold - No Cleanup](#uc-sbom-2-repository-below-threshold---no-cleanup)
    - [UC-SBOM-3: Repository Above Threshold - Cleanup with Default Settings](#uc-sbom-3-repository-above-threshold---cleanup-with-default-settings)
    - [UC-SBOM-4: Repository Above Threshold - Cleanup with Custom Version Count](#uc-sbom-4-repository-above-threshold---cleanup-with-custom-version-count)

## Overview

This document covers use cases for [SBOM Retention](/docs/features/sbom-retention.md) - automatic cleanup of cached SBOM files to manage Instance Repository size.

## SBOM Cleanup Execution

The cleanup logic is triggered during effective set generation and depends on configuration settings and repository size. These use cases demonstrate different scenarios based on configuration and repository state.

### UC-SBOM-1: SBOM Retention Disabled - No Cleanup

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist in `/sboms/` directory
3. SBOM retention is **disabled** in `/configuration/config.yml`:

   ```yaml
   # Option 1: No sbom_retention section
   crypt: false
   ```

   or

   ```yaml
   # Option 2: Explicitly disabled
   sbom_retention:
     enabled: false
   ```

4. Repository size is 1300 MB (above 1200 MB threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Generates effective set for the environment
   2. Checks SBOM retention configuration
   3. Finds `sbom_retention.enabled: false` (or no configuration)
   4. Skips SBOM cleanup logic
   5. Completes effective set generation

**Results:**

1. Effective set is generated successfully
2. No SBOM files are deleted
3. Pipeline log shows: "SBOM retention is disabled, skipping cleanup"

### UC-SBOM-2: Repository Below Threshold - No Cleanup

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist in `/sboms/` directory with total size 800 MB
3. SBOM retention is **enabled** in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 10
   ```

4. Repository size is 800 MB (below 1200 MB threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Generates effective set for the environment
   2. Checks SBOM retention configuration
   3. Finds `sbom_retention.enabled: true`
   4. Checks repository size: 800 MB
   5. Compares with threshold: 800 MB < 1200 MB
   6. Skips SBOM cleanup (threshold not reached)
   7. Completes effective set generation

**Results:**

1. Effective set is generated successfully
2. No SBOM files are deleted
3. Pipeline log shows: "Repository size (800 MB) below threshold (1200 MB), skipping cleanup"

### UC-SBOM-3: Repository Above Threshold - Cleanup with Default Settings

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist for multiple applications:
   - `app-a-1.0.15.sbom.json` through `app-a-1.0.1.sbom.json` (15 versions)
   - `app-b-2.0.12.sbom.json` through `app-b-2.0.1.sbom.json` (12 versions)
   - `app-c-3.5.8.sbom.json` through `app-c-3.5.1.sbom.json` (8 versions)
3. SBOM retention is **enabled** with default settings in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 10  # default value
   ```

4. Repository size is 1300 MB (above 1200 MB threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Generates effective set for the environment
   2. Checks SBOM retention configuration: enabled with `keep_versions_per_app: 10`
   3. Checks repository size: 1300 MB > 1200 MB threshold
   4. Triggers SBOM cleanup process:
      1. Scans `/sboms/` directory
      2. Groups SBOM files by application name
      3. For each application:
         - Sorts versions by file creation time (newest first)
         - Keeps 10 most recent versions
         - Deletes older versions
   5. Completes effective set generation

**Results:**

1. Effective set is generated successfully
2. SBOM files are cleaned up for each application:
   - **app-a**: Keeps versions 1.0.15 through 1.0.6 (10 versions)
   - **app-b**: Keeps versions 2.0.12 through 2.0.3 (10 versions)
   - **app-c**: Keeps all 8 versions (no deletion needed)
3. Total files deleted: 7 SBOM files
4. Pipeline log shows:
   - "Repository size (1300 MB) above threshold (1200 MB), starting cleanup"
   - "Cleaned up 7 SBOM files"
   - "Kept 10 versions per application"

### UC-SBOM-4: Repository Above Threshold - Cleanup with Custom Version Count

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist for application `postgres`:
   - `postgres-pg16-2.10.10.sbom.json` through `postgres-pg16-2.10.1.sbom.json` (10 versions)
3. SBOM retention is **enabled** with custom settings in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 3  # only keep 3 most recent versions
   ```

4. Repository size is 1350 MB (above 1200 MB threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Generates effective set for the environment
   2. Checks SBOM retention configuration: enabled with `keep_versions_per_app: 3`
   3. Checks repository size: 1350 MB > 1200 MB threshold
   4. Triggers SBOM cleanup process:
      1. Scans `/sboms/` directory
      2. Groups SBOM files by application name (finds `postgres`)
      3. Sorts postgres versions by file creation time (newest first)
      4. Keeps 3 most recent versions: 2.10.10, 2.10.9, 2.10.8
      5. Deletes 7 older versions: 2.10.7 through 2.10.1
   5. Completes effective set generation

**Results:**

1. Effective set is generated successfully
2. SBOM files for `postgres` are cleaned up:
   - **Kept**: `postgres-pg16-2.10.10.sbom.json`, `postgres-pg16-2.10.9.sbom.json`, `postgres-pg16-2.10.8.sbom.json`
   - **Deleted**: `postgres-pg16-2.10.7.sbom.json` through `postgres-pg16-2.10.1.sbom.json` (7 files)
3. Total files deleted: 7 SBOM files
4. Pipeline log shows:
   - "Repository size (1350 MB) above threshold (1200 MB), starting cleanup"
   - "Cleaned up 7 SBOM files for postgres"
   - "Kept 3 versions per application"
