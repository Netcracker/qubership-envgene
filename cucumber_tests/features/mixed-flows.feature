Feature: Mixed flows - No-CMDB v2 and No-CMDB v1 runs on the same environment
  As an EnvGene pipeline orchestrator
  I want a No-CMDB v1 run to accept the deploy plan left by a No-CMDB v2 run
  So that an environment operated with both flows keeps generating the effective set

  Scenario: No-CMDB v2 CLEAN of a whole environment followed by a No-CMDB v1 effective set run
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the deploy plan is empty
    When the pipeline parameter "PIPELINE_TYPE" is removed
    And the pipeline parameter "OPERATION_TYPE" is removed
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is changed to "true"
    And the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "process_sd" has status "SKIPPED"
    And the pipeline step "migrate_sd_to_deploy_plan" has status "SKIPPED"
    And the pipeline step "process_deployment_plan" has status "SKIPPED"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the deploy plan is empty
    And the effective set folder "topology" contains file "parameters.yaml"
    And the effective set folder "pipeline" contains file "parameters.yaml"
