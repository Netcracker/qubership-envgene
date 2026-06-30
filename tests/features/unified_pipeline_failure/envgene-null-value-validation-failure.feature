Feature: Unified Pipeline Failure - envgene-null-value-validation.md
  As an EnvGene developer
  I want to ensure the pipeline fails appropriately when envgeneNullValue is found
  So that unresolved placeholder values do not leave the pipeline

  Scenario: UC-NVV-1: Unresolved parameter blocks pipeline
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And a deploy parameter "API_URL" is set to "envgeneNullValue" in the environment instance
    When the unified pipeline orchestrator runs
    Then the orchestrator fails

  Scenario: UC-NVV-2: Unresolved credential blocks pipeline
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And a credential "dbaas-cluster-dba-cred" has "envgeneNullValue" for username in the environment instance
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
