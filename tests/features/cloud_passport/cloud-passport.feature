Feature: Cloud Passport Association

  Scenario: UC-01: Environment inherits cluster Cloud Passport automatically
    Given the workspace is initialized with test data from "e2e/uc_cp_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-01"

  Scenario: UC-02: Environment uses explicitly named Cloud Passport
    Given the workspace is initialized with test data from "e2e/uc_cp_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-02"

  Scenario: UC-03: Environment builds without Cloud Passport
    Given the workspace is initialized with test data from "e2e/uc_cp_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-03"

  Scenario: UC-04: Environment uses passport from custom location
    Given the workspace is initialized with test data from "e2e/uc_cp_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-04"

  Scenario: UC-05: Parameter source traceability
    Given the workspace is initialized with test data from "e2e/uc_cp_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-05"

  Scenario: UC-06: Business environments auto-associate the business passport in a mixed cluster
    Given the workspace is initialized with test data from "e2e/uc_cp_6_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-06"

  Scenario: UC-07: Infra environments use an explicit infra passport in a mixed cluster
    Given the workspace is initialized with test data from "e2e/uc_cp_7_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-07"

  Scenario: UC-09: Backward compatibility for existing business environments
    Given the workspace is initialized with test data from "e2e/uc_cp_7_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-09"
