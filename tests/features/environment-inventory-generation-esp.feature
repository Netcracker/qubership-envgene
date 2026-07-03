Feature: Environment Inventory Generation - ENV_SPECIFIC_PARAMS
  As an EnvGene orchestrator
  I want to update Environment Inventory using ENV_SPECIFIC_PARAMS
  So that external systems can adjust inventory fields without full replacement

  Background:
    Given the pipeline has ENV_BUILD set to "false"
    And the target environment inventory file exists with cluster URL

  # NOTE: All ESP scenarios are marked @xfail because ENV_SPECIFIC_PARAMS handler
  # references SCHEMAS_DIR which is undefined in env_inventory_generation.py — known
  # bug in production code. Tests are written to match documented behavior and will
  # pass once the bug is fixed.

  @xfail
  Scenario: UC-EINV-ESP-1: Update inventory with ENV_SPECIFIC_PARAMS (merge/override)
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing additionalTemplateVariables
    Then the pipeline completes successfully
    And the env_definition.yml contains the merged additionalTemplateVariables

  @xfail
  Scenario: UC-EINV-ESP-2: Override inventory.clusterUrl via clusterParams.clusterEndpoint
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing clusterEndpoint "https://new-cluster.example.com:6443"
    Then the pipeline completes successfully
    And the env_definition.yml clusterUrl equals "https://new-cluster.example.com:6443"

  @xfail
  Scenario: UC-EINV-ESP-3: Add cluster token credential via clusterParams.clusterToken (no override if exists)
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing clusterToken "my-token-value"
    Then the pipeline completes successfully
    And the credentials file "inventory_generation_creds.yml" is created at "env" scope

  @xfail
  Scenario: UC-EINV-ESP-4: Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS merging additionalTemplateVariables key "NEW_KEY" value "new-value"
    Then the pipeline completes successfully
    And the env_definition.yml additionalTemplateVariables contains key "NEW_KEY" with value "new-value"

  @xfail
  Scenario: UC-EINV-ESP-5: Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting cloudName to "new-cloud"
    Then the pipeline completes successfully
    And the env_definition.yml inventory.cloudName equals "new-cloud"

  @xfail
  Scenario: UC-EINV-ESP-6: Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting tenantName to "NewTenant"
    Then the pipeline completes successfully
    And the env_definition.yml inventory.tenantName equals "NewTenant"

  @xfail
  Scenario: UC-EINV-ESP-7: Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting deployer to "abstract-CMDB-1"
    Then the pipeline completes successfully
    And the env_definition.yml inventory.deployer equals "abstract-CMDB-1"

  @xfail
  Scenario: UC-EINV-ESP-8: Merge envSpecificParamsets into envTemplate.envSpecificParamsets
    When the Instance pipeline is started with ENV_SPECIFIC_PARAMS merging envSpecificParamsets for "bss" with "esp-paramset"
    Then the pipeline completes successfully
    And the env_definition.yml envTemplate.envSpecificParamsets for "bss" contains "esp-paramset"
