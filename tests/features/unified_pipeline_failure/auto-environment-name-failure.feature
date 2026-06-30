Feature: Unified Pipeline Failure - auto-environment-name.md
  As an EnvGene developer
  I want to ensure the pipeline fails appropriately on invalid inputs
  So that incorrect configurations do not proceed

  Scenario: UC-AEN-END-4: Invalid folder structure for environment
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "invalid-structure"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the orchestrator completes with an error
