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

  # The merge mode of the environment decides whether the template override of the Namespace survives the run that
  # sets PROFILE. The Namespace below carries a template override with its own custom values and the object baseline
  # "dev", so the two runs below differ only by inventory.config.mergeEnvSpecificResourceProfiles.

  Scenario: UC-DP-RP-1: Replace mode leaves the generated profile as the only override of the Namespace
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_4"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated profile "core-profile-override" with baseline "prod"
    And the environment definition assigns the generated profile "core-profile-override" to "core"
    And the namespace "core" references resource profile "core-profile-override" with baseline "dev"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "2"
    And the service "svc1" of application "app1" does not receive "TEMPLATE_PARAM"

  Scenario: UC-DP-RP-2: Merge mode keeps the template override and changes only the baseline
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_5"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated profile "core-profile-override" with baseline "prod"
    And the environment definition assigns the generated profile "core-profile-override" to "core"
    And the namespace "core" references resource profile "core-tmpl" with baseline "dev"
    And the environment instance has no resource profile "core-profile-override"
    And the service "svc1" of application "app1" receives "TEMPLATE_PARAM" as "from-template"
    And the service "svc1" of application "app1" receives "REPLICAS" as "3"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"

  Scenario: UC-DP-NB-1: A baseline the deployed application does not have layers nothing under its services
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_5"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "perf-test"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated profile "core-profile-override" with baseline "perf-test"
    And the service "svc1" of application "app1" receives "TEMPLATE_PARAM" as "from-template"
    And the service "svc1" of application "app1" receives "REPLICAS" as "3"
    And the service "svc1" of application "app1" does not receive "BASELINE_MEMORY"

  Scenario: UC-DP-NS-1: Only the namespaces the run deploys get the PROFILE override
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_1"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment definition assigns the generated resource profile to "bss"
    And the environment definition has no generated resource profile for "core"
    And the namespace "core" has no resource profile

  # A Blue-Green environment renders both sides of the pair, while one run deploys one of them. The generated override
  # is named after the deployPostfix both sides share, and every run records the folder it deployed as its own key.

  Scenario: UC-DP-BG-1: Only the Blue-Green side the run deploys gets a key of its own
    Given the workspace is initialized with test data from "e2e/uc_bgd_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "BG_NS_TARGET" is set to "ORIGIN"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated resource profile with baseline "prod"
    And the environment definition assigns the generated resource profile to "bss-origin"
    And the environment definition has no generated resource profile for "bss-peer"

  Scenario: UC-DP-BG-2: The run of the other side adds its key and rewrites the shared override
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_bg"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "BG_NS_TARGET" is set to "PEER"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the pipeline parameter "PROFILE" is set to "prod2"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run writes the generated resource profile with baseline "prod2"
    And the environment definition assigns the generated resource profile to "bss-peer"
    And the environment definition assigns the generated resource profile to "bss-origin"

  # The run below builds the environment without a Solution Descriptor and without a GitLab deploy,
  # so it deploys no application and PROFILE has no effect. The overall result of such a run is not
  # asserted here - only that PROFILE stays out of the way.
  Scenario: UC-DP-SKIP-1: A run that deploys no application skips PROFILE
    Given the workspace is initialized with test data from "e2e/uc_rp_dp_1"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the run leaves no generated resource profile
    And the environment definition has no generated resource profile for "bss"

  Scenario: UC-DP-SKIP-2: A CLEAN run skips PROFILE
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"
    And the pipeline parameter "PROFILE" is set to "prod"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the run leaves no generated resource profile
