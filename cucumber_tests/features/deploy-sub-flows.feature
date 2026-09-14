Feature: Deploy sub-flows - deploy.md
  As an EnvGene pipeline orchestrator
  I want to run the correct subset of pipeline steps for each deploy architecture
  So that No-CMDB v2 computes the deploy plan from APPLICATION_VERSIONS end to end and
  No-CMDB v1 builds the env instance and effective set from a Solution Descriptor

  # ── No-CMDB v2 - Deploy ──────────────────────────────────────────────────────
  # PIPELINE_TYPE: GITLAB_DEPLOY, OPERATION_TYPE: DEPLOY. Build the env instance, compute the
  # deploy plan from APPLICATION_VERSIONS, generate the effective set, commit. A deploy scoped
  # to a Blue-Green side (BG_NS_TARGET) is covered separately in bgd-sub-flows.feature
  # (Sub-flow 3 / Sub-flow 3 SD path), since that scenario's assertions center on
  # namespace-map.yml resolution rather than the plain deploy step chain.

  Scenario: No-CMDB v2 - deploy computes the deploy plan from APPLICATION_VERSIONS and commits the effective set
    Given the workspace is initialized with test data from "e2e/uc_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "appregdef_render" has status "SUCCESS"
    And the pipeline step "deploy_postfix_namespace_map" has status "SUCCESS"
    And the pipeline step "process_deployment_plan" has status "SUCCESS"
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the pipeline step "git_commit" has status "SUCCESS"
    And the pipeline step "warmup" has status "SKIPPED"
    And the pipeline step "change_bg_state" has status "SKIPPED"
    And the pipeline step "process_sd" has status "SKIPPED"
    And the deploy plan contains an entry for namespace "dummy-namespace" with version "app1:1.0"

  # ── No-CMDB v1 ───────────────────────────────────────────────────────────────
  # PIPELINE_TYPE defaults to LEGACY. ENV_BUILDER + GENERATE_EFFECTIVE_SET select an
  # a-la-carte run: process_sd merges the Solution Descriptor, env_build renders the env
  # instance, generate_effective_set produces the ES, git_commit commits both.

  Scenario: No-CMDB v1 - a legacy SD-driven run builds the env instance and commits the effective set
    Given the workspace is initialized with test data from "e2e/uc_deploy_legacy_sd"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "appregdef_render" has status "SUCCESS"
    And the pipeline step "process_sd" has status "SUCCESS"
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the pipeline step "git_commit" has status "SUCCESS"
    # Per code, not the doc's flow list: DeployPostfixNamespaceMapStep itself requires
    # GITLAB_DEPLOY, so it does not run for LEGACY - the namespace map that process_sd needs is
    # instead seeded by MigrateSdToDeployPlanStep.execute() via compute_namespace_map() when
    # ENV_BUILDER is set. Pinned here so a change either way is caught.
    And the pipeline step "deploy_postfix_namespace_map" has status "SKIPPED"
    And the pipeline step "process_deployment_plan" has status "SKIPPED"
    And the pipeline step "warmup" has status "SKIPPED"
    And the pipeline step "change_bg_state" has status "SKIPPED"
