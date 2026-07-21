# Template Version Update Use Cases

## Table of Contents

- [Template Version Update Use Cases](#template-version-update-use-cases)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Template Version Update](#template-version-update)
    - [UC-TV-1: Apply `ENV_TEMPLATE_VERSION` (`PERSISTENT` vs `TEMPORARY`)](#uc-tv-1-apply-env_template_version-persistent-vs-temporary)

---

## Overview

This document describes use cases for **Template Version Update** - applying
[`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version) to an Environment. The
mode is selected with
[`ENV_TEMPLATE_VERSION_UPDATE_MODE`](/docs/instance-pipeline-parameters.md#env_template_version_update_mode)
(default: `PERSISTENT`).

> **Note (template version priority):**  
> If `ENV_TEMPLATE_VERSION` is passed to the Instance pipeline, it has **higher priority** than the template
> version specified in `env_definition.yml` (`envDefinition.content.envTemplate.*`).

---

## Template Version Update

Applying `ENV_TEMPLATE_VERSION` to an Environment in `PERSISTENT` or `TEMPORARY` mode.

### UC-TV-1: Apply `ENV_TEMPLATE_VERSION` (`PERSISTENT` vs `TEMPORARY`)

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
2. **TEMPORARY**: `generatedVersions.generateEnvironmentLatestVersion` is updated and committed. `envTemplate.*` remains unchanged.
