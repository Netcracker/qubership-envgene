# Template Override Test Cases

- [Template Override Test Cases](#template-override-test-cases)
  - [TC-003-001: Using `templates_dir`](#tc-003-001-using-templates_dir)
  - [TC-003-002: Using `current_env.name`](#tc-003-002-using-current_envname)
  - [TC-003-003: Using `current_env.tenant`](#tc-003-003-using-current_envtenant)
  - [TC-003-004: Using `current_env.cloud`. `inventory.cloudName` set in Environment Inventory](#tc-003-004-using-current_envcloud-inventorycloudname-set-in-environment-inventory)
  - [TC-003-005: Using `current_env.cloud`. `inventory.cloudName` NOT set in Environment Inventory](#tc-003-005-using-current_envcloud-inventorycloudname-not-set-in-environment-inventory)
  - [TC-003-006: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` set in Environment Inventory](#tc-003-006-using-current_envcloudnamewithcluster-inventorycloudname-set-in-environment-inventory)
  - [TC-003-007: Using `current_env.cloudNameWithCluster`. `inventory.cloudPassport` set in Environment Inventory](#tc-003-007-using-current_envcloudnamewithcluster-inventorycloudpassport-set-in-environment-inventory)
  - [TC-003-008: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory](#tc-003-008-using-current_envcloudnamewithcluster-inventorycloudname-and-inventorycloudpassport-not-set-in-environment-inventory)
  - [TC-003-009: Using `current_env.cmdb_name`. `inventory.deployer` set in Environment Inventory](#tc-003-009-using-current_envcmdb_name-inventorydeployer-set-in-environment-inventory)
  - [TC-003-010: Using `current_env.cmdb_name`. `inventory.deployer` NOT set in Environment Inventory](#tc-003-010-using-current_envcmdb_name-inventorydeployer-not-set-in-environment-inventory)
  - [TC-003-011: Using `current_env.cmdb_url`. `inventory.deployer` set in Environment Inventory](#tc-003-011-using-current_envcmdb_url-inventorydeployer-set-in-environment-inventory)
  - [TC-003-012: Using `current_env.cmdb_url`. `inventory.deployer` NOT set in Environment Inventory](#tc-003-012-using-current_envcmdb_url-inventorydeployer-not-set-in-environment-inventory)
  - [TC-003-013: Using `current_env.description`. `inventory.description` set in Environment Inventory](#tc-003-013-using-current_envdescription-inventorydescription-set-in-environment-inventory)
  - [TC-003-014: Using `current_env.description`. `inventory.description` NOT set in Environment Inventory](#tc-003-014-using-current_envdescription-inventorydescription-not-set-in-environment-inventory)
  - [TC-003-015: Using `current_env.owners`. `inventory.owners` set in Environment Inventory](#tc-003-015-using-current_envowners-inventoryowners-set-in-environment-inventory)
  - [TC-003-016: Using `current_env.owners`. `inventory.owners` NOT set in Environment Inventory](#tc-003-016-using-current_envowners-inventoryowners-not-set-in-environment-inventory)
  - [TC-003-017: Using `current_env.env_template`](#tc-003-017-using-current_envenv_template)
  - [TC-003-018: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` set in Environment Inventory](#tc-003-018-using-current_envadditionaltemplatevariables-envtemplateadditionaltemplatevariables-set-in-environment-inventory)
  - [TC-003-019: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` NOT set in Environment Inventory](#tc-003-019-using-current_envadditionaltemplatevariables-envtemplateadditionaltemplatevariables-not-set-in-environment-inventory)
  - [TC-003-020: Using `current_env.cloud_passport`. `inventory.cloudPassport` set in Environment Inventory](#tc-003-020-using-current_envcloud_passport-inventorycloudpassport-set-in-environment-inventory)
  - [TC-003-021: Using `current_env.cloud_passport`. `inventory.cloudPassport` NOT set in Environment Inventory](#tc-003-021-using-current_envcloud_passport-inventorycloudpassport-not-set-in-environment-inventory)
  - [TC-003-022: Using `current_env.solution_structure`. SD exist in Instance repo](#tc-003-022-using-current_envsolution_structure-sd-exist-in-instance-repo)
  - [TC-003-023: Using `current_env.solution_structure`. SD NOT in Instance repo](#tc-003-023-using-current_envsolution_structure-sd-not-in-instance-repo)

Test Cases for [Template Macros](/docs/template-macros.md)

## TC-003-001: Using `templates_dir`

Status: Not Implemented

Pre-requisites:

- Template Descriptor uses `templates_dir` in attributes:
  - `tenant`
  - `cloud`
  - `namespaces.template_path`

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Operation completed successfully

## TC-003-002: Using `current_env.name`

Status: Not Implemented

Pre-requisites:

- Namespace template uses `current_env.name` in attributes:
  - `name`
  - `labels`
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.name` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Environment Inventory has `inventory.environmentName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.name` was substituted with value from `inventory.environmentName` in Environment Inventory

## TC-003-003: Using `current_env.tenant`

Status: Not Implemented

Pre-requisites:

- Tenant template uses `current_env.tenant` in `name` attribute
- Environment Inventory has `inventory.tenantName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.tenant` was substituted with value from `inventory.tenantName` in Environment Inventory

## TC-003-004: Using `current_env.cloud`. `inventory.cloudName` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cloud` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cloud` was substituted with value from `inventory.cloudName` in Environment Inventory

## TC-003-005: Using `current_env.cloud`. `inventory.cloudName` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cloud` in `name` attribute
- Environment Inventory does NOT have `inventory.cloudName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cloud` was substituted with value from `inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-006: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `inventory.cloudName` in Environment Inventory

## TC-003-007: Using `current_env.cloudNameWithCluster`. `inventory.cloudPassport` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudPassport` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `inventory.cloudPassport_inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-008: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `<name of cluster folder>_inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-009: Using `current_env.cmdb_name`. `inventory.deployer` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cmdb_name` in `e2eParameters` attribute
- Environment Inventory has `inventory.deployer` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cmdb_name` was substituted with value from `inventory.deployer` in Environment Inventory

## TC-003-010: Using `current_env.cmdb_name`. `inventory.deployer` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cmdb_name` in `e2eParameters` attribute
- Environment Inventory does NOT have `inventory.deployer` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Operation failed

## TC-003-011: Using `current_env.cmdb_url`. `inventory.deployer` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cmdb_url` in `e2eParameters` attribute
- Environment Inventory has `inventory.deployer` attribute set
- Instance repository has configured deployer specified in `inventory.deployer` attribute

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Cloud in Environment Instance contains values where `current_env.cmdb_url` was substituted with value from `deployerUrl` in deployer configuration, whose name is specified in `inventory.deployer` in Environment Inventory

## TC-003-012: Using `current_env.cmdb_url`. `inventory.deployer` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.cmdb_url` in `e2eParameters` attribute
- Environment Inventory does NOT have `inventory.deployer` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Operation failed

## TC-003-013: Using `current_env.description`. `inventory.description` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Tenant template uses `current_env.description` in `description` attribute
- Environment Inventory has `inventory.description` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.description` was substituted with value from `inventory.description` in Environment Inventory

## TC-003-014: Using `current_env.description`. `inventory.description` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Tenant template uses `current_env.description` in `description` attribute
- Environment Inventory does NOT have `inventory.description` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.description` was substituted with value `""`

## TC-003-015: Using `current_env.owners`. `inventory.owners` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Tenant template uses `current_env.owners` in `description` attribute
- Environment Inventory has `inventory.owners` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.owners` was substituted with value from `inventory.owners` in Environment Inventory

## TC-003-016: Using `current_env.owners`. `inventory.owners` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Tenant template uses `current_env.owners` in `description` attribute
- Environment Inventory does NOT have `inventory.owners` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.owners` was substituted with value `""`

## TC-003-017: Using `current_env.env_template`

Status: Not Implemented

Pre-requisites:

- Cloud template uses `current_env.env_template` in `e2eParameters` attribute
- Environment Inventory has `envTemplate.name` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Tenant in Environment Instance contains values where `current_env.env_template` was substituted with value from `envTemplate.name` in Environment Inventory

## TC-003-018: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.additionalTemplateVariables` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.additionalTemplateVariables` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Environment Inventory has `envTemplate.additionalTemplateVariables` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.additionalTemplateVariables` was substituted with value from `envTemplate.additionalTemplateVariables` in Environment Inventory

## TC-003-019: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.additionalTemplateVariables` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.additionalTemplateVariables` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Environment Inventory does NOT have `envTemplate.additionalTemplateVariables` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.additionalTemplateVariables` was substituted with value `{}`

## TC-003-020: Using `current_env.cloud_passport`. `inventory.cloudPassport` set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.cloud_passport` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.cloud_passport` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Environment Inventory has `inventory.cloudPassport` attribute set
- Instance repo contains valid Cloud Passport

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.cloud_passport` was substituted with contents of Cloud Passport specified in `inventory.cloudPassport` in Environment Inventory

## TC-003-021: Using `current_env.cloud_passport`. `inventory.cloudPassport` NOT set in Environment Inventory

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.cloud_passport` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.cloud_passport` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Environment Inventory does NOT have `inventory.cloudPassport` attribute set

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.cloud_passport` was substituted with value `{}`

## TC-003-022: Using `current_env.solution_structure`. SD exist in Instance repo

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.solution_structure` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.solution_structure` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Instance repo contains valid SD for this environment

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.solution_structure` was substituted with value obtained according to principles described [here](/docs/template-macros.md#current_envsolution_structure)

## TC-003-023: Using `current_env.solution_structure`. SD NOT in Instance repo

Status: Not Implemented

Pre-requisites:

- Namespace template uses (including if/else Jinja expressions) `current_env.solution_structure` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.solution_structure` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Instance repo doesnn't contain SD for this environment

Inputs:

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

Results:

- Namespace in Environment Instance contains values where `current_env.solution_structure` was substituted with value `{}`
