Feature: Environment Inventory Generation
  As an EnvGene orchestrator
  I want to generate or modify Environment Inventory files based on input content
  So that I can automate the setup of the environment configurations

  Background:
    Given the pipeline has ENV_BUILD set to "false"

  # ── env_definition.yml ──────────────────────────────────────────────────────

  Scenario: UC-EINV-ED-1: Create env_definition.yml
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition"
    Then it validates "envDefinition" against the request schema
    And it validates "envDefinition.content" against the "env_definition.yml" schema
    And it resolves target path for "env_definition.yml"
    And the "env_definition.yml" file is created
    And its content matches the payload

  Scenario: UC-EINV-ED-2: Replace env_definition.yml
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition"
    Then it validates "envDefinition" against the request schema
    And it validates "envDefinition.content" against the "env_definition.yml" schema
    And it resolves target path for "env_definition.yml"
    And the "env_definition.yml" file is updated
    And its content matches the payload

  @xfail
  Scenario: UC-EINV-ED-3: Delete env_definition.yml
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for "envDefinition"
    Then the "env_definition.yml" file is deleted
    And the environment directory is deleted

  # ── Paramsets ────────────────────────────────────────────────────────────────

  Scenario: UC-EINV-PS-1: Create paramset file
    Given the target paramset file "app_params" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for paramset "app_params" at "env" scope
    Then it validates "paramSets" against the request schema
    And it validates "paramSets[].content" against the "parameters.yml" schema
    And it resolves target path for "app_params.yml"
    And the paramset file "app_params.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-PS-2: Replace paramset file
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for paramset "app_params" at "env" scope
    Then it validates "paramSets" against the request schema
    And it validates "paramSets[].content" against the "parameters.yml" schema
    And it resolves target path for "app_params.yml"
    And the paramset file "app_params.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-PS-3: Delete paramset file
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for paramset "app_params" at "env" scope
    Then the paramset file "app_params.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Credentials ──────────────────────────────────────────────────────────────

  Scenario: UC-EINV-CR-1: Create credentials file
    Given the target credentials file "db_creds" does not exist at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for credentials "db_creds" at "cluster" scope
    Then it validates "credentials" against the request schema
    And it validates "credentials[].content" against the "credentials.yml" schema
    And it resolves target path for "db_creds.yml"
    And the credentials file "db_creds.yml" is created at "cluster" scope
    And its content matches the payload

  Scenario: UC-EINV-CR-2: Replace credentials file
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for credentials "db_creds" at "cluster" scope
    Then it validates "credentials" against the request schema
    And it validates "credentials[].content" against the "credentials.yml" schema
    And it resolves target path for "db_creds.yml"
    And the credentials file "db_creds.yml" is updated at "cluster" scope
    And its content matches the payload

  Scenario: UC-EINV-CR-3: Delete credentials file
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for credentials "db_creds" at "cluster" scope
    Then the credentials file "db_creds.yml" is deleted at "cluster" scope
    And its parent directory is not deleted

  # ── Resource Profiles ────────────────────────────────────────────────────────

  Scenario: UC-EINV-RP-1: Create resource profile override file
    Given the target resource_profile file "db_profile" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for resource_profile "db_profile" at "env" scope
    Then it validates "resourceProfiles" against the request schema
    And it validates "resourceProfiles[].content" against the "resourceProfiles.yml" schema
    And it resolves target path for "db_profile.yml"
    And the resource_profile file "db_profile.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-RP-2: Replace resource profile override file
    Given the target resource_profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for resource_profile "db_profile" at "env" scope
    Then it validates "resourceProfiles" against the request schema
    And it validates "resourceProfiles[].content" against the "resourceProfiles.yml" schema
    And it resolves target path for "db_profile.yml"
    And the resource_profile file "db_profile.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-RP-3: Delete resource profile override file
    Given the target resource_profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for resource_profile "db_profile" at "env" scope
    Then the resource_profile file "db_profile.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Shared Template Variables ─────────────────────────────────────────────────

  Scenario: UC-EINV-STV-1: Create Shared Template Variable file
    Given the target shared_template_variable file "prod_vars" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for shared_template_variable "prod_vars" at "env" scope
    Then it validates "sharedTemplateVariables" against the request schema
    And it validates "sharedTemplateVariables[].content" against the "shared_template_variables.yml" schema
    And it resolves target path for "prod_vars.yml"
    And the shared_template_variable file "prod_vars.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-STV-2: Replace Shared Template Variable file
    Given the target shared_template_variable file "prod_vars" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for shared_template_variable "prod_vars" at "env" scope
    Then it validates "sharedTemplateVariables" against the request schema
    And it validates "sharedTemplateVariables[].content" against the "shared_template_variables.yml" schema
    And it resolves target path for "prod_vars.yml"
    And the shared_template_variable file "prod_vars.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-STV-3: Delete Shared Template Variable file
    Given the target shared_template_variable file "prod_vars" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for shared_template_variable "prod_vars" at "env" scope
    Then the shared_template_variable file "prod_vars.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Atomic rollback ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails
    Given the repository has an initial state for rollback testing
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying multiple operations where one fails
    Then the pipeline fails
    And the pipeline logs contain a readable error message explaining the failure reason
    And the repository state is identical to the initial state

  # ── Template Version Update ───────────────────────────────────────────────────

  @xfail
  Scenario: UC-EINV-TV-1: Apply ENV_TEMPLATE_VERSION in PERSISTENT mode
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_TEMPLATE_VERSION set to "env-templates:2.0.0" and update mode "PERSISTENT"
    Then the "env_definition.yml" file has envTemplate.artifact equal to "env-templates:2.0.0"
