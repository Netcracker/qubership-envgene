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
