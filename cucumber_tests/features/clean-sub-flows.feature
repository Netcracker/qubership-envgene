Feature: CLEAN sub-flows
  As an EnvGene pipeline orchestrator
  I want to reduce the deploy plan without rendering or recalculating the effective set
  So that the separate cleanup command can clean the existing effective set

  Background:
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"

  Scenario: CLEAN a whole environment empties its plan without changing the effective set
    Given the environment has deployed namespaces
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the pipeline step "cleanup" has status "SUCCESS"
    And the pipeline step "appregdef_render" has status "SKIPPED"
    And the pipeline step "regdefv2_adapter" has status "SKIPPED"
    And the pipeline step "process_deployment_plan" has status "SKIPPED"
    And the pipeline step "env_build" has status "SKIPPED"
    And the pipeline step "generate_effective_set" has status "SKIPPED"
    And the pipeline step "git_commit" has status "SUCCESS"
    And the deploy plan is empty
    And the namespace definitions are unchanged
    And the reduced deploy plan and namespace map are committed

  Scenario Outline: CLEAN selected namespaces reduces only their deployment plan entries
    Given the environment has deployed namespaces
    And the namespaces "test-env-core" and "test-env-bss-peer" are selected with "<separator>"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the deploy plan contains 1 entry
    And the deploy plan contains an entry for namespace "test-env-bss-origin"
    And the namespace definitions are unchanged
    And the reduced deploy plan and namespace map are committed

    Examples:
      | separator       |
      | semicolon       |
      | escaped newline |

  Scenario: CLEAN of one Blue-Green side preserves the other side and BG state
    Given the environment has deployed namespaces
    And the BG state files are origin "active" and peer "idle"
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-bss-origin"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the BG state files are origin "active" and peer "idle"
    And the deploy plan contains 2 entries
    And the deploy plan does not contain an entry for namespace "test-env-bss-origin"
    And the reduced deploy plan and namespace map are committed

  Scenario: CLEAN warns for a namespace missing from the deploy plan
    Given the environment has deployed namespaces
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-controller"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the pipeline log contains "Namespace 'test-env-controller' is absent from deploy-plan.yml"
    And the deploy plan contains 3 entries

  Scenario: CLEAN rejects an unknown namespace before changing the plan
    Given the environment has deployed namespaces
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core;does-not-exist"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline step "cleanup" has status "FAILED"
    And the pipeline log contains "Namespace 'does-not-exist' is absent from namespace-map.yml"
    And the existing effective set is unchanged
    And the deploy plan contains 3 entries

  Scenario: CLEAN a whole environment without a Blue-Green Domain
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the environment has deployed namespaces
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the pipeline step "cleanup" has status "SUCCESS"
    And the deploy plan is empty

  Scenario: CLEAN one namespace without a Blue-Green Domain
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the environment has deployed namespaces
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the deploy plan contains 1 entry
    And the deploy plan contains an entry for namespace "test-env-bss"
    And the reduced deploy plan and namespace map are committed

  Scenario: CLEAN preserves SBOM files
    Given the environment has deployed namespaces
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the SBOM directory "app1" contains 2 files
    And no SBOM files were removed

  Scenario: Repeating CLEAN keeps the reduced deployment plan unchanged
    Given the environment has deployed namespaces
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the existing effective set is unchanged
    And the pipeline log contains "Namespace 'test-env-core' is absent from deploy-plan.yml"
    And the deploy plan contains 2 entries
