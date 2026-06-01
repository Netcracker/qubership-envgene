# SBOM Retention Use Cases

- [SBOM Retention Use Cases](#sbom-retention-use-cases)
  - [Overview](#overview)
  - [SBOM cleanup execution](#sbom-cleanup-execution)
    - [UC-SBOM-1: SBOM retention disabled - no cleanup](#uc-sbom-1-sbom-retention-disabled---no-cleanup)
    - [UC-SBOM-2: All applications within per-application limit - no files deleted](#uc-sbom-2-all-applications-within-per-application-limit---no-files-deleted)
    - [UC-SBOM-3: Per-application retention keeps 10 most recent versions](#uc-sbom-3-per-application-retention-keeps-10-most-recent-versions)
    - [UC-SBOM-4: Per-application retention with custom version count](#uc-sbom-4-per-application-retention-with-custom-version-count)
    - [UC-SBOM-5: Total /sboms/ size exceeds 600 MB - safety net keeps newest per application](#uc-sbom-5-total-sboms-size-exceeds-600-mb---safety-net-keeps-newest-per-application)

## Overview

This document covers use cases for [SBOM Retention](/docs/features/sbom-retention.md), the
automatic cleanup of cached SBOM files used to manage Instance Repository size. SBOM files are
stored under `/sboms/<application-name>/` as `<application-name>-<application-version>.sbom.json`.
See [SBOM directory layout](/docs/features/sbom.md#sbom-directory-layout) for the storage
structure.

## SBOM cleanup execution

The cleanup logic runs during effective set generation and depends only on the
`sbom_retention.enabled` flag. When enabled, per-application SBOM retention runs only if
`keep_versions_per_app` is set, then a 600 MB safety net is evaluated on the total size
of `/sboms/`. These use cases demonstrate the observable behavior in each scenario.

### UC-SBOM-1: SBOM retention disabled - no cleanup

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory. SBOM files are stored in
   `/sboms/<application-name>/`
2. SBOM files exist in `/sboms/<application-name>/`
3. SBOM retention is **disabled** in `/configuration/config.yml`:

   ```yaml
   # Option 1: No sbom_retention section
   ```

   or

   ```yaml
   # Option 2: Explicitly disabled
   sbom_retention:
     enabled: false
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. SBOM retention configuration is checked. `enabled` is false (or the section is absent).
3. SBOM cleanup is skipped.
4. The effective set generation completes.

**Results:**

1. Effective set is generated successfully
2. No SBOM files are deleted
3. Pipeline log shows: `SBOM retention policy is disabled`

### UC-SBOM-2: All applications within per-application limit - no files deleted

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory. SBOM files are stored in
   `/sboms/<application-name>/`
2. SBOM files exist for multiple applications, with each subdirectory holding
   `keep_versions_per_app` files or fewer:
   - `/sboms/app-a/`: 7 versions
   - `/sboms/app-b/`: 4 versions
   - `/sboms/app-c/`: 10 versions
3. SBOM retention is **enabled** in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 10
   ```

4. Total size of `/sboms/` is 200 MB (at or below the 600 MB safety-net threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. SBOM retention is enabled with `keep_versions_per_app: 10`. The cleanup procedure starts.
3. Any legacy flat SBOM files at the top of `/sboms/` are removed (none in this case).
4. Per-application SBOM retention runs over each subdirectory. Every subdirectory already
   contains 10 or fewer files, so no files are deleted.
5. The total size of `/sboms/` is at or below the 600 MB safety-net threshold. The safety net
   does not run.
6. The effective set generation completes.

**Results:**

1. Effective set is generated successfully
2. No SBOM files are deleted
3. Pipeline log shows:
   - `SBOM retention policy is enabled for directory <path>/sboms`
   - `Directory size 200.00 MB`

### UC-SBOM-3: Per-application retention keeps 10 most recent versions

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist for multiple applications under per-application subdirectories:
   - `/sboms/app-a/`: 15 SBOM files
   - `/sboms/app-b/`: 12 SBOM files
   - `/sboms/app-c/`: 8 SBOM files
3. SBOM retention is **enabled** in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 10
   ```

4. Total size of `/sboms/` is 500 MB (below the 600 MB safety-net threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. SBOM retention is enabled with `keep_versions_per_app: 10`. The cleanup procedure starts.
3. Any legacy flat SBOM files at the top of `/sboms/` are removed (none in this case).
4. For each per-application subdirectory, the 10 most recent files are kept and older files are
   deleted.
5. The total size of `/sboms/` after per-application SBOM retention is at or below the 600 MB
   safety-net threshold. The safety net does not run.
6. The effective set generation completes.

**Results:**

1. Effective set is generated successfully
2. SBOM files are cleaned up per application:
   - `/sboms/app-a/`: 10 most recently modified files are kept, the 5 oldest are deleted
   - `/sboms/app-b/`: 10 most recently modified files are kept, the 2 oldest are deleted
   - `/sboms/app-c/`: all 8 files are kept (count is at or below `keep_versions_per_app`)
3. Total files deleted: 7 SBOM files
4. Pipeline log shows:
   - `SBOM retention policy is enabled for directory <path>/sboms`
   - `Only 10 files will remain in <path>/sboms/app-a` (and a `Removing file:` line per deleted
     file)
   - `Only 10 files will remain in <path>/sboms/app-b` (and a `Removing file:` line per deleted
     file)
   - `Directory size <X> MB`

### UC-SBOM-4: Per-application retention with custom version count

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist for application `postgres` under `/sboms/postgres/`: 10 SBOM files
3. SBOM retention is **enabled** with custom settings in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 3  # only keep 3 most recent versions
   ```

4. Total size of `/sboms/` is 350 MB (below the 600 MB safety-net threshold)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. SBOM retention is enabled with `keep_versions_per_app: 3`. The cleanup procedure starts.
3. Any legacy flat SBOM files at the top of `/sboms/` are removed (none in this case).
4. For `/sboms/postgres/`, the 3 most recent files are kept and the 7 older files are deleted.
5. The total size of `/sboms/` after per-application SBOM retention is at or below the 600 MB
   safety-net threshold. The safety net does not run.
6. The effective set generation completes.

**Results:**

1. Effective set is generated successfully
2. SBOM files under `/sboms/postgres/` are cleaned up:
   - 3 most recently modified files are kept
   - 7 oldest files are deleted
3. Total files deleted: 7 SBOM files
4. Pipeline log shows:
   - `SBOM retention policy is enabled for directory <path>/sboms`
   - `Only 3 files will remain in <path>/sboms/postgres` (and a `Removing file:` line per
     deleted file)
   - `Directory size <X> MB`

### UC-SBOM-5: Total /sboms/ size exceeds 600 MB - safety net keeps newest per application

**Pre-requisites:**

1. Instance Repository exists with `/sboms/` directory
2. SBOM files exist for several applications. Each subdirectory already contains
   `keep_versions_per_app` files or fewer, but the individual SBOM files are unusually large
3. SBOM retention is **enabled** in `/configuration/config.yml`:

   ```yaml
   sbom_retention:
     enabled: true
     keep_versions_per_app: 10
   ```

4. Total size of `/sboms/` is 700 MB (above the 600 MB safety-net threshold). Per-application
   retention is not able to reduce the total below the threshold because no per-application
   subdirectory exceeds `keep_versions_per_app`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. SBOM retention is enabled with `keep_versions_per_app: 10`. The cleanup procedure starts.
3. Any legacy flat SBOM files at the top of `/sboms/` are removed (none in this case).
4. Per-application SBOM retention runs over each subdirectory. No subdirectory exceeds
   `keep_versions_per_app`, so no per-application files are deleted.
5. The total size of `/sboms/` is above the 600 MB safety-net threshold. Safety-net retention
   runs over each subdirectory and keeps only the most recently modified file. Older files in
   each subdirectory are deleted.
6. The effective set generation completes.

**Results:**

1. Effective set is generated successfully
2. Only the single most recent SBOM file remains under each `/sboms/<application-name>/`. Older
   versions are deleted. Subsequent pipeline runs that need previous versions will regenerate
   them, which is a costly operation
3. Pipeline log shows:
   - `SBOM retention policy is enabled for directory <path>/sboms`
   - `Directory size 700.00 MB`
   - `SBOM directory exceeds size limit, starting cleanup: <path>/sboms`
   - `Only 1 files will remain in <path>/sboms/<application-name>` (one per subdirectory that
     had more than one file), and a `Removing file: <path>` line per deleted file
