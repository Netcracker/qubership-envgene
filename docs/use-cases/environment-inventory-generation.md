# Environment Inventory Generation Use Cases

## Table of Contents

- [Overview](#overview)
- [Environment Inventory: env_definition.yml](#environment-inventory-env_definitionyml)
  - [UC-EINV-ED-1: Create `env_definition.yml` (`create_or_replace`, file does not exist)](#uc-einv-ed-1-create-env_definitionyml-create_or_replace-file-does-not-exist)
  - [UC-EINV-ED-2: Replace `env_definition.yml` (`create_or_replace`, file exists)](#uc-einv-ed-2-replace-env_definitionyml-create_or_replace-file-exists)
  - [UC-EINV-ED-3: Delete `env_definition.yml`](#uc-einv-ed-3-delete-env_definitionyml)
- [Environment Inventory: Paramsets](#environment-inventory-paramsets)
  - [UC-EINV-PS-1: Create paramset file (`create_or_replace`, file does not exist)](#uc-einv-ps-1-create-paramset-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-PS-2: Replace paramset file (`create_or_replace`, file exists)](#uc-einv-ps-2-replace-paramset-file-create_or_replace-file-exists)
  - [UC-EINV-PS-3: Delete paramset file](#uc-einv-ps-3-delete-paramset-file)
- [Environment Inventory: Credentials](#environment-inventory-credentials)
  - [UC-EINV-CR-1: Create credentials file (`create_or_replace`, file does not exist)](#uc-einv-cr-1-create-credentials-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-CR-2: Replace credentials file (`create_or_replace`, file exists)](#uc-einv-cr-2-replace-credentials-file-create_or_replace-file-exists)
  - [UC-EINV-CR-3: Delete credentials file](#uc-einv-cr-3-delete-credentials-file)
- [Environment Inventory: Resource Profile Overrides](#environment-inventory-resource-profile-overrides)
  - [UC-EINV-RP-1: Create resource profile override file (`create_or_replace`, file does not exist)](#uc-einv-rp-1-create-resource-profile-override-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-RP-2: Replace resource profile override file (`create_or_replace`, file exists)](#uc-einv-rp-2-replace-resource-profile-override-file-create_or_replace-file-exists)
  - [UC-EINV-RP-3: Delete resource profile override file](#uc-einv-rp-3-delete-resource-profile-override-file)
- [Environment Inventory: Shared Template Variable Files](#environment-inventory-shared-template-variable-files)
  - [UC-EINV-STV-1: Create Shared Template Variable file (`create_or_replace`, file does not exist)](#uc-einv-stv-1-create-shared-template-variable-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-STV-2: Replace Shared Template Variable file (`create_or_replace`, file exists)](#uc-einv-stv-2-replace-shared-template-variable-file-create_or_replace-file-exists)
  - [UC-EINV-STV-3: Delete Shared Template Variable file](#uc-einv-stv-3-delete-shared-template-variable-file)
  - [UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails (negative, atomic processing)](#uc-einv-at-all-1-rollback-all-inventory-changes-if-any-operation-fails-negative-atomic-processing)
- [Template Version Update](#template-version-update)
  - [UC-EINV-TV-1: Apply `ENV_TEMPLATE_VERSION` (`PERSISTENT` vs `TEMPORARY`)](#uc-einv-tv-1-apply-env_template_version-persistent-vs-temporary)

---

## Overview

This document describes use cases for **Environment Inventory Generation** — creating or replacing `env_definition.yml`, `paramsets`, `resource_profiles`, and `credentials` using `ENV_INVENTORY_CONTENT`, as well as template version update in `PERSISTENT` and `TEMPORARY` modes.

> **Note (template version priority):**  
> If `ENV_TEMPLATE_VERSION` is passed to the Instance pipeline, it has **higher priority** than the template version specified in `env_definition.yml` (`envDefinition.content.envTemplate.*`).

---

## Environment Inventory: env_definition.yml

### UC-EINV-ED-1: Create `env_definition.yml` (`create_or_replace`, file does not exist)

**Pre-requisites:**

1. The Environment Inventory file does not exist:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
- `ENV_TEMPLATE_VERSION: <template-artifact>` (optional; if provided, it has higher priority than the version from `envDefinition.content.envTemplate.*`)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `envDefinition` against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `envDefinition.action == create_or_replace`
      - `envDefinition.content` is present
   3. Validates `envDefinition.content` against `env_definition.yml` schema:
      - [`/docs/envgene-configs.md#env_definitionyml`](/docs/envgene-configs.md#env_definitionyml)
   4. Resolves target path:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
   5. Creates `Inventory/` directory if missing.
   6. Creates `env_definition.yml` using `envDefinition.content`.
   7. If `ENV_TEMPLATE_VERSION` is provided, applies it as the template version (higher priority).
2. The `git_commit` job runs:
   1. Commits created files into the Instance repository.

**Results:**

1. The file is created:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. If `ENV_TEMPLATE_VERSION` is provided, it overrides the version from `envDefinition.content.envTemplate.*`.
3. Changes are committed.

---

### UC-EINV-ED-2: Replace `env_definition.yml` (`create_or_replace`, file exists)

**Pre-requisites:**

1. The Environment Inventory file exists:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
- `ENV_TEMPLATE_VERSION: <template-artifact>` (optional; if provided, it has higher priority than the version from `envDefinition.content.envTemplate.*`)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `envDefinition` against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `envDefinition.action == create_or_replace`
      - `envDefinition.content` is present
   3. Validates `envDefinition.content` against `env_definition.yml` schema:
      - [`/docs/envgene-configs.md#env_definitionyml`](/docs/envgene-configs.md#env_definitionyml)
   4. Resolves target path:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
   5. Replaces `env_definition.yml` using `envDefinition.content` (fully overwrites the file).
   6. If `ENV_TEMPLATE_VERSION` is provided, applies it as the template version (higher priority).
2. The `git_commit` job runs:
   1. Commits updated files into the Instance repository.

**Results:**

1. The file is replaced (fully overwritten):
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. If `ENV_TEMPLATE_VERSION` is provided, it overrides the version from `envDefinition.content.envTemplate.*`.
3. Changes are committed.

---

### UC-EINV-ED-3: Delete `env_definition.yml`

1. The Environment Inventory file exists:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `envDefinition` against the request schema:
      - `envDefinition.action == delete`
      - `envDefinition.content` is not required
   3. Resolves target environment folder:
      - `/environments/<cluster-name>/<env-name>/`
   4. Deletes the entire environment directory:
      - `/environments/<cluster-name>/<env-name>/`

2. The `git_commit` job runs:
   1. Commits repository changes into the Instance repository.

**Results:**

1. The environment directory is removed:
   - `/environments/<cluster-name>/<env-name>/`

2. `env_definition.yml` is removed as part of the environment directory deletion (if it existed):
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

3. All Inventory-related files under the environment are removed as part of the environment directory deletion (if they existed):
   - `/environments/<cluster-name>/<env-name>/Inventory/parameters/*`
   - `/environments/<cluster-name>/<env-name>/Inventory/credentials/*`
   - `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/*`
   - `/environments/<cluster-name>/<env-name>/shared-template-variables/*`
4. Changes are committed.

---

## Environment Inventory: Paramsets

### UC-EINV-PS-1: Create paramset file (`create_or_replace`, file does not exist)

**Pre-requisites:**

1. The target paramset file does not exist (for the resolved `place` and `content.name`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `paramsets[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content.name: <paramset-name>`
- `content` is a valid Paramset file content

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `paramsets[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<paramset-name>` from `content.name`.
   4. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml`
      - `place=site` → `/environments/Inventory/parameters/<paramset-name>.yml`
   5. Creates `parameters/` directory if missing.
   6. Creates the paramset file using `content` (create-or-replace semantics; in this UC the file is expected to be missing).
2. The `git_commit` job runs:
   1. Commits created files into the Instance repository.

**Results:**

1. Paramset file is created at the resolved path.
2. File content matches `paramsets[].content`.
3. Changes are committed.

---

### UC-EINV-PS-2: Replace paramset file (`create_or_replace`, file exists)

**Pre-requisites:**

1. The target paramset file exists (for the resolved `place` and `content.name`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `paramsets[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content.name: <paramset-name>`
- `content` is a valid Paramset file content

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `paramsets[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place == { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<paramset-name>` from `content.name`.
   4. Resolves target path by `place`.
   5. Replaces the paramset file using `content` (fully overwrites the file).
2. The `git_commit` job runs:
   1. Commits updated files into the Instance repository.

**Results:**

1. Paramset file is replaced at the resolved path.
2. File content matches `paramsets[].content`.
3. Changes are committed.

---

### UC-EINV-PS-3: Delete paramSet file

**Pre-requisites:**

1. The target ParamSet file exists

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `paramsets[]`:

- `action: delete`
- `place: env | cluster | site`
- `content.name: <paramset-name>`
- `content` is a valid Paramset file content

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `paramSets[]` item against the request schema:
      - `action == delete`
      - `place == { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<paramset-name>` from `content.name`.
   4. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml`
      - `place=site` → `/environments/Inventory/parameters/<paramset-name>.yml`
   5. Deletes the target paramset file if it exists.
      - Directories are not removed.

2. The `git_commit` job runs:
   1. Commits repository changes into the Instance repository.

**Results:**

1. The paramset file is removed at the resolved path (if it existed).
2. Parent directories remain unchanged.
3. Changes are committed.

---

## Environment Inventory: Credentials

### UC-EINV-CR-1: Create credentials file (`create_or_replace`, file does not exist)

**Pre-requisites:**

1. The target credentials file does not exist (for the resolved `place`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `credentials[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content` is a credentials map (one or multiple credentials)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `content` is present
   3. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`
      - `place=cluster` → `/environments/<cluster-name>/Inventory/credentials/inventory_generation_creds.yml`
      - `place=site` → `/environments/credentials/inventory_generation_creds.yml`
   4. Creates `credentials/` directory if missing (for `env`/`cluster` levels).
   5. Creates the credentials file using `content` (create-or-replace semantics; in this UC the file is expected to be missing).
2. The `git_commit` job runs:
   1. Commits created files into the Instance repository.

**Results:**

1. Credentials file is created at the resolved path.
2. File content matches `credentials[].content`.
3. Changes are committed.

---

### UC-EINV-CR-2: Replace credentials file (`create_or_replace`, file exists)

**Pre-requisites:**

1. The target credentials file exists (for the resolved `place`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `credentials[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content` is a credentials map (one or multiple credentials)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `content` is present
   3. Resolves target path by `place`.
   4. Replaces the credentials file using `content` (fully overwrites the file).
2. The `git_commit` job runs:
   1. Commits updated files into the Instance repository.

**Results:**

1. Credentials file is replaced at the resolved path.
2. File content matches `credentials[].content`.
3. Changes are committed.

---

### UC-EINV-CR-3: Delete credentials file

**Pre-requisites:**

1. The target credentials file exists

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `credentials[]` with at least one item where:

- `action: delete`
- `place: env | cluster | site`
- `content` is present

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item against the request schema:
      - `action == delete`
      - `place ∈ { env, cluster, site }`
      - `content` is present
   3. Resolves target credentials file path by `place`.
   4. Deletes the target credentials file if it exists.
      - Directories are not removed.

2. The `git_commit` job runs:
   1. Commits repository changes into the Instance repository.

**Results:**

1. Credentials file is removed at the resolved path (if it existed).
2. Parent directories remain unchanged (no directory cleanup).
3. Changes are committed.

---

## Environment Inventory: Resource Profile Overrides

### UC-EINV-RP-1: Create resource profile override file (`create_or_replace`, file does not exist)

**Pre-requisites:**

1. The target override file does not exist (for the resolved `place` and `content.name`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `resourceProfiles[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content.name: <override-name>`
- `content` is a valid Resource Profile Override file content

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `resourceProfiles[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<override-name>` from `content.name`.
   4. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/Inventory/resource_profiles/<override-name>.yml`
      - `place=site` → `/environments/Inventory/resource_profiles/<override-name>.yml`
   5. Creates `resource_profiles/` directory if missing.
   6. Creates the override file using `content` (create-or-replace semantics; in this UC the file is expected to be missing).
2. The `git_commit` job runs:
   1. Commits created files into the Instance repository.

**Results:**

1. Override file is created at the resolved path.
2. File content matches `resourceProfiles[].content`.
3. Changes are committed.

---

### UC-EINV-RP-2: Replace resource profile override file (`create_or_replace`, file exists)

**Pre-requisites:**

1. The target override file exists (for the resolved `place` and `content.name`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `resourceProfiles[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `content.name: <override-name>`
- `content` is a valid Resource Profile Override file content

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `resourceProfiles[]` item against the request schema:
      - [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<override-name>` from `content.name`.
   4. Resolves target path by `place`.
   5. Replaces the override file using `content` (fully overwrites the file).
2. The `git_commit` job runs:
   1. Commits updated files into the Instance repository.

**Results:**

1. Override file is replaced at the resolved path.
2. File content matches `resourceProfiles[].content`.
3. Changes are committed.

---

### UC-EINV-RP-3: Delete resource profile override file

**Pre-requisites:**

1. The target Resource Profile Override file exists

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `resourceProfiles[]` with at least one item where:

- `action: delete`
- `place: env | cluster | site`
- `content.name: <override-name>`
- `content` is present (used to resolve the target file name)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `resourceProfiles[]` item against the request schema:
      - `action == delete`
      - `place ∈ { env, cluster, site }`
      - `content` is present and contains `name`
   3. Extracts `<override-name>` from `content.name`.
   4. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/resource_profiles/<override-name>.yml`
      - `place=site` → `/environments/resource_profiles/<override-name>.yml`
   5. Deletes the target override file if it exists.
      - Directories are not removed.

2. The `git_commit` job runs:
   1. Commits repository changes into the Instance repository.

**Results:**

1. Resource Profile Override file is removed at the resolved path (if it existed).
2. Parent directories remain unchanged (no directory cleanup).
3. Changes are committed.

---

## Environment Inventory: Shared Template Variable Files

### UC-EINV-STV-1: Create Shared Template Variable file (`create_or_replace`, file does not exist)

**Pre-requisites:**

1. The target Shared Template Variable file does not exist (for the resolved `place` and `name`):
   - `place=env` → `/environments/<cluster-name>/<env-name>/shared-template-variables/<name>.yml`
   - `place=cluster` → `/environments/<cluster-name>/shared-template-variables/<name>.yml`
   - `place=site` → `/environments/shared-template-variables/<name>.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: [`/docs/features/env-inventory-generation.md`](/docs/features/env-inventory-generation.md)

`ENV_INVENTORY_CONTENT` includes `sharedTemplateVariables[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `name: <file-name-without-extension>`
- `content`

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `sharedTemplateVariables[]` item against the request schema:
      - `/docs/features/env-inventory-generation.md`
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `name` is present
      - `content` is present
   3. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/shared-template-variables/<name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/shared-template-variables/<name>.yml`
      - `place=site` → `/environments/shared-template-variables/<name>.yml`
   4. Creates `shared-template-variables/` directory if missing.
   5. Creates the Shared Template Variable file using `content` (create-or-replace semantics; in this UC the file is expected to be missing).

2. The `git_commit` job runs:
   1. Commits created files into the Instance repository.

**Results:**

1. Shared Template Variable file is created at the resolved path.
2. File name is saved as `<name>.yml`.
3. File content matches `sharedTemplateVariables[].content`.
4. Changes are committed.

---

### UC-EINV-STV-2: Replace Shared Template Variable file (create_or_replace, file exists)

**Pre-requisites:**

1. The target Shared Template Variable file exists (for the resolved `place` and `name`):
   - `place=env` → `/environments/<cluster-name>/<env-name>/shared-template-variables/<name>.yml`
   - `place=cluster` → `/environments/<cluster-name>/shared-template-variables/<name>.yml`
   - `place=site` → `/environments/shared-template-variables/<name>.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: `/docs/features/env-inventory-generation.md`

`ENV_INVENTORY_CONTENT` includes `sharedTemplateVariables[]` with at least one item where:

- `action: create_or_replace`
- `place: env | cluster | site`
- `name: <file-name-without-extension>`
- `content`

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `sharedTemplateVariables[]` item against the request schema:
      - `/docs/features/env-inventory-generation.md`
      - `action == create_or_replace`
      - `place ∈ { env, cluster, site }`
      - `name` is present
      - `content` is present
   3. Resolves target path by `place`.
   4. Replaces the Shared Template Variable file using `content` (fully overwrites the file).

2. The `git_commit` job runs:
   1. Commits updated files into the Instance repository.

**Results:**

1. Shared Template Variable file is replaced at the resolved path.
2. File content matches `sharedTemplateVariables[].content`.
3. Changes are committed.

---

### UC-EINV-STV-3: Delete Shared Template Variable file

**Pre-requisites:**

1. The target Shared Template Variable file exists (for the resolved `place` and `name`):
   - `place=env` → `/environments/<cluster-name>/<env-name>/shared-template-variables/<name>.yml`
   - `place=cluster` → `/environments/<cluster-name>/shared-template-variables/<name>.yml`
   - `place=site` → `/environments/shared-template-variables/<name>.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: `/docs/features/env-inventory-generation.md`

`ENV_INVENTORY_CONTENT` includes `sharedTemplateVariables[]` with at least one item where:

- `action: delete`
- `place: env | cluster | site`
- `name: <file-name-without-extension>`

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `sharedTemplateVariables[]` item against the request schema:
      - `action == delete`
      - `place ∈ { env, cluster, site }`
      - `name` is present
   3. Resolves target path by `place`:
      - `place=env` → `/environments/<cluster-name>/<env-name>/shared-template-variables/<name>.yml`
      - `place=cluster` → `/environments/<cluster-name>/shared-template-variables/<name>.yml`
      - `place=site` → `/environments/shared-template-variables/<name>.yml`
   4. Deletes the target Shared Template Variable file if it exists.
      - Directories are not removed.

2. The `git_commit` job runs:
   1. Commits repository changes into the Instance repository.

**Results:**

1. Shared Template Variable file is removed at the resolved path (if it existed).
2. Parent directories remain unchanged (no directory cleanup).
3. Changes are committed.

---

### UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails (negative, atomic processing)

**Pre-requisites:**

1. Instance pipeline is started with `ENV_INVENTORY_CONTENT` that includes one or more Inventory operations (any combination of):
   - `envDefinition`
   - `paramSets[]`
   - `credentials[]`
   - `resourceProfiles[]`
   - `sharedTemplateVariables[]`
2. Repository has an initial state (files may exist or not exist).
3. At least one requested operation will fail during processing (validation error or file operation error).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_INVENTORY_CONTENT: <payload>`
  - Examples: `/docs/features/env-inventory-generation.md`

During processing of `ENV_INVENTORY_CONTENT`, at least one operation fails .

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Runs validations:
      - Parameter exclusivity validation:
        - If `ENV_INVENTORY_CONTENT` is provided together with `ENV_INVENTORY_INIT` or `ENV_SPECIFIC_PARAMS`, validation fails.
      - JSON schema validation:
        - `ENV_INVENTORY_CONTENT` is validated against `/schemas/env-inventory-content.schema.json`.
   3. Starts atomic processing of all requested operations (order between object types is not guaranteed).
   4. Applies some operations (examples of partial progress):
      - Creates required directories (e.g., `Inventory`, `parameters`, `credentials`, `resource_profiles`, `shared-template-variables`).
      - Creates or replaces files (e.g., `env_definition.yml`, paramset files, credential files, resource profile overrides, shared template variables).
   5. While processing one of operations, an error occurs:
      - Schema validation fails for one object content, **or**
      - Any file write/delete operation fails.
   6. Performs rollback:
      - Reverts all files created/changed during this job run.
      - Restores overwritten files to their previous state.
      - Removes directories/files created only during this run.
   7. Fails the job with a readable error message in logs.

2. The `git_commit` job does **not** commit any changes (because there must be no net changes after rollback).

**Results:**

1. No files are modified in the Instance repository after the pipeline run ).
2. Any files created during this run are removed.
3. Any overwritten files are restored to the original state.
4. Any directories created only during this run are removed.
5. Pipeline logs contain a readable error message explaining the failure reason.
6. No changes are committed.

---

## Template Version Update

### UC-EINV-TV-1: Apply `ENV_TEMPLATE_VERSION` (`PERSISTENT` vs `TEMPORARY`)

**Pre-requisites:**

1. Environment Inventory exists:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_TEMPLATE_VERSION: <template-artifact>`
- `ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT | TEMPORARY` (optional; default: `PERSISTENT`)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads `ENV_TEMPLATE_VERSION_UPDATE_MODE` (default: `PERSISTENT`).
   2. Applies `ENV_TEMPLATE_VERSION`:
      - **PERSISTENT**:
        - Updates template version in `env_definition.yml`
          (`envTemplate.artifact` or `envTemplate.templateArtifact.artifact.version`).
      - **TEMPORARY**:
        - Does not change `envTemplate.*` in `env_definition.yml`.
        - Writes the applied version into:
          - `generatedVersions.generateEnvironmentLatestVersion: "<ENV_TEMPLATE_VERSION>"`
2. The `git_commit` job runs:
   1. Commits updated `env_definition.yml` into the Instance repository.

**Results:**

1. **PERSISTENT**: template version in `env_definition.yml` is updated and committed.
2. **TEMPORARY**: `generatedVersions.generateEnvironmentLatestVersion` is updated and committed; `envTemplate.*` remains unchanged.
