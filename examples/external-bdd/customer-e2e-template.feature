Feature: Customer E2E Test Scenarios - general

  Scenario: UC-CUST-E2E-001: Typical Implementation Project Full Execution
    # In a real customer environment, the workspace is initialized by the CI script
    # downloading templates from ENV_TEMPLATES_REPO and instances from ENV_INSTANCES_REPO.
    # For internal testing, we make do with our local test data.
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
