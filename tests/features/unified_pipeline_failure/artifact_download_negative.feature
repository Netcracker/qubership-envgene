Feature: Unified Pipeline Failure - Artifact Download
  As an EnvGene developer
  I want to ensure the pipeline handles artifact download failures properly
  So that users get clear error messages

  Scenario: UC-AD-ERR-1: Handle missing application definition
    Given the workspace is initialized with test data from "cucumber/uc_ad_err_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-missing-artdef"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    Then the pipeline log shows "Application Definition not found"

  Scenario: UC-AD-ERR-2: Handle missing registry definition
    Given the workspace is initialized with test data from "cucumber/uc_ad_err_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-missing-regdef"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    Then the pipeline log shows "Registry Definition not found"

  Scenario: UC-AD-ERR-3: Handle authentication failure
    Given the workspace is initialized with test data from "cucumber/uc_ad_err_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-auth-fail"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    Then the pipeline log shows "Authentication failed"

  Scenario: UC-AD-ERR-4: Handle missing artifact definition
    Given the workspace is initialized with test data from "cucumber/uc_ad_err_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-no-art"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    Then the pipeline log shows "Artifact Definition not found"
