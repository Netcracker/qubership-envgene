Feature: AppDef and RegDef Template Rendering - app_reg_defs_template_rendering.md
  As an EnvGene user
  I want AppDefs and RegDefs to be correctly rendered from templates
  So that environments have the correct definitions according to placement modes and configuration

  Scenario: UC-ARD-TR-1: Basic AppDef/RegDef template rendering
    Given the workspace is initialized with test data from "e2e/uc_ard_tr_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-tr-1"

  Scenario: UC-ARD-TR-2: Basic AppDef/RegDef template delete
    Given the workspace is initialized with test data from "e2e/uc_ard_tr_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-tr-2"

  Scenario: UC-ARD-TR-3: Shared template repository, off-site instance rendering
    Given the workspace is initialized with test data from "e2e/uc_ard_tr_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-tr-3"

  Scenario: UC-ARD-TR-4: Shared template repository, on-site instance rendering
    Given the workspace is initialized with test data from "e2e/uc_ard_tr_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-tr-4"

  Scenario: UC-ARD-UD-1: Replace template-rendered definition with user-provided file
    Given the workspace is initialized with test data from "e2e/uc_ard_ud_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-ud-1"

  Scenario: UC-ARD-UD-2: Delete user-provided file
    Given the workspace is initialized with test data from "e2e/uc_ard_ud_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-ud-2"

  Scenario: UC-ARD-UD-3: Add new definition via user-provided file with no matching template
    Given the workspace is initialized with test data from "e2e/uc_ard_ud_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-ud-3"

  Scenario: UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout)
    Given the workspace is initialized with test data from "e2e/uc_ard_pm_1_base"
    And the config parameter "app_reg_defs_placement" is set to "root"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-pm-1"

  Scenario: UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup)
    Given the workspace is initialized with test data from "e2e/uc_ard_pm_2_base"
    And the config parameter "app_reg_defs_placement" is set to "dual"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-pm-2"

  Scenario: UC-ARD-CI-1: Export definitions to CMDB
    Given the workspace is initialized with test data from "e2e/uc_ard_ci_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the workspace matches the reference "ref-uc-ard-ci-1"
