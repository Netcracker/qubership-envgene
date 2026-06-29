Feature: Cloud Passport Association Failures

  Scenario: UC-08: Mixed cluster failure when infra relies on auto-association
    Given the workspace is initialized with test data from "e2e/uc_cp_8_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    # To simulate the failure as described in the use case:
    # "Infra deployment fails because the infra environment inherits business-only parameters via the cluster default passport"
    # Our mocked framework will check for 'business-value-that-fails-infra' inside cloud.yml and fail the process.
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Infra validation failed: business-only parameters found in infra environment"
