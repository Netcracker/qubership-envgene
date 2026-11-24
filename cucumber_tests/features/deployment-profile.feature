Feature: The PROFILE parameter of a run as a resource profile
  As an operator who deploys an environment
  I want the PROFILE parameter to set the baseline of the applications the run deploys
  So that a run applies its profile without an edit to the Inventory of the environment

  Background:
    Given the workspace is initialized with test data from "e2e/uc_rp_common"
    And the pipeline parameter "ENV_BUILDER" is set to "true"

  # The PROFILE override is a file of its own, named after the deploy postfix, and the environment definition
  # refers to it through envTemplate.generatedProfileDefaults, which the pipeline writes and the author does not.

  Scenario: UC-DP-ES-1: A run with PROFILE applies its baseline through the Effective Set
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_1"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated resource profile with baseline "prod"
    And the environment definition assigns the generated resource profile to "bss"
    And the namespace "bss" references resource profile "bss-profile-override"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "2"

  Scenario: UC-DP-ES-2: The values of the environment override win over PROFILE
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_2"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment definition keeps resource profile "bss-tuning" for "bss"
    And the environment definition assigns the generated resource profile to "bss"
    And the namespace "bss" references resource profile "bss-tuning"
    And the environment instance has no resource profile "bss-profile-override"
    And the service "svc1" of application "app1" receives "REPLICAS" as "9"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"

  Scenario: UC-DP-ES-3: PROFILE wins over the baseline an application has in the environment override
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_3"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "bss" references resource profile "bss-dev-baseline"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"

  Scenario: UC-DP-NS-1: Only the namespaces the run deploys get the PROFILE override
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_1"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment definition assigns the generated resource profile to "bss"
    And the environment definition has no generated resource profile for "core"
    And the namespace "core" has no resource profile

  # The run below builds the environment without a Solution Descriptor and without a GitLab deploy,
  # so it deploys no application and PROFILE has no effect. The overall result of such a run is not
  # asserted here - only that the step stays out of the way.
  Scenario: UC-DP-SKIP-1: A run that deploys no application skips PROFILE
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_1"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the pipeline step "apply_deployment_profile" has status "SKIPPED"
    And the run leaves no generated resource profile
    And the environment definition has no generated resource profile for "bss"

  Scenario: UC-DP-SKIP-2: A CLEAN run skips PROFILE
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "apply_deployment_profile" has status "SKIPPED"
    And the run leaves no generated resource profile
