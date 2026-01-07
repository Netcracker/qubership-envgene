# Environment Inventory Generation Use Cases

## Table of Contents

- [Overview](#overview)
- [Environment Inventory: env_definition.yml](#environment-inventory-env_definitionyml)
  - [UC-EINV-ED-1: Create `env_definition.yml` (`create_or_replace`, file does not exist)](#uc-einv-ed-1-create-env_definitionyml-create_or_replace-file-does-not-exist)
  - [UC-EINV-ED-2: Replace `env_definition.yml` (`create_or_replace`, file exists)](#uc-einv-ed-2-replace-env_definitionyml-create_or_replace-file-exists)
- [Environment Inventory: Paramsets](#environment-inventory-paramsets)
  - [UC-EINV-PS-1: Create paramset file (`create_or_replace`, file does not exist)](#uc-einv-ps-1-create-paramset-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-PS-2: Replace paramset file (`create_or_replace`, file exists)](#uc-einv-ps-2-replace-paramset-file-create_or_replace-file-exists)
- [Environment Inventory: Credentials](#environment-inventory-credentials)
  - [UC-EINV-CR-1: Create credentials file (`create_or_replace`, file does not exist)](#uc-einv-cr-1-create-credentials-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-CR-2: Replace credentials file (`create_or_replace`, file exists)](#uc-einv-cr-2-replace-credentials-file-create_or_replace-file-exists)
- [Environment Inventory: Resource Profile Overrides](#environment-inventory-resource-profile-overrides)
  - [UC-EINV-RP-1: Create resource profile override file (`create_or_replace`, file does not exist)](#uc-einv-rp-1-create-resource-profile-override-file-create_or_replace-file-does-not-exist)
  - [UC-EINV-RP-2: Replace resource profile override file (`create_or_replace`, file exists)](#uc-einv-rp-2-replace-resource-profile-override-file-create_or_replace-file-exists)
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
      - `place ∈ { env, cluster, site }`
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
