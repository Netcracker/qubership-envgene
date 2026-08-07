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
(default: `PERSISTENT`). Optional
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) selects whether the version updates
the common template artefact or a Blue-Green `origin` / `peer` artefact.

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

> [!NOTE]
> One of the following `BG_NS_TARGET` conditions applies:

1. Instance pipeline is started with `ENV_TEMPLATE_VERSION` and without `BG_NS_TARGET` (common artefact)
2. Instance pipeline is started with `ENV_TEMPLATE_VERSION` and `BG_NS_TARGET: origin`
3. Instance pipeline is started with `ENV_TEMPLATE_VERSION` and `BG_NS_TARGET: peer`

Also:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT | TEMPORARY` (optional; default: `PERSISTENT`)

**Steps:**

1. The `env_inventory_generation` job runs:
   1. Reads `ENV_TEMPLATE_VERSION_UPDATE_MODE` (default: `PERSISTENT`).
   2. Reads `BG_NS_TARGET` when present (`peer` or `origin`).
   3. Applies `ENV_TEMPLATE_VERSION`:
      - **PERSISTENT** without `BG_NS_TARGET`:
        - Updates `envTemplate.artifact` or `envTemplate.templateArtifact.artifact.version` in
          `env_definition.yml`.
      - **PERSISTENT** with `BG_NS_TARGET: origin`:
        - Updates `envTemplate.bgNsArtifacts.origin` in `env_definition.yml`.
      - **PERSISTENT** with `BG_NS_TARGET: peer`:
        - Updates `envTemplate.bgNsArtifacts.peer` in `env_definition.yml`.
      - **TEMPORARY** (any `BG_NS_TARGET` value, including unset):
        - Does not change `envTemplate.artifact`, `envTemplate.templateArtifact`, or
          `envTemplate.bgNsArtifacts` in `env_definition.yml`.
        - Writes the applied version into:
          - `generatedVersions.generateEnvironmentLatestVersion: "<ENV_TEMPLATE_VERSION>"`
2. The `git_commit` job runs:
   1. Commits updated `env_definition.yml` into the Instance repository.

**Results:**

1. **PERSISTENT** without `BG_NS_TARGET`: common template version in `env_definition.yml` is updated
   and committed.
2. **PERSISTENT** with `BG_NS_TARGET: origin` or `peer`: the matching `bgNsArtifacts` field is updated
   and committed. Other template artefact fields are unchanged.
3. **TEMPORARY**: `generatedVersions.generateEnvironmentLatestVersion` is updated and committed.
   `envTemplate.*` remains unchanged.
