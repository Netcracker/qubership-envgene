Feature: External Credentials Management
  As an EnvGene pipeline
  I want to manage credentials stored in external secret stores
  So that sensitive data never lives encrypted in the repository

  # ── Environment Instance Generation ─────────────────────────────────────────

  Scenario: UC-EC-EI-1: Credential template with explicit remoteRefPath is rendered and written
    Given the workspace is initialized with test data from "e2e/uc_ec_ei_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the rendered env credentials match the reference "ref-uc-ec-ei-1"

  Scenario: UC-EC-EI-2: Credential template without remoteRefPath receives the default cloud/env path
    Given the workspace is initialized with test data from "e2e/uc_ec_ei_2"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the rendered env credentials match the reference "ref-uc-ec-ei-2"

  # ── Validation ───────────────────────────────────────────────────────────────

  Scenario: UC-EC-VAL-1: Mixed local and external credential types in the same environment fails
    Given the workspace is initialized with test data from "e2e/uc_ec_val_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Only external credentials allowed"

  Scenario: UC-EC-VAL-2: A credRef inside technicalConfigurationParameters fails
    Given the workspace is initialized with test data from "e2e/uc_ec_val_2"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "External credentials are not supported in 'technicalConfigurationParameters'"

  Scenario: UC-EC-VAL-3: A credRef pointing to an absent credential ID fails
    Given the workspace is initialized with test data from "e2e/uc_ec_val_3"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "not found in any external credential source"

  Scenario: UC-EC-VAL-4: An orphan external credential produces a warning but does not fail
    Given the workspace is initialized with test data from "e2e/uc_ec_ei_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "exist in external credential source but are not referred in environment"
