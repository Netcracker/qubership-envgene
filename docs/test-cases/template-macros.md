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
  - [TC-003-022: Using `current_env.solution_structure`. SD exist in Instance repository](#tc-003-022-using-current_envsolution_structure-sd-exist-in-instance-repository)
  - [TC-003-023: Using `current_env.solution_structure`. SD NOT in Instance repository](#tc-003-023-using-current_envsolution_structure-sd-not-in-instance-repository)
  - [TC-003-024: Using `current_env.cluster.name`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory](#tc-003-024-using-current_envclustername-inventorycloudname-and-inventorycloudpassport-not-set-in-environment-inventory)
  - [TC-003-025: Using `current_env.cluster.name`. `inventory.cloudName` and `inventory.cloudPassport` set in Environment Inventory](#tc-003-025-using-current_envclustername-inventorycloudname-and-inventorycloudpassport-set-in-environment-inventory)

Test Cases for [Template Macros](/docs/template-macros.md)

## TC-003-001: Using `templates_dir`

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1.yaml
- test_data/test_templates/env_templates/test-template-2.yaml

**Pre-requisites:**

- Template Descriptor uses `templates_dir` in attributes:
  - `tenant`
  - `cloud`
  - `namespaces.template_path`

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Operation completed successfully

## TC-003-002: Using `current_env.name`

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/Namespaces/app.yml.j2
- test_data/test_templates/parameters/app/Namespaces/test-parameters-1.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

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

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.name` was substituted with value from `inventory.environmentName` in Environment Inventory

## TC-003-003: Using `current_env.tenant`

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/tenant.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Tenant template uses `current_env.tenant` in `name` attribute
- Environment Inventory has `inventory.tenantName` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.tenant` was substituted with value from `inventory.tenantName` in Environment Inventory

## TC-003-004: Using `current_env.cloud`. `inventory.cloudName` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/cloud.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cloud` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cloud` was substituted with value from `inventory.cloudName` in Environment Inventory

## TC-003-005: Using `current_env.cloud`. `inventory.cloudName` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cloud` in `name` attribute
- Environment Inventory does NOT have `inventory.cloudName` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cloud` was substituted with value from `inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-006: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `inventory.cloudName` in Environment Inventory

## TC-003-007: Using `current_env.cloudNameWithCluster`. `inventory.cloudPassport` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudPassport` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `inventory.cloudPassport_inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-008: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cloudNameWithCluster` in `name` attribute
- Environment Inventory has `inventory.cloudName` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cloudNameWithCluster` was substituted with value from `<name of cluster folder>_inventory.environmentName.replace("-","_")` in Environment Inventory

## TC-003-009: Using `current_env.cmdb_name`. `inventory.deployer` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/cloud.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cmdb_name` in `e2eParameters` attribute
- Environment Inventory has `inventory.deployer` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cmdb_name` was substituted with value from `inventory.deployer` in Environment Inventory

## TC-003-010: Using `current_env.cmdb_name`. `inventory.deployer` NOT set in Environment Inventory

**Status:** New

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cmdb_name` in `e2eParameters` attribute
- Environment Inventory does NOT have `inventory.deployer` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Operation failed

## TC-003-011: Using `current_env.cmdb_url`. `inventory.deployer` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/cloud.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cmdb_url` in `e2eParameters` attribute
- Environment Inventory has `inventory.deployer` attribute set
- Instance repository has configured deployer specified in `inventory.deployer` attribute

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud in Environment Instance contains values where `current_env.cmdb_url` was substituted with value from `deployerUrl` in deployer configuration, whose name is specified in `inventory.deployer` in Environment Inventory

## TC-003-012: Using `current_env.cmdb_url`. `inventory.deployer` NOT set in Environment Inventory

**Status:** New

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.cmdb_url` in `e2eParameters` attribute
- Environment Inventory does NOT have `inventory.deployer` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Operation failed

## TC-003-013: Using `current_env.description`. `inventory.description` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/tenant.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Tenant template uses `current_env.description` in `description` attribute
- Environment Inventory has `inventory.description` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.description` was substituted with value from `inventory.description` in Environment Inventory

## TC-003-014: Using `current_env.description`. `inventory.description` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/tenant.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Tenant template uses `current_env.description` in `description` attribute
- Environment Inventory does NOT have `inventory.description` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.description` was substituted with value `""`

## TC-003-015: Using `current_env.owners`. `inventory.owners` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/tenant.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Tenant template uses `current_env.owners` in `description` attribute
- Environment Inventory has `inventory.owners` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.owners` was substituted with value from `inventory.owners` in Environment Inventory

## TC-003-016: Using `current_env.owners`. `inventory.owners` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/tenant.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

- Tenant template uses `current_env.owners` in `description` attribute
- Environment Inventory does NOT have `inventory.owners` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.owners` was substituted with value `""`

## TC-003-017: Using `current_env.env_template`

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/cloud.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

- Cloud template uses `current_env.env_template` in `e2eParameters` attribute
- Environment Inventory has `envTemplate.name` attribute set

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Tenant in Environment Instance contains values where `current_env.env_template` was substituted with value from `envTemplate.name` in Environment Inventory

## TC-003-018: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/Namespaces/app.yml.j2
- test_data/test_templates/parameters/app/test-parameters-1.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

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

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.additionalTemplateVariables` was substituted with value from `envTemplate.additionalTemplateVariables` in Environment Inventory

## TC-003-019: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/Namespaces/app.yml.j2
- test_data/test_templates/parameters/app/test-parameters-1.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

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

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.additionalTemplateVariables` was substituted with value `{}`

## TC-003-020: Using `current_env.cloud_passport`. `inventory.cloudPassport` set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/cloud.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/env_definition.yml

**Pre-requisites:**

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
- Instance repository contains valid Cloud Passport

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.cloud_passport` was substituted with contents of Cloud Passport specified in `inventory.cloudPassport` in Environment Inventory

## TC-003-021: Using `current_env.cloud_passport`. `inventory.cloudPassport` NOT set in Environment Inventory

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/cloud.yml.j2
- test_data/test_environments/cluster01/env04/Inventory/env_definition.yml

**Pre-requisites:**

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

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.cloud_passport` was substituted with value `{}`

## TC-003-022: Using `current_env.solution_structure`. SD exist in Instance repository

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-1/Namespaces/app.yml.j2
- test_data/test_templates/parameters/app/test-parameters-1.yml.j2
- test_data/test_environments/cluster01/env03/Inventory/solution-descriptor/sd.yaml

**Pre-requisites:**

- Namespace template uses (including if/else Jinja expressions) `current_env.solution_structure` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.solution_structure` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Instance repository contains valid SD for this environment

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.solution_structure` was substituted with value obtained according to principles described in [Solution Structure](/docs/template-macros.md#current_envsolution_structure)

## TC-003-023: Using `current_env.solution_structure`. SD NOT in Instance repository

**Status:** Active

**Test Data:**

- test_data/test_templates/env_templates/test-template-2/Namespaces/app.yml.j2
- test_data/test_templates/parameters/app/test-parameters-1.yml.j2
- test_data/test_environments/cluster01/env04/Inventory

**Pre-requisites:**

- Namespace template uses (including if/else Jinja expressions) `current_env.solution_structure` in attributes:
  - `deployParameters`
  - `e2eParameters`
  - `technicalConfigurationParameters`
- Paramsets in Template repository use `current_env.solution_structure` in `parameters` attribute
- Paramsets are associated with namespace via:
  - `deployParameterSets`
  - `e2eParameterSets`
  - `technicalConfigurationParameterSets`
- Instance repository doesn't contain SD for this environment

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Namespace in Environment Instance contains values where `current_env.solution_structure` was substituted with value `{}`

## TC-003-024: Using `current_env.cluster.name`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory

**Status:** New

**Test Data:**

- Credential Template in Template repository with a Credential that uses `current_env.cluster.name` in `remoteRefPath`
- Environment Inventory at `/environments/test-cluster-01/test-env-01/Inventory/env_definition.yml`

**Pre-requisites:**

- Template Descriptor sets `external_credential_template`
- Credential Template contains the Credential:

  ```yaml
  argocd-cred:
    type: external
    secretStore: default_store
    remoteRefPath: "{{ current_env.cluster.name }}"
    create: false
    properties:
      - name: username
      - name: password
  ```

- Environment Inventory does not set `inventory.cloudName` and `inventory.cloudPassport`
- Instance repository contains no Cloud Passport for the cluster `test-cluster-01`
- Instance repository does not override `argocd-cred`

**Steps:**

- `ENV_NAMES`: `test-cluster-01/test-env-01`
- `ENV_BUILDER`: `true`
- `GENERATE_EFFECTIVE_SET`: `true`

**Expected Results:**

- Environment Credentials File in Environment Instance contains `argocd-cred` with `remoteRefPath: test-cluster-01`
- Effective Set contains the VALS reference `ref+vault://<mountPath>/test-cluster-01/argocd-cred` for `argocd-cred`,
  where `<mountPath>` is the `mountPath` of `default_store`
- `current_env.cloud` is rendered as `test_cluster_01_test_env_01`, the same as without the new macro

## TC-003-025: Using `current_env.cluster.name`. `inventory.cloudName` and `inventory.cloudPassport` set in Environment Inventory

**Status:** New

**Test Data:**

- Credential Template from [TC-003-024](#tc-003-024-using-current_envclustername-inventorycloudname-and-inventorycloudpassport-not-set-in-environment-inventory)
- Environment Inventory at `/environments/test-cluster-01/test-env-01/Inventory/env_definition.yml`
- Cloud Passport referenced by `inventory.cloudPassport`

**Pre-requisites:**

- Environment Inventory sets `inventory.cloudName` and `inventory.cloudPassport`
- Cloud Passport referenced by `inventory.cloudPassport` exists in Instance repository. Its credentials file does not
  contain `argocd-cred`

**Steps:**

- `ENV_NAMES`: `test-cluster-01/test-env-01`
- `ENV_BUILDER`: `true`

**Expected Results:**

- Environment Credentials File in Environment Instance contains `argocd-cred` with `remoteRefPath: test-cluster-01`
- `current_env.cluster.name` is not affected by `inventory.cloudName` and `inventory.cloudPassport`
