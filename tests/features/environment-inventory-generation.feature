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

  Scenario: UC-EINV-ED-2: Update env_definition.yml
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "update" for "envDefinition"
    Then the "env_definition.yml" file is updated

  Scenario: UC-EINV-PS-2: Update paramset file
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "update" for paramset "app_params" at "env" scope
    Then the paramset file "app_params.yml" is updated at "env" scope

  Scenario: UC-EINV-PS-3: Delete paramset file
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for paramset "app_params" at "env" scope
    Then the paramset file "app_params.yml" is deleted at "env" scope

  Scenario: UC-EINV-CR-2: Update credentials file
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "update" for credentials "db_creds" at "cluster" scope
    Then the credentials file "db_creds.yml" is updated at "cluster" scope

  Scenario: UC-EINV-CR-3: Delete credentials file
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for credentials "db_creds" at "cluster" scope
    Then the credentials file "db_creds.yml" is deleted at "cluster" scope

  Scenario: UC-EINV-RP-1: Create resource profile file
    Given the target resource profile file "db_profile" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for resource_profile "db_profile" at "env" scope
    Then the resource profile file "db_profile.yml" is created at "env" scope

  Scenario: UC-EINV-RP-2: Update resource profile file
    Given the target resource profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "update" for resource_profile "db_profile" at "env" scope
    Then the resource profile file "db_profile.yml" is updated at "env" scope

  Scenario: UC-EINV-RP-3: Delete resource profile file
    Given the target resource profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for resource_profile "db_profile" at "env" scope
    Then the resource profile file "db_profile.yml" is deleted at "env" scope

  Scenario: UC-EINV-STV-1: Create specific template version file
    Given the target specific template version file "db_stv" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for specific_template_version "db_stv" at "env" scope
    Then the specific template version file "db_stv.yml" is created at "env" scope

  Scenario: UC-EINV-STV-2: Update specific template version file
    Given the target specific template version file "db_stv" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "update" for specific_template_version "db_stv" at "env" scope
    Then the specific template version file "db_stv.yml" is updated at "env" scope

  Scenario: UC-EINV-STV-3: Delete specific template version file
    Given the target specific template version file "db_stv" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for specific_template_version "db_stv" at "env" scope
    Then the specific template version file "db_stv.yml" is deleted at "env" scope

  Scenario: UC-EINV-TV-1: Create template variable file
    Given the target template variable file "db_tv" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for template_variable "db_tv" at "env" scope
    Then the template variable file "db_tv.yml" is created at "env" scope
