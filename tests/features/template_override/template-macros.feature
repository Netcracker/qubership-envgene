Feature: Template Macros Test Cases - template-macros.md
  As an EnvGene developer
  I want to ensure template macros are correctly substituted
  So that environment instances contain correct variables

  Scenario: TC-003-001: Using templates_dir
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env01"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-002: Using current_env.name
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-003: Using current_env.tenant
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-004: Using current_env.cloud. inventory.cloudName set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-006: Using current_env.cloudNameWithCluster. inventory.cloudName set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-007: Using current_env.cloudNameWithCluster. inventory.cloudPassport set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-009: Using current_env.cmdb_name. inventory.deployer set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-011: Using current_env.cmdb_url. inventory.deployer set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-013: Using current_env.description. inventory.description set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-015: Using current_env.owners. inventory.owners set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-017: Using current_env.env_template
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-018: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-020: Using current_env.cloud_passport. inventory.cloudPassport set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-022: Using current_env.solution_structure. SD exist in Instance repository
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-005: Using current_env.cloud. inventory.cloudName NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-008: Using current_env.cloudNameWithCluster. inventory.cloudName and inventory.cloudPassport NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-010: Using current_env.cmdb_name. inventory.deployer NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails

  Scenario: TC-003-012: Using current_env.cmdb_url. inventory.deployer NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails

  Scenario: TC-003-014: Using current_env.description. inventory.description NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-016: Using current_env.owners. inventory.owners NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-019: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-021: Using current_env.cloud_passport. inventory.cloudPassport NOT set in Environment Inventory
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-003-023: Using current_env.solution_structure. SD NOT in Instance repository
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
