# SD Processing Use Cases

- [SD Processing Use Cases](#sd-processing-use-cases)
  - [Overview](#overview)
    - [UC-SD-1: Single SD\_VERSION with `replace` mode](#uc-sd-1-single-sd_version-with-replace-mode)
    - [UC-SD-2: Single SD\_VERSION with `extended-merge` mode](#uc-sd-2-single-sd_version-with-extended-merge-mode)
    - [UC-SD-2a: Single SD\_VERSION with `extended-merge` mode when Full SD does not exist](#uc-sd-2a-single-sd_version-with-extended-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-3: Single SD\_VERSION with `basic-merge` mode](#uc-sd-3-single-sd_version-with-basic-merge-mode)
    - [UC-SD-3a: Single SD\_VERSION with `basic-merge` mode when Full SD does not exist](#uc-sd-3a-single-sd_version-with-basic-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-4: Single SD\_VERSION with `basic-exclusion-merge` mode](#uc-sd-4-single-sd_version-with-basic-exclusion-merge-mode)
    - [UC-SD-4a: Single SD\_VERSION with `basic-exclusion-merge` mode when Full SD does not exist](#uc-sd-4a-single-sd_version-with-basic-exclusion-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-5: Multiple SD\_VERSION with `basic-merge` mode](#uc-sd-5-multiple-sd_version-with-basic-merge-mode)
    - [UC-SD-5a: Multiple SD\_VERSION with `basic-merge` mode when Full SD does not exist](#uc-sd-5a-multiple-sd_version-with-basic-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-6: Multiple SD\_VERSION with `basic-exclusion-merge` mode](#uc-sd-6-multiple-sd_version-with-basic-exclusion-merge-mode)
    - [UC-SD-6a: Multiple SD\_VERSION with `basic-exclusion-merge` mode when Full SD does not exist](#uc-sd-6a-multiple-sd_version-with-basic-exclusion-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-7: Multiple SD\_VERSION with `extended-merge` mode](#uc-sd-7-multiple-sd_version-with-extended-merge-mode)
    - [UC-SD-7a: Multiple SD\_VERSION with `extended-merge` mode when Full SD does not exist](#uc-sd-7a-multiple-sd_version-with-extended-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-8: Multiple SD\_VERSION with `replace` mode](#uc-sd-8-multiple-sd_version-with-replace-mode)
    - [UC-SD-9: Single SD\_VERSION with SD\_DELTA=true](#uc-sd-9-single-sd_version-with-sd_deltatrue)
    - [UC-SD-9a: Single SD\_VERSION with SD\_DELTA=true when Full SD does not exist](#uc-sd-9a-single-sd_version-with-sd_deltatrue-when-full-sd-does-not-exist)
    - [UC-SD-10: Single SD\_VERSION with SD\_DELTA=false](#uc-sd-10-single-sd_version-with-sd_deltafalse)
    - [UC-SD-11: Single SD\_DATA with `replace` mode](#uc-sd-11-single-sd_data-with-replace-mode)
    - [UC-SD-12: Single SD\_DATA with `extended-merge` mode](#uc-sd-12-single-sd_data-with-extended-merge-mode)
    - [UC-SD-12a: Single SD\_DATA with `extended-merge` mode when Full SD does not exist](#uc-sd-12a-single-sd_data-with-extended-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-13: Single SD\_DATA with `basic-merge` mode](#uc-sd-13-single-sd_data-with-basic-merge-mode)
    - [UC-SD-13a: Single SD\_DATA with `basic-merge` mode when Full SD does not exist](#uc-sd-13a-single-sd_data-with-basic-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-14: Single SD\_DATA with `basic-exclusion-merge` mode](#uc-sd-14-single-sd_data-with-basic-exclusion-merge-mode)
    - [UC-SD-14a: Single SD\_DATA with `basic-exclusion-merge` mode when Full SD does not exist](#uc-sd-14a-single-sd_data-with-basic-exclusion-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-15: Multiple SD\_DATA with `basic-merge` mode](#uc-sd-15-multiple-sd_data-with-basic-merge-mode)
    - [UC-SD-15a: Multiple SD\_DATA with `basic-merge` mode when Full SD does not exist](#uc-sd-15a-multiple-sd_data-with-basic-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-16: Multiple SD\_DATA with `basic-exclusion-merge` mode](#uc-sd-16-multiple-sd_data-with-basic-exclusion-merge-mode)
    - [UC-SD-16a: Multiple SD\_DATA with `basic-exclusion-merge` mode when Full SD does not exist](#uc-sd-16a-multiple-sd_data-with-basic-exclusion-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-17: Multiple SD\_DATA with `extended-merge` mode](#uc-sd-17-multiple-sd_data-with-extended-merge-mode)
    - [UC-SD-17a: Multiple SD\_DATA with `extended-merge` mode when Full SD does not exist](#uc-sd-17a-multiple-sd_data-with-extended-merge-mode-when-full-sd-does-not-exist)
    - [UC-SD-18: Multiple SD\_DATA with `replace` mode](#uc-sd-18-multiple-sd_data-with-replace-mode)
    - [UC-SD-19: Single SD\_DATA with SD\_DELTA=true](#uc-sd-19-single-sd_data-with-sd_deltatrue)
    - [UC-SD-19a: Single SD\_DATA with SD\_DELTA=true when Full SD does not exist](#uc-sd-19a-single-sd_data-with-sd_deltatrue-when-full-sd-does-not-exist)
    - [UC-SD-20: Single SD\_DATA with SD\_DELTA=false](#uc-sd-20-single-sd_data-with-sd_deltafalse)

## Overview

This document covers use cases for [Solution Descriptor Processing](/docs/features/sd-processing.md) - the process of retrieving, merging, and storing Solution Descriptors (SDs) in artifact or JSON format for Effective Set calculations and deployment purposes.

The SD processing logic depends on:

- Source type (`artifact` or `json`)
- Number of SDs provided (single or multiple)
- Merge mode (`replace`, `basic-merge`, `basic-exclusion-merge`, or `extended-merge`)
- Whether a Full SD already exists in the repository

### UC-SD-1: Single SD_VERSION with `replace` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: replace`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=replace"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. If Full SD exists in repository, replaces it completely with the downloaded SD
   4. If Full SD does not exist, saves the downloaded SD as Full SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
2. Delta SD is not created or modified

### UC-SD-2: Single SD_VERSION with `extended-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Saves downloaded SD as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges downloaded SD with repository Full SD using [`extended-merge` mode](/docs/features/sd-processing.md#extended-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-2a: Single SD_VERSION with `extended-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Detects that Full SD does not exist in repository
   4. Saves the downloaded SD as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the downloaded SD content
2. Delta SD is not created

### UC-SD-3: Single SD_VERSION with `basic-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_VERSION: <application:version>`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_VERSION=<application:version>"`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Saves downloaded SD as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges downloaded SD with repository Full SD using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-3a: Single SD_VERSION with `basic-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_VERSION: <application:version>`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_VERSION=<application:version>"`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Detects that Full SD does not exist in repository
   4. Saves the downloaded SD as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the downloaded SD content
2. Delta SD is not created

### UC-SD-4: Single SD_VERSION with `basic-exclusion-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Saves downloaded SD as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges downloaded SD with repository Full SD using [`basic-exclusion-merge` mode](/docs/features/sd-processing.md#basic-exclusion-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-4a: Single SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Detects that Full SD does not exist in repository
   4. Saves the downloaded SD as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the downloaded SD content
2. Delta SD is not created

### UC-SD-5: Multiple SD_VERSION with `basic-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_VERSION: <application:version>\n<application:version>`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_VERSION=<application:version>\\n<application:version>"`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Saves result from step 3 (merged multiple SDs) as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   5. Reads existing Full SD from repository
   6. Merges result from step 3 with repository Full SD using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   7. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-5a: Multiple SD_VERSION with `basic-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_VERSION: <application:version>\n<application:version>`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_VERSION=<application:version>\\n<application:version>"`

   Or with explicit parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Detects that Full SD does not exist in repository
   5. Saves the merged result from step 3 as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   6. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from multiple SD artifacts
2. Delta SD is not created

### UC-SD-6: Multiple SD_VERSION with `basic-exclusion-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Saves result from step 3 (merged multiple SDs) as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   5. Reads existing Full SD from repository
   6. Merges result from step 3 with repository Full SD using [`basic-exclusion-merge` mode](/docs/features/sd-processing.md#basic-exclusion-merge-sd-merge-mode)
   7. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-6a: Multiple SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Detects that Full SD does not exist in repository
   5. Saves the merged result from step 3 as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   6. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from multiple SD artifacts
2. Delta SD is not created

### UC-SD-7: Multiple SD_VERSION with `extended-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Attempts to process multiple SDs with `extended-merge` mode
   4. Raises error: `ValueError("Multiple SDs not supported in extended merge mode")`
   5. Pipeline job fails with error

**Results:**

1. Pipeline job fails with error: `ValueError("Multiple SDs not supported in extended merge mode")`
2. No SD files are created or modified in the repository

### UC-SD-7a: Multiple SD_VERSION with `extended-merge` mode when Full SD does not exist

> [!Note]
> This use case has the same behavior as UC-SD-7. Multiple SDs with `extended-merge` mode are not supported regardless of whether Full SD exists in the repository.

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Attempts to process multiple SDs with `extended-merge` mode
   4. Raises error: `ValueError("Multiple SDs not supported in extended merge mode")`
   5. Pipeline job fails with error

**Results:**

1. Pipeline job fails with error: `ValueError("Multiple SDs not supported in extended merge mode")`
2. No SD files are created or modified in the repository

### UC-SD-8: Multiple SD_VERSION with `replace` mode

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in all `SD_VERSION` entries
3. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>\n<application:version>`
   4. `SD_REPO_MERGE_MODE: replace`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>\\n<application:version>,SD_REPO_MERGE_MODE=replace"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter with multiple entries
   2. Downloads SD artifacts for each `application:version` in sequence
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Replaces Full SD in repository with the result from step 3 (no repository merge)
   5. Does not create or update Delta SD

**Results:**

1. Full SD is saved or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from all SD artifacts
2. Delta SD is not created or modified

### UC-SD-9: Single SD_VERSION with SD_DELTA=true

> [!Note]
> This use case covers deprecated `SD_DELTA` parameter behavior. When `SD_DELTA=true`, it behaves identically to `SD_REPO_MERGE_MODE: extended-merge`. If both `SD_DELTA` and `SD_REPO_MERGE_MODE` are provided, `SD_REPO_MERGE_MODE` takes precedence.

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_DELTA: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_DELTA=true"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Saves downloaded SD as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges downloaded SD with repository Full SD using `extended-merge` mode (equivalent to `SD_REPO_MERGE_MODE: extended-merge`)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-9a: Single SD_VERSION with SD_DELTA=true when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_DELTA: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_DELTA=true"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. Detects that Full SD does not exist in repository
   4. Saves the downloaded SD as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the downloaded SD content
2. Delta SD is not created
3. Full SD is available in job artifacts

### UC-SD-10: Single SD_VERSION with SD_DELTA=false

**Pre-requisites:**

1. Environment Inventory exists
2. AppDef and RegDef exist for each `app:ver` in `SD_VERSION`
3. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: artifact`
   3. `SD_VERSION: <application:version>`
   4. `SD_DELTA: false`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=artifact,SD_VERSION=<application:version>,SD_DELTA=false"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_VERSION` parameter
   2. Downloads SD artifact for the specified `application:version`
   3. If Full SD exists in repository, replaces it completely with the downloaded SD
   4. If Full SD does not exist, saves the downloaded SD as Full SD
   5. Does not create or update Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
2. Delta SD is not created or modified
3. Full SD is available in job artifacts

### UC-SD-11: Single SD_DATA with `replace` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: replace`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: replace`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=replace"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=replace"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. If Full SD exists in repository, replaces it completely with the SD from `SD_DATA`
   4. If Full SD does not exist, saves the SD from `SD_DATA` as Full SD
   5. Does not create or update Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
2. Delta SD is not created or modified

### UC-SD-12: Single SD_DATA with `extended-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: extended-merge`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=extended-merge"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Saves SD from `SD_DATA` as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges SD from `SD_DATA` with repository Full SD using [`extended-merge` mode](/docs/features/sd-processing.md#extended-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-12a: Single SD_DATA with `extended-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: extended-merge`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=extended-merge"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Detects that Full SD does not exist in repository
   4. Saves the SD from `SD_DATA` as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the SD from `SD_DATA`
2. Delta SD is not created

### UC-SD-13: Single SD_DATA with `basic-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: basic-merge`

   Or with SD as list and explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...}"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}]"`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=basic-merge"`

   Or with SD as list and explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Saves SD from `SD_DATA` as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges SD from `SD_DATA` with repository Full SD using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-13a: Single SD_DATA with `basic-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: basic-merge`

   Or with SD as list and explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...}"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}]"`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=basic-merge"`

   Or with SD as list and explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Detects that Full SD does not exist in repository
   4. Saves the SD from `SD_DATA` as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the SD from `SD_DATA`
2. Delta SD is not created

### UC-SD-14: Single SD_DATA with `basic-exclusion-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=basic-exclusion-merge"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Saves SD from `SD_DATA` as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges SD from `SD_DATA` with repository Full SD using [`basic-exclusion-merge` mode](/docs/features/sd-processing.md#basic-exclusion-merge-sd-merge-mode)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result
3. Duplicating Applications are removed from Full SD
4. Warnings are logged for New Applications

### UC-SD-14a: Single SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_REPO_MERGE_MODE=basic-exclusion-merge"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Detects that Full SD does not exist in repository
   4. Saves the SD from `SD_DATA` as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the SD from `SD_DATA`
2. Delta SD is not created

### UC-SD-15: Multiple SD_DATA with `basic-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}]"`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Saves result from step 3 (merged multiple SDs) as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   5. Reads existing Full SD from repository
   6. Merges result from step 3 with repository Full SD using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   7. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result

### UC-SD-15a: Multiple SD_DATA with `basic-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: basic-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}]"`

   Or with explicit merge mode:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=basic-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Detects that Full SD does not exist in repository
   5. Saves the merged result from step 3 as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   6. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from multiple SDs in `SD_DATA`
2. Delta SD is not created

### UC-SD-16: Multiple SD_DATA with `basic-exclusion-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Saves result from step 3 (merged multiple SDs) as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   5. Reads existing Full SD from repository
   6. Merges result from step 3 with repository Full SD using [`basic-exclusion-merge` mode](/docs/features/sd-processing.md#basic-exclusion-merge-sd-merge-mode)
   7. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result
3. Duplicating Applications are removed from Full SD
4. Warnings are logged for New Applications

### UC-SD-16a: Multiple SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: basic-exclusion-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=basic-exclusion-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Detects that Full SD does not exist in repository
   5. Saves the merged result from step 3 as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   6. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from multiple SDs in `SD_DATA`
2. Delta SD is not created

### UC-SD-17: Multiple SD_DATA with `extended-merge` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Attempts to process multiple SDs with `extended-merge` mode
   4. Raises error: `ValueError("Multiple SDs not supported in extended merge mode")`
   5. Pipeline job fails with error

**Results:**

1. Pipeline job fails with error: `ValueError("Multiple SDs not supported in extended merge mode")`
2. No SD files are created or modified in the repository

### UC-SD-17a: Multiple SD_DATA with `extended-merge` mode when Full SD does not exist

> [!Note]
> This use case has the same behavior as UC-SD-17. Multiple SDs with `extended-merge` mode are not supported regardless of whether Full SD exists in the repository.

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: extended-merge`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=extended-merge"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Attempts to process multiple SDs with `extended-merge` mode
   4. Raises error: `ValueError("Multiple SDs not supported in extended merge mode")`
   5. Pipeline job fails with error

**Results:**

1. Pipeline job fails with error: `ValueError("Multiple SDs not supported in extended merge mode")`
2. No SD files are created or modified in the repository

### UC-SD-18: Multiple SD_DATA with `replace` mode

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...},{...}]'` (multiple SDs in JSON array)
   4. `SD_REPO_MERGE_MODE: replace`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...},{...}],SD_REPO_MERGE_MODE=replace"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing multiple SDs in JSON format
   2. Parses JSON content to extract all SDs
   3. Merges multiple SDs sequentially using [`basic-merge` mode](/docs/features/sd-processing.md#basic-merge-sd-merge-mode)
   4. Replaces Full SD in repository with the result from step 3 (no repository merge)
   5. Does not create or update Delta SD

**Results:**

1. Full SD is saved or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result from all SDs in `SD_DATA`
2. Delta SD is not created or modified

### UC-SD-19: Single SD_DATA with SD_DELTA=true

> [!Note]
> This use case covers deprecated `SD_DELTA` parameter behavior. When `SD_DELTA=true`, it behaves identically to `SD_REPO_MERGE_MODE: extended-merge`. If both `SD_DELTA` and `SD_REPO_MERGE_MODE` are provided, `SD_REPO_MERGE_MODE` takes precedence.

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD exists in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_DELTA: true`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_DELTA: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_DELTA=true"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_DELTA=true"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Saves SD from `SD_DATA` as Delta SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml`
   4. Reads existing Full SD from repository
   5. Merges SD from `SD_DATA` with repository Full SD using `extended-merge` mode (equivalent to `SD_REPO_MERGE_MODE: extended-merge`)
   6. Saves merged result as Full SD, replacing the existing one

**Results:**

1. Full SD is updated at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with merged result
2. Delta SD is created or replaced at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yaml` with merged result
3. Behavior is identical to UC-SD-12 (Single SD_DATA with `extended-merge` mode)

### UC-SD-19a: Single SD_DATA with SD_DELTA=true when Full SD does not exist

> [!Note]
> This use case covers deprecated `SD_DELTA` parameter behavior. When `SD_DELTA=true`, it behaves identically to `SD_REPO_MERGE_MODE: extended-merge`. This use case describes the fallback behavior when Full SD does not exist in the repository.

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD does **not** exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_DELTA: true`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_DELTA: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_DELTA=true"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_DELTA=true"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. Detects that Full SD does not exist in repository
   4. Saves the SD from `SD_DATA` as Full SD at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
   5. Does not create Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml` with the SD from `SD_DATA`
2. Behavior is identical to UC-SD-12a (Single SD_DATA with `extended-merge` mode when Full SD does not exist)
3. Delta SD is not created
4. Full SD is available in job artifacts

### UC-SD-20: Single SD_DATA with SD_DELTA=false

> [!Note]
> This use case covers deprecated `SD_DELTA` parameter behavior. When `SD_DELTA=false`, it behaves identically to `SD_REPO_MERGE_MODE: replace`. If both `SD_DELTA` and `SD_REPO_MERGE_MODE` are provided, `SD_REPO_MERGE_MODE` takes precedence.

**Pre-requisites:**

1. Environment Inventory exists
2. Full SD may or may not exist in repository at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '{...}'`
   4. `SD_DELTA: false`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `SD_SOURCE_TYPE: json`
   3. `SD_DATA: '[{...}]'`
   4. `SD_DELTA: false`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA={...},SD_DELTA=false"`

   Or with SD as list:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "SD_SOURCE_TYPE=json,SD_DATA=[{...}],SD_DELTA=false"`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Reads `SD_DATA` parameter containing single SD in JSON format
   2. Parses JSON content to extract SD
   3. If Full SD exists in repository, replaces it completely with the SD from `SD_DATA`
   4. If Full SD does not exist, saves the SD from `SD_DATA` as Full SD
   5. Does not create or update Delta SD

**Results:**

1. Full SD is saved at `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`
2. Behavior is identical to UC-SD-11 (Single SD_DATA with `replace` mode)
3. Delta SD is not created or modified
4. Full SD is available in job artifacts
