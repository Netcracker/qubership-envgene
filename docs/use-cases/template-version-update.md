# Template Version Update Use Cases

## Table of Contents

- [Template Version Update Use Cases](#template-version-update-use-cases)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Template Version Update](#template-version-update)
    - [UC-TV-1: Apply `ENV_TEMPLATE_VERSION` in `PERSISTENT` mode](#uc-tv-1-apply-env_template_version-in-persistent-mode)
    - [UC-TV-2: Apply `ENV_TEMPLATE_VERSION` in `TEMPORARY` mode](#uc-tv-2-apply-env_template_version-in-temporary-mode)

---

## Overview

This document describes use cases for **Template Version Update** - applying
[`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version) to an Environment with
the `set_template_version` pipeline step. The mode is selected with
[`ENV_TEMPLATE_VERSION_UPDATE_MODE`](/docs/instance-pipeline-parameters.md#env_template_version_update_mode)
(default: `PERSISTENT`).

The job runs after Environment Inventory generation. Because of that order, the version passed in
`ENV_TEMPLATE_VERSION` overrides the template version arriving in `envDefinition.content.envTemplate.*` of
[`ENV_INVENTORY_CONTENT`](/docs/features/env-inventory-generation.md#env_inventory_content).

---

## Template Version Update

Applying `ENV_TEMPLATE_VERSION` to an Environment in one of the two update modes.

### UC-TV-1: Apply `ENV_TEMPLATE_VERSION` in `PERSISTENT` mode

**Pre-requisites:**

1. The Environment Inventory exists, or is generated earlier in the same pipeline run:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_TEMPLATE_VERSION: <template-artifact>`
- `ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT` (optional, default)

**Steps:**

1. The `set_template_version` job runs:
   1. Updates the template version in `env_definition.yml`
      (`envTemplate.artifact` or `envTemplate.templateArtifact.artifact.version`).
2. The `git_commit` job runs:
   1. Commits updated `env_definition.yml` into the Instance repository.

**Results:**

1. The template version in `env_definition.yml` is updated and committed.

---

### UC-TV-2: Apply `ENV_TEMPLATE_VERSION` in `TEMPORARY` mode

**Pre-requisites:**

1. The Environment Inventory exists, or is generated earlier in the same pipeline run:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with:

- `ENV_NAMES: <cluster-name>/<env-name>`
- `ENV_TEMPLATE_VERSION: <template-artifact>`
- `ENV_TEMPLATE_VERSION_UPDATE_MODE: TEMPORARY`

**Steps:**

1. The `set_template_version` job runs:
   1. Does not change `env_definition.yml`. The version is applied to the current pipeline run only.
2. If the environment is rendered in the same run (`env_build`),
   `generatedVersions.generateEnvironmentLatestVersion` in `env_definition.yml` is updated with the
   template version actually used.
3. The `git_commit` job runs:
   1. Commits updated files, if any, into the Instance repository.

**Results:**

1. `envTemplate.*` remains unchanged.
2. When the environment is rendered in the same run, `generatedVersions.generateEnvironmentLatestVersion`
   reflects the applied version and is committed.
