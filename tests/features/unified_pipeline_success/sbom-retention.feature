Feature: Unified Pipeline Successful Execution - sbom-retention.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-SBOM-1: SBOM retention disabled - no cleanup
    Given the workspace is initialized with test data from "cucumber/uc_sbom_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-SBOM-2: All applications within per-application limit - no files deleted
    Given the workspace is initialized with test data from "cucumber/uc_sbom_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-SBOM-3: Per-application retention keeps 10 most recent versions
    Given the workspace is initialized with test data from "cucumber/uc_sbom_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-SBOM-4: Per-application retention with custom version count
    Given the workspace is initialized with test data from "cucumber/uc_sbom_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-SBOM-5: Total /sboms/ size exceeds 1200 MB - keeps newest per application
    Given the workspace is initialized with test data from "cucumber/uc_sbom_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
