Feature: Unified Pipeline Successful Execution - blue-green-deployment.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-BG-1: Init Domain
    Given the workspace is initialized with test data from "cucumber/uc_bg_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-3"

  Scenario: UC-BG-2: Warmup
    Given the workspace is initialized with test data from "cucumber/uc_bg_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"candidate\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-4"

  Scenario: UC-BG-3: Promote
    Given the workspace is initialized with test data from "cucumber/uc_bg_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"legacy\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-5"

  Scenario: UC-BG-4: Commit
    Given the workspace is initialized with test data from "cucumber/uc_bg_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-6"

  Scenario: UC-BG-5: Rollback
    Given the workspace is initialized with test data from "cucumber/uc_bg_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-6"

  Scenario: UC-BG-7: Reverse Promote
    Given the workspace is initialized with test data from "cucumber/uc_bg_7_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"legacy\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-7"

  Scenario: UC-BG-8: Reverse Commit
    Given the workspace is initialized with test data from "cucumber/uc_bg_8_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-8"

  Scenario: UC-BG-9: Reverse Rollback
    Given the workspace is initialized with test data from "cucumber/uc_bg_9_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-8"
