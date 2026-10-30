Feature: CLEAN sub-flows
  As an EnvGene pipeline orchestrator
  I want to clean deployed namespaces without rendering or recalculating the effective set
  So that downstream tooling can undeploy them while other namespaces stay unchanged

  Background:
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"

  Scenario: CLEAN a whole environment empties its plan and cleans every namespace
    Given the environment has a deployed effective set in its ES repository
    And the ES repository contains an old cleanup context
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "cleanup" has status "SUCCESS"
    And the pipeline step "appregdef_render" has status "SKIPPED"
    And the pipeline step "regdefv2_adapter" has status "SKIPPED"
    And the pipeline step "process_deployment_plan" has status "SKIPPED"
    And the pipeline step "env_build" has status "SKIPPED"
    And the pipeline step "generate_effective_set" has status "SKIPPED"
    And the pipeline step "git_commit" has status "SUCCESS"
    And the namespace "core" is marked as cleaned
    And the namespace "bss-origin" is marked as cleaned
    And the namespace "bss-peer" is marked as cleaned
    And the namespace "controller" is marked as cleaned
    And the deploy plan is empty
    And the ES repository keeps its namespace mappings
    And the effective set folder "cleanup" does not exist
    And the ES repository contains no cleanup context
    And the namespace definitions are unchanged
    And the reduced deploy plan and namespace map are committed

  Scenario: CLEAN selected namespaces preserves all other application content
    Given the environment has a deployed effective set in its ES repository
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core;test-env-bss-peer"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" is marked as cleaned
    And the namespace "bss-peer" is marked as cleaned
    And the namespace "bss-origin" is not marked as cleaned
    And the deploy plan contains 1 entry
    And the deploy plan contains an entry for namespace "test-env-bss-origin"
    And the ES repository keeps its namespace mappings
    And the namespace definitions are unchanged

  Scenario: CLEAN of one Blue-Green side preserves the other side and BG state
    Given the environment has a deployed effective set in its ES repository
    And the BG state files are origin "active" and peer "idle"
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-bss-origin"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "bss-origin" is marked as cleaned
    And the namespace "bss-peer" is not marked as cleaned
    And the namespace "core" is not marked as cleaned
    And the BG state files are origin "active" and peer "idle"
    And the deploy plan contains 2 entries
    And the deploy plan does not contain an entry for namespace "test-env-bss-origin"

  Scenario: CLEAN warns for a namespace missing from the deploy plan
    Given the environment has a deployed effective set in its ES repository
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-controller"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Namespace 'test-env-controller' is absent from deploy-plan.yml"
    And the namespace "controller" is marked as cleaned
    And the namespace "core" is not marked as cleaned
    And the deploy plan contains 3 entries

  Scenario: CLEAN rejects an unknown namespace before changing the plan
    Given the environment has a deployed effective set in its ES repository
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core;does-not-exist"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline step "cleanup" has status "FAILED"
    And the pipeline log contains "Namespace 'does-not-exist' is absent from namespace-map.yml"
    And the deploy plan contains 3 entries
    And the namespace "core" is not marked as cleaned

  Scenario: CLEAN a whole environment without a Blue-Green Domain
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the environment has a deployed effective set in its ES repository
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "cleanup" has status "SUCCESS"
    And the namespace "core" is marked as cleaned
    And the namespace "bss" is marked as cleaned
    And the deploy plan is empty
    And the ES repository keeps its namespace mappings

  Scenario: CLEAN one namespace without a Blue-Green Domain
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the environment has a deployed effective set in its ES repository
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" is marked as cleaned
    And the namespace "bss" is not marked as cleaned
    And the deploy plan contains 1 entry
    And the deploy plan contains an entry for namespace "test-env-bss"

  Scenario: CLEAN preserves SBOM files
    Given the environment has a deployed effective set in its ES repository
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the SBOM directory "app1" contains 2 files
    And no SBOM files were removed

  Scenario: Repeating CLEAN warns without changing the cleaned effective set
    Given the environment has a deployed effective set in its ES repository
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Namespace 'test-env-core' is already cleaned"
    And the namespace "core" is marked as cleaned
    And the namespace "bss-origin" is not marked as cleaned
