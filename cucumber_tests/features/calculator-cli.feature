Feature: Calculator CLI - calculator-cli.md
  As an EnvGene operator
  I want the Calculator CLI to correctly match deployPostfix values and resolve parameter references
  So that the Effective Set v2.0 is generated with accurate namespace associations and type-safe parameters

  Background:
    Given the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"

  # ── deployPostfix Matching Logic ──────────────────────────────────────────────

  Scenario: UC-CC-DP-1: Exact Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the pipeline log contains "Effective set"

  Scenario: UC-CC-DP-2: BG Domain Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_2"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the pipeline log contains "Effective set"

  Scenario: UC-CC-DP-3: No Exact Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Cannot find Namespace folder in Environment Instance for deployPostfix"

  Scenario: UC-CC-DP-4: No BG Domain Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Cannot find Namespace folder in Environment Instance for deployPostfix"

  # ── Parameter Type Preservation in Macro Resolution ───────────────────────────

  @xfail
  Scenario: UC-CC-MR-1: Simple Type Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-cc-mr-1"

  @xfail
  Scenario: UC-CC-MR-2: Complex Structure Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_2"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-cc-mr-2"

  # ── Cross-Level Parameter References ──────────────────────────────────────────

  @xfail
  Scenario: UC-CC-HR-1: Namespace to Cloud Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-cc-hr-1"

  @xfail
  Scenario: UC-CC-HR-2: Namespace to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_2"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-cc-hr-2"

  @xfail
  Scenario: UC-CC-HR-3: Cloud to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_3"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set is generated successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-cc-hr-3"

  @xfail
  Scenario: UC-CC-HR-4: Cloud to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Cloud level parameters cannot reference Namespace level parameters"

  @xfail
  Scenario: UC-CC-HR-5: Tenant to Cloud Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Tenant level parameters cannot reference Cloud level parameters"

  @xfail
  Scenario: UC-CC-HR-6: Tenant to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Tenant level parameters cannot reference Namespace level parameters"

  # ── Cross-Context Parameter References ────────────────────────────────────────

  @xfail
  Scenario: UC-CC-CR-1: DeployParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_1"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'deployParameters' cannot reference parameters from 'e2eParameters'"

  @xfail
  Scenario: UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_2"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'deployParameters' cannot reference parameters from 'technicalConfigurationParameters'"

  @xfail
  Scenario: UC-CC-CR-3: E2EParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'e2eParameters' cannot reference parameters from 'deployParameters'"

  @xfail
  Scenario: UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'e2eParameters' cannot reference parameters from 'technicalConfigurationParameters'"

  @xfail
  Scenario: UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'technicalConfigurationParameters' cannot reference parameters from 'deployParameters'"

  @xfail
  Scenario: UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Parameters in 'technicalConfigurationParameters' cannot reference parameters from 'e2eParameters'"
