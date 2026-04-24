# Automatic Environment Name Derivation Use Cases

- [Automatic Environment Name Derivation Use Cases](#automatic-environment-name-derivation-use-cases)
  - [Overview](#overview)
  - [Environment Name Derivation Scenarios](#environment-name-derivation-scenarios)
    - [UC-AEN-END-1: Environment with no explicit environmentName defined](#uc-aen-end-1-environment-with-no-explicit-environmentname-defined)
    - [UC-AEN-END-2: Environment with explicit environmentName defined](#uc-aen-end-2-environment-with-explicit-environmentname-defined)
    - [UC-AEN-END-3: Environment with explicit environmentName different from folder name](#uc-aen-end-3-environment-with-explicit-environmentname-different-from-folder-name)
    - [UC-AEN-END-4: Invalid folder structure for environment](#uc-aen-end-4-invalid-folder-structure-for-environment)
    - [UC-AEN-END-5: Template rendering with derived environment name](#uc-aen-end-5-template-rendering-with-derived-environment-name)

## Overview

This document describes use cases for automatic environment name derivation.

Feature reference: [Automatic Environment Name Derivation](/docs/features/auto-env-name-derivation.md).

## Environment Name Derivation Scenarios

### UC-AEN-END-1: Environment with no explicit environmentName defined

**Pre-requisites:**

1. Environment definition file exists at path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`.
2. The `environmentName` attribute is not defined in `env_definition.yml`:

    ```yaml
    inventory:
      # environmentName is not defined
      tenantName: "Applications"
      cloudName: "cluster01"
    envTemplate:
      name: "simple"
      artifact: "project-env-template:master_20231024-080204"
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env01`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_build` job runs in the pipeline.
2. EnvGene reads environment path from `ENV_NAMES`.
3. EnvGene loads `env_definition.yml` and determines environment name.

**Results:**

1. The environment is successfully created.
2. The environment name is derived from the folder name `env01`.
3. The environment context contains `current_env.name` with the value `env01`.
4. The generated environment instance references the correct environment name.

### UC-AEN-END-2: Environment with explicit environmentName defined

**Pre-requisites:**

1. Environment definition file exists at path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`.
2. The `environmentName` attribute is explicitly defined in `env_definition.yml`:

    ```yaml
    inventory:
      environmentName: "env02"
      tenantName: "Applications"
      cloudName: "cluster01"
    envTemplate:
      name: "simple"
      artifact: "project-env-template:master_20231024-080204"
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env02`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_build` job runs in the pipeline.
2. EnvGene reads environment path from `ENV_NAMES`.
3. EnvGene loads `env_definition.yml` and uses explicit `environmentName`.

**Results:**

1. The environment is successfully created.
2. The explicitly defined environment name `env02` is used.
3. The environment context contains `current_env.name` with the value `env02`.
4. The generated environment instance references the correct environment name.

### UC-AEN-END-3: Environment with explicit environmentName different from folder name

**Pre-requisites:**

1. Environment definition file exists at path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`.
2. The `environmentName` attribute is explicitly defined with a value different from folder name:

    ```yaml
    inventory:
      environmentName: "custom-env"
      tenantName: "Applications"
      cloudName: "cluster01"
    envTemplate:
      name: "simple"
      artifact: "project-env-template:master_20231024-080204"
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env03`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_build` job runs in the pipeline.
2. EnvGene reads environment path from `ENV_NAMES`.
3. EnvGene loads `env_definition.yml` and uses explicit `environmentName`.

**Results:**

1. The environment is successfully created.
2. The explicitly defined environment name `custom-env` is used instead of folder name.
3. The environment context contains `current_env.name` with the value `custom-env`.
4. The generated environment instance references the correct environment name.

### UC-AEN-END-4: Invalid folder structure for environment

**Pre-requisites:**

1. Environment definition file exists at invalid path that does not follow expected structure.
2. The `environmentName` attribute is not defined in `env_definition.yml`:

    ```yaml
    inventory:
      # environmentName is not defined
      tenantName: "Applications"
      cloudName: "cluster01"
    envTemplate:
      name: "simple"
      artifact: "project-env-template:master_20231024-080204"
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: invalid-structure`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_build` job runs in the pipeline.
2. EnvGene attempts to determine environment name from path.
3. EnvGene detects invalid folder structure.

**Results:**

1. Environment creation fails with an appropriate error message.
2. The error message indicates that environment name could not be determined from path.
3. The error message suggests checking folder structure.

### UC-AEN-END-5: Template rendering with derived environment name

**Pre-requisites:**

1. Environment definition file exists at path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`.
2. The `environmentName` attribute is not defined in `env_definition.yml`.
3. Environment template contains references to `current_env.name`:

    ```yaml
    # cloud.yml.j2
    name: "{{ current_env.name }}-cloud"
    description: "Cloud for {{ current_env.name }} environment"
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env04`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_build` job runs in the pipeline.
2. EnvGene derives environment name from folder path.
3. EnvGene renders template with `current_env.name`.

**Results:**

1. The environment is successfully created.
2. The environment name is derived from folder name `env04`.
3. The template is rendered with derived environment name:

    ```yaml
    # Rendered cloud.yml
    name: "env04-cloud"
    description: "Cloud for env04 environment"
    ```

4. All template variables referencing `current_env.name` are substituted with derived name.
