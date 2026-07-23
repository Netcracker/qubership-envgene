Feature: Blue-Green Deployment State Management - blue-green-deployment.md
  As an EnvGene orchestrator
  I want to transition state files between origin and peer namespaces
  So that blue-green deployment works correctly

  # ── Init Domain ──────────────────────────────────────────────────────────────

  Scenario: UC-BG-1: Init Domain
    Given the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    And the bg_domain.yml is configured with origin namespace "origin-ns" and peer namespace "peer-ns"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-active" and ".peer-idle"

  # ── Warmup ───────────────────────────────────────────────────────────────────

  Scenario: UC-BG-2: Warmup
    Given the workspace is initialized with test data from "e2e/uc_bg_2"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"candidate\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-active" and ".peer-candidate"
    And the namespace "origin-ns" and namespace "peer-ns" have the same content

  # ── Promote ──────────────────────────────────────────────────────────────────

  Scenario: UC-BG-3: Promote
    Given the workspace is initialized with test data from "e2e/uc_bg_3"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"legacy\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-legacy" and ".peer-active"

  # ── Commit ───────────────────────────────────────────────────────────────────

  Scenario: UC-BG-4: Commit
    Given the workspace is initialized with test data from "e2e/uc_bg_4"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-idle" and ".peer-active"

  # ── Rollback ─────────────────────────────────────────────────────────────────

  Scenario: UC-BG-5: Rollback
    Given the workspace is initialized with test data from "e2e/uc_bg_5"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-idle" and ".peer-active"

  # ── Reverse Warmup ────────────────────────────────────────────────────────────

  Scenario: UC-BG-6: Reverse Warmup
    Given the workspace is initialized with test data from "e2e/uc_bg_6"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"candidate\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-candidate" and ".peer-active"
    And the namespace "origin-ns" and namespace "peer-ns" have the same content

  # ── Reverse Promote ───────────────────────────────────────────────────────────

  Scenario: UC-BG-7: Reverse Promote
    Given the workspace is initialized with test data from "e2e/uc_bg_7"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"legacy\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-active" and ".peer-legacy"

  # ── Reverse Commit ────────────────────────────────────────────────────────────

  Scenario: UC-BG-8: Reverse Commit
    Given the workspace is initialized with test data from "e2e/uc_bg_8"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-active" and ".peer-idle"

  # ── Reverse Rollback ──────────────────────────────────────────────────────────

  Scenario: UC-BG-9: Reverse Rollback
    Given the workspace is initialized with test data from "e2e/uc_bg_9"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"origin-ns\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"peer-ns\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2023-10-25T12:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the Blue-Green state files are ".origin-active" and ".peer-idle"
