# Automatic Environment Name Derivation Test Cases

- [Automatic Environment Name Derivation Test Cases](#automatic-environment-name-derivation-test-cases)
  - [TC-003-001: Environment with no explicit environmentName defined](#tc-003-001-environment-with-no-explicit-environmentname-defined)
  - [TC-003-002: Environment with explicit environmentName defined](#tc-003-002-environment-with-explicit-environmentname-defined)
  - [TC-003-003: Environment with explicit environmentName different from folder name](#tc-003-003-environment-with-explicit-environmentname-different-from-folder-name)
  - [TC-003-004: Invalid folder structure for environment](#tc-003-004-invalid-folder-structure-for-environment)
  - [TC-003-005: Template rendering with derived environment name](#tc-003-005-template-rendering-with-derived-environment-name)

This describes test cases for the [Automatic Environment Name Derivation](/docs/features/auto-environment-name.md) feature

## TC-003-001: Environment with no explicit environmentName defined

**Status:** Active

**Test Data:**

- test_environments/cluster01/env01/Inventory/env_definition.yml (without environmentName)

**Pre-requisites:**

- Environment definition file exists at the path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`
- The `environmentName` attribute is not defined in the env_definition.yml file:

```yaml
inventory:
  # environmentName is not defined
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

**Steps:**

- `ENV_NAMES`: `cluster01/env01` # Environment path
- `ENV_BUILDER`: `true`

**Expected Results:**

- The environment is successfully created
- The environment name is derived from the folder name "env01"
- The environment context contains `current_env.name` with the value "env01"
- The generated environment instance references the correct environment name

## TC-003-002: Environment with explicit environmentName defined

**Status:** Active

**Test Data:**

- test_environments/cluster01/env02/Inventory/env_definition.yml (with environmentName)

**Pre-requisites:**

- Environment definition file exists at the path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`
- The `environmentName` attribute is explicitly defined in the env_definition.yml file:

```yaml
inventory:
  environmentName: "env02"  # Explicitly defined
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

**Steps:**

- `ENV_NAMES`: `cluster01/env02` # Environment path
- `ENV_BUILDER`: `true`

**Expected Results:**

- The environment is successfully created
- The explicitly defined environment name "env02" is used
- The environment context contains `current_env.name` with the value "env02"
- The generated environment instance references the correct environment name

## TC-003-003: Environment with explicit environmentName different from folder name

**Status:** Active

**Test Data:**

- test_environments/cluster01/env03/Inventory/env_definition.yml (with custom environmentName)

**Pre-requisites:**

- Environment definition file exists at the path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`
- The `environmentName` attribute is explicitly defined with a value different from the folder name:

```yaml
inventory:
  environmentName: "custom-env"  # Different from folder name "env03"
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

**Steps:**

- `ENV_NAMES`: `cluster01/env03` # Environment path
- `ENV_BUILDER`: `true`

**Expected Results:**

- The environment is successfully created
- The explicitly defined environment name "custom-env" is used instead of the folder name
- The environment context contains `current_env.name` with the value "custom-env"
- The generated environment instance references the correct environment name

## TC-003-004: Invalid folder structure for environment

**Status:** Active

**Test Data:**

- test_environments/invalid-structure/Inventory/env_definition.yml (without environmentName)

**Pre-requisites:**

- Environment definition file exists at an invalid path that doesn't follow the expected structure
- The `environmentName` attribute is not defined in the env_definition.yml file:

```yaml
inventory:
  # environmentName is not defined
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

**Steps:**

- `ENV_NAMES`: `invalid-structure` # Invalid environment path
- `ENV_BUILDER`: `true`

**Expected Results:**

- The environment creation fails with an appropriate error message
- The error message indicates that the environment name could not be determined from the path
- The error message suggests checking the folder structure

## TC-003-005: Template rendering with derived environment name

**Status:** Active

**Test Data:**

- test_environments/cluster01/env04/Inventory/env_definition.yml (without environmentName)
- test_templates/env_templates/test-template/cloud.yml.j2 (with references to current_env.name)

**Pre-requisites:**

- Environment definition file exists at the path `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`
- The `environmentName` attribute is not defined in the env_definition.yml file
- The environment template contains references to `current_env.name`:

```yaml
# cloud.yml.j2
name: "{{ current_env.name }}-cloud"
description: "Cloud for {{ current_env.name }} environment"
```

**Steps:**

- `ENV_NAMES`: `cluster01/env04` # Environment path
- `ENV_BUILDER`: `true`

**Expected Results:**

- The environment is successfully created
- The environment name is derived from the folder name "env04"
- The template is correctly rendered with the derived environment name:
  ```yaml
  # Rendered cloud.yml
  name: "env04-cloud"
  description: "Cloud for env04 environment"
  ```
- All template variables referencing `current_env.name` are correctly substituted with the derived name
