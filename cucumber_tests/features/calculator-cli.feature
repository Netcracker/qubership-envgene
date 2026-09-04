Feature: Calculator CLI
  As an EnvGene pipeline
  I want to generate Effective Set v2.0 using the Calculator CLI
  So that deployPostfix matching, parameter merging, macro resolution, custom params, and reference rules all work correctly

  Background:
    Given the pipeline has GENERATE_EFFECTIVE_SET set to "true"

  # ── deployPostfix Matching (UC-CC-DP-*) ──────────────────────────────────────

  Scenario: UC-CC-DP-1: Exact deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "NAMESPACE: core"

  @xfail_cli_npe
  Scenario: UC-CC-DP-2: BG Domain deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  @xfail_cli_npe
  Scenario: UC-CC-DP-3: No Exact Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "nonexistent"

  @xfail_cli_npe
  Scenario: UC-CC-DP-4: No BG Domain Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "xyz"

  # ── Parameter Merge Hierarchy (UC-CC-PM-*) ───────────────────────────────────

  Scenario: UC-CC-PM-1: Namespace Parameter Overrides Cloud Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-namespace"

  Scenario: UC-CC-PM-2: Cloud Parameter Overrides Tenant Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-cloud"

  Scenario: UC-CC-PM-3: Namespace Parameter Overrides Tenant Parameter Directly
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-namespace"

  # ── Parameter Type Preservation in Macro Resolution (UC-CC-MR-*) ─────────────

  Scenario: UC-CC-MR-1: Simple Type Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "api_port: 8080"
    And the effective set deployment parameters contain "use_ssl: true"

  Scenario: UC-CC-MR-2: Complex Structure Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "api_config:"
    And the effective set deployment parameters contain "host: db.example.com"

  Scenario: UC-CC-MR-3: Multi-Step Macro Chain Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "final_url: https://api.example.com"

  @xfail_cli_macro_ns_timeout
  Scenario: UC-CC-MR-4: Macro Reference Resolved Across Hierarchy Levels
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_4"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "ns_timeout: 30"

  # ── Custom Parameters Injection (UC-CC-CP-*) ─────────────────────────────────

  Scenario: UC-CC-CP-1: CUSTOM_PARAMS Injected into Deployment Parameters
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_1"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"override_key\":\"injected-value\"}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "override_key: injected-value"

  Scenario: UC-CC-CP-2: CUSTOM_PARAMS with Unknown Namespace Fails
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_2"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"namespaces\":{\"nonexistent-ns\":{\"key\":\"value\"}}}"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "nonexistent-ns"

  Scenario: UC-CC-CP-3: CUSTOM_PARAMS with Mixed Top-Level and Namespace Keys Fails
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_3"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"key\":\"val\"},\"namespaces\":{\"core\":{\"key\":\"val\"}}}"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "namespaces"
    And the pipeline log shows "deployment"

  # ── Generation ID Types (UC-CC-GI-*) ─────────────────────────────────────────

  Scenario: UC-CC-GI-1: UniqForRun Application Gets Unique Generation Directory
    Given the workspace is initialized with test data from "e2e/uc_cc_gi_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set contains a generation id subdirectory for "test-app"

  Scenario: UC-CC-GI-2: UniqForVersion Application Gets Version-Derived Generation Directory
    Given the workspace is initialized with test data from "e2e/uc_cc_gi_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters for "test-app" exist under version "1.2.3"

  # ── Cross-Level Parameter References (UC-CC-HR-*) ────────────────────────────

  Scenario: UC-CC-HR-1: Namespace to Cloud Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "service_url: https://api.example.com"

  Scenario: UC-CC-HR-2: Namespace to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "organization: acme-corp"

  Scenario: UC-CC-HR-3: Cloud to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "cloud_label: acme-corp"

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
