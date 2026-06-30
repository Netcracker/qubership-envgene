Feature: Unified Pipeline Failure - envgene-null-value-validation.md
  As an EnvGene developer
  I want to ensure the pipeline fails appropriately on invalid inputs
  So that incorrect configurations do not proceed

  Scenario: UC-NVV-1: Validation failure on missing required key
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CMDB_IMPORT" is set to "true"
    And the pipeline parameter "SIMULATE_MISSING_KEY" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the orchestrator completes with an error

  Scenario: UC-NVV-2: Validation failure on explicitly null value
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CMDB_IMPORT" is set to "true"
    And the pipeline parameter "SIMULATE_NULL_VALUE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the orchestrator completes with an error
