Feature: Unified Pipeline Successful Execution - envgene-null-value-validation.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-NVV-3: All values resolved
    Given the workspace is initialized with test data from "cucumber/uc_nvv_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CMDB_IMPORT" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
