Feature: Unified Pipeline Successful Execution - auto-environment-name.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-AEN-END-1: Environment with no explicit environmentName defined
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env01"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-AEN-END-2: Environment with explicit environmentName defined
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env02"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-AEN-END-3: Environment with explicit environmentName different from folder name
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env03"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-AEN-END-5: Template rendering with derived environment name
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env04"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
