Feature: Calculator CLI
  As an EnvGene pipeline
  I want to generate Effective Set v2.0 using the Calculator CLI
  So that deployPostfix matching, macro resolution, and parameter reference rules work correctly

  Background:
    Given the pipeline has GENERATE_EFFECTIVE_SET set to "true"
    And the Calculator CLI mock validates rules

  # ── deployPostfix Matching (UC-CC-DP-*) ──────────────────────────────────────

  Scenario: UC-CC-DP-1: Exact deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  @xfail_cli_npe
  Scenario: UC-CC-DP-2: BG Domain deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  Scenario: UC-CC-DP-3: No Exact Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "nonexistent"

  Scenario: UC-CC-DP-4: No BG Domain Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "xyz"

  # ── Parameter Type Preservation in Macro Resolution (UC-CC-MR-*) ─────────────

  Scenario: UC-CC-MR-1: Simple Type Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  Scenario: UC-CC-MR-2: Complex Structure Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  # ── Cross-Level Parameter References (UC-CC-HR-*) ────────────────────────────

  Scenario: UC-CC-HR-1: Namespace to Cloud Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  Scenario: UC-CC-HR-2: Namespace to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  Scenario: UC-CC-HR-3: Cloud to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  Scenario: UC-CC-HR-4: Cloud to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "namespace_test_url"

  @xfail_cli_no_hierarchy_rule
  Scenario: UC-CC-HR-5: Tenant to Cloud Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "Tenant level parameters cannot reference Cloud level parameters"

  @xfail_cli_no_hierarchy_rule
  Scenario: UC-CC-HR-6: Tenant to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "Tenant level parameters cannot reference Namespace level parameters"

  # ── Cross-Context Parameter References (UC-CC-CR-*) ──────────────────────────

  Scenario: UC-CC-CR-1: DeployParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_1"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "service_url"
    And the pipeline log shows "test_url"

  Scenario: UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_2"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "service_config"
    And the pipeline log shows "config_url"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-3: E2EParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "e2eParameters"
    And the pipeline log shows "deployParameters"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "e2eParameters"
    And the pipeline log shows "technicalConfigurationParameters"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "technicalConfigurationParameters"
    And the pipeline log shows "deployParameters"

  Scenario: UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "runtime_endpoint"
    And the pipeline log shows "e2e_endpoint"
