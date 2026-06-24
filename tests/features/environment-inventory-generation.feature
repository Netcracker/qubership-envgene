Feature: Environment Inventory Generation
  As an EnvGene orchestrator
  I want to generate or modify Environment Inventory files based on input content
  So that I can automate the setup of the environment configurations

  Background:
    Given the pipeline has ENV_BUILD set to "false"

  Scenario: UC-EINV-ED-1: Create env_definition.yml
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition"
    Then the "env_definition.yml" file is created

  Scenario: UC-EINV-ED-3: Delete env_definition.yml
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for "envDefinition"
    Then the "env_definition.yml" file is deleted

  Scenario: UC-EINV-PS-1: Create paramset file
    Given the target paramset file "app_params" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for paramset "app_params" at "env" scope
    Then the paramset file "app_params.yml" is created at "env" scope

  Scenario: UC-EINV-CR-1: Create credentials file
    Given the target credentials file "db_creds" does not exist at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for credentials "db_creds" at "cluster" scope
    Then the credentials file "db_creds.yml" is created at "cluster" scope

  Scenario: UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying multiple operations where one fails
    Then the pipeline fails
    And no inventory files are created or modified
