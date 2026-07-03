Feature: Template Override Test Cases - template-override.md
  As an EnvGene developer
  I want to ensure template overrides work correctly
  So that Cloud and Namespace templates are overridden according to the documentation

  Scenario: TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments
    Given the workspace is initialized for template testing
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env01"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log shows "Generation completed"
