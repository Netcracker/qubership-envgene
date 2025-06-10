# SD Processing Test Cases

- [SD Processing Test Cases](#sd-processing-test-cases)
  - [TC-001-001: Adding SD for the first time for an Environment via SD artifact](#tc-001-001-adding-sd-for-the-first-time-for-an-environment-via-sd-artifact)
  - [TC-001-002: Adding SD for the first time an Environment via SD content](#tc-001-002-adding-sd-for-the-first-time-an-environment-via-sd-content)
  - [TC-001-003: Adding SD for the first time for an Environment via several SD artifacts](#tc-001-003-adding-sd-for-the-first-time-for-an-environment-via-several-sd-artifacts)
  - [TC-001-004: Adding SD for the first time for an Environment via content of several SDs](#tc-001-004-adding-sd-for-the-first-time-for-an-environment-via-content-of-several-sds)
  - [TC-001-005: Replace SD for an Environment via SD artifact](#tc-001-005-replace-sd-for-an-environment-via-sd-artifact)
  - [TC-001-006: Replace SD for an Environment via SD content](#tc-001-006-replace-sd-for-an-environment-via-sd-content)
  - [TC-001-007: Replace SD for an Environment via several SD artifacts](#tc-001-007-replace-sd-for-an-environment-via-several-sd-artifacts)
  - [TC-001-008: Replace SD for an Environment via content of several SDs](#tc-001-008-replace-sd-for-an-environment-via-content-of-several-sds)
  - [TC-001-009: Adding new application and update application version to SD for an Environment via SD artifact](#tc-001-009-adding-new-application-and-update-application-version-to-sd-for-an-environment-via-sd-artifact)
  - [TC-001-010: Adding new application and update application version to SD for an Environment via SD content](#tc-001-010-adding-new-application-and-update-application-version-to-sd-for-an-environment-via-sd-content)
  - [TC-001-011: Adding new application and update application version to SD for an Environment via several SD artifacts](#tc-001-011-adding-new-application-and-update-application-version-to-sd-for-an-environment-via-several-sd-artifacts)
  - [TC-001-012: Adding new application and update application version to SD for an Environment via content of several SDs](#tc-001-012-adding-new-application-and-update-application-version-to-sd-for-an-environment-via-content-of-several-sds)
  - [TC-001-013: Removing application and revert application version from SD for an Environment via SD artifact](#tc-001-013-removing-application-and-revert-application-version-from-sd-for-an-environment-via-sd-artifact)
  - [TC-001-014: Removing application and revert application version from SD for an Environment via SD content](#tc-001-014-removing-application-and-revert-application-version-from-sd-for-an-environment-via-sd-content)
  - [TC-001-015: Removing application and revert application version from SD for an Environment via several SD artifacts](#tc-001-015-removing-application-and-revert-application-version-from-sd-for-an-environment-via-several-sd-artifacts)
  - [TC-001-016: Removing application and revert application version from SD for an Environment via content of several SDs](#tc-001-016-removing-application-and-revert-application-version-from-sd-for-an-environment-via-content-of-several-sds)
  - [TC-001-017: Adding new application and update application version in `extended-merge` mode to SD for an Environment via SD content](#tc-001-017-adding-new-application-and-update-application-version-in-extended-merge-mode-to-sd-for-an-environment-via-sd-content)
  - [TC-001-018: Adding new application and update application version to SD for an Environment via SD content. SD version migration](#tc-001-018-adding-new-application-and-update-application-version-to-sd-for-an-environment-via-sd-content-sd-version-migration)

This describes test cases for the [SD Processing](/docs/sd-processing.md) feature

## TC-001-001: Adding SD for the first time for an Environment via SD artifact

**Status:** New

**Test Data:**

**Pre-requisites:**

- No Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:ver>` # Single app:ver
- `SD_SOURCE_TYPE`: `artifact`

**Expected Results:**

- Full SD with content obtained from `<app:ver>` artifact exist for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-002: Adding SD for the first time an Environment via SD content

**Status:** New

**Test Data:**

**Pre-requisites:**

- No Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SD-content>` # Single SD
- `SD_SOURCE_TYPE`: `json`

**Expected Results:**

- Full SD with content obtained from `<SD-content>` exist for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-003: Adding SD for the first time for an Environment via several SD artifacts

**Status:** New

**Test Data:**

**Pre-requisites:**

- No Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:vers>` # Multiple app:ver
- `SD_SOURCE_TYPE`: `artifact`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from artifacts `<app:vers>` exists for the Environment in the Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-004: Adding SD for the first time for an Environment via content of several SDs

**Status:** New

**Test Data:**

**Pre-requisites:**

- No Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SDs-content>` # Multiple SD
- `SD_SOURCE_TYPE`: `json`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from `<SDs-content>` exists for the Environment in the Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-005: Replace SD for an Environment via SD artifact

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:ver>` # Single app:ver
- `SD_SOURCE_TYPE`: `artifact`
- `SD_REPO_MERGE_MODE`: `replace`

**Expected Results:**

- Full SD with content obtained from `<app:ver>` artifact exist for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-006: Replace SD for an Environment via SD content

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SD-content>` # Single SD
- `SD_SOURCE_TYPE`: `json`
- `SD_REPO_MERGE_MODE`: `replace`

**Expected Results:**

- Full SD with content obtained from `<SD-content>` exist for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-007: Replace SD for an Environment via several SD artifacts

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SDs-content>` # Multiple SD
- `SD_SOURCE_TYPE`: `artifact`
- `SD_REPO_MERGE_MODE`: `replace`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from artifacts `<SDs-content>` exists for the Environment in the Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-008: Replace SD for an Environment via content of several SDs

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SDs-content>` # Multiple SD
- `SD_SOURCE_TYPE`: `json`
- `SD_REPO_MERGE_MODE`: `replace`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from `<SDs-content>` exists for the Environment in the Instance repository
- No Delta SD exists for the Environment in Instance repository

## TC-001-009: Adding new application and update application version to SD for an Environment via SD artifact

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:ver>` # Single app:ver of SD with new application and application with updated version
- `SD_SOURCE_TYPE`: `artifact`

**Expected Results:**

- Full SD with content obtained as a result of merging in `basic-merge` mode of SD retrieved from artifacts `<app:ver>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from artifact `<app:ver>` exist for the Environment in Instance repository

## TC-001-010: Adding new application and update application version to SD for an Environment via SD content

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SD-content>` # Single SD with new application and application with updated version
- `SD_SOURCE_TYPE`: `json`

**Expected Results:**

- Full SD with content obtained as a result of merging in `basic-merge` mode of SD retrieved from `<SD-content>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from `<SD-content>` exist for the Environment in Instance repository

## TC-001-011: Adding new application and update application version to SD for an Environment via several SD artifacts

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:vers>` # Multiple app:vers of SDs with new application and application with updated version
- `SD_SOURCE_TYPE`: `artifact`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from artifacts `<app:vers>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from artifact `<app:ver>` exist for the Environment in Instance repository

## TC-001-012: Adding new application and update application version to SD for an Environment via content of several SDs

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SDs-content>` # Multiple SDs with new application and application with updated version
- `SD_SOURCE_TYPE`: `json`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from `<SDs-content>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from `<SD-content>` exist for the Environment in Instance repository

## TC-001-013: Removing application and revert application version from SD for an Environment via SD artifact

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:ver>` # Single app:ver of SD with application to remove and application with updated version
- `SD_SOURCE_TYPE`: `artifact`
- `SD_DELTA`: `true`
- `SD_REPO_MERGE_MODE`: `basic-exclusion-merge`

**Expected Results:**

- Full SD with content obtained as a result of merging in `basic-exclusion-merge` mode of SD retrieved from artifacts `<app:ver>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from artifact `<app:ver>` exist for the Environment in Instance repository

## TC-001-014: Removing application and revert application version from SD for an Environment via SD content

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SD-content>` # Single SD with with application to remove and application with updated version
- `SD_SOURCE_TYPE`: `json`
- `SD_REPO_MERGE_MODE`: `basic-exclusion-merge`

**Expected Results:**

- Full SD with content obtained as a result of merging in `basic-exclusion-merge` mode of SD retrieved from `<SD-content>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from `<SD-content>` exist for the Environment in Instance repository

## TC-001-015: Removing application and revert application version from SD for an Environment via several SD artifacts

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:vers>` # Multiple app:vers of SDs with with application to remove and application with updated version
- `SD_SOURCE_TYPE`: `artifact`
- `SD_REPO_MERGE_MODE`: `basic-exclusion-merge`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from artifacts `<app:vers>` into previous Full SD (from pre-requisites) in `basic-exclusion-merge` mode exists for the Environment in the Instance repository
- Delta SD with content obtained from artifact `<app:ver>` exist for the Environment in Instance repository

## TC-001-016: Removing application and revert application version from SD for an Environment via content of several SDs

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SDs-content>` # Multiple SDs with with application to remove and application with updated version
- `SD_SOURCE_TYPE`: `json`
- `SD_REPO_MERGE_MODE`: `basic-exclusion-merge`

**Expected Results:**

- Full SD with content obtained as a result of sequential merging in `basic-merge` mode of SDs retrieved from `<SDs-content>` into previous Full SD (from pre-requisites) in `basic-exclusion-merge` mode exists for the Environment in the Instance repository
- Delta SD with content obtained from `<SD-content>` exist for the Environment in Instance repository

## TC-001-017: Adding new application and update application version in `extended-merge` mode to SD for an Environment via SD content

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_DATA`: `<SD-content>` # Single SD with new application and application with updated version
- `SD_SOURCE_TYPE`: `json`
- `SD_REPO_MERGE_MODE`: `extended-merge`

**Expected Results:**

- Full SD with content obtained as a result of merging in `extended-merge` mode of SD retrieved from `<SD-content>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from `<SD-content>` exist for the Environment in Instance repository

## TC-001-018: Adding new application and update application version to SD for an Environment via SD content. SD version migration

**Status:** New

**Test Data:**

**Pre-requisites:**

- Full SD **v2.1** exists for the Environment in Instance repository
- No Delta SD exists for the Environment in Instance repository

**Steps**:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `SD_VERSION`: `<app:ver>` # Single app:ver of SD **v2.2** with application to remove and application with updated version
- `SD_SOURCE_TYPE`: `artifact`

**Expected Results:**

- Full SD with content obtained as a result of merging in `basic-merge` mode of SD retrieved from artifacts `<app:ver>` into previous Full SD (from pre-requisites) exists for the Environment in the Instance repository
- Delta SD with content obtained from artifact `<app:ver>` exist for the Environment in Instance repository
