Feature: Unified Pipeline Successful Execution - calculator-cli.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-CC-DP-1: Exact Match
    Given the workspace is initialized with test data from "cucumber/uc_cc_dp_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-DP-2: BG Domain Match
    Given the workspace is initialized with test data from "cucumber/uc_cc_dp_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-DP-3: No Exact Match Found
    Given the workspace is initialized with test data from "cucumber/uc_cc_dp_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-DP-4: No BG Domain Match Found
    Given the workspace is initialized with test data from "cucumber/uc_cc_dp_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-MR-1: Simple Type Resolution
    Given the workspace is initialized with test data from "cucumber/uc_cc_mr_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-MR-2: Complex Structure Resolution
    Given the workspace is initialized with test data from "cucumber/uc_cc_mr_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-1: Namespace to Cloud Reference
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-2: Namespace to Tenant Reference
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-3: Cloud to Tenant Reference
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-4: Cloud to Namespace Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-5: Tenant to Cloud Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-HR-6: Tenant to Namespace Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_hr_6_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-1: DeployParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-3: E2EParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "cucumber/uc_cc_cr_6_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
