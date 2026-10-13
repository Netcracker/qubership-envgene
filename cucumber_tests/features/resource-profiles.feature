Feature: Resource profile baseline and override resolution
  As an EnvGene pipeline
  I want environment build and Effective Set generation to resolve resource profiles end to end
  So that the baseline and custom values chosen for an environment reach each service

  Background:
    Given the workspace is initialized with test data from "e2e/uc_rp_common"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the Calculator CLI generates the effective set

  Scenario: UC-RP-ES-1: Standalone environment-specific override with no template override
    Given the workspace is initialized with test data from "e2e/uc_rp_es_1"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "bss" references resource profile "bss-env-over" with baseline "prod"
    And the resource profile "bss-env-over" in the environment instance has baseline "prod"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "5"

  Scenario: UC-RP-ES-2: Merge mode with a different baseline is the warned wrong path
    Given the workspace is initialized with test data from "e2e/uc_rp_es_2"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" references resource profile "core-tmpl" with baseline "prod"
    And the resource profile "core-tmpl" in the environment instance has baseline "prod"
    And the environment instance has no resource profile "core-env-over"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "5"
    And the service "svc1" of application "app1" receives "TEMPLATE_PARAM" as "from-template"

  Scenario: UC-RP-ES-3: Replace mode changes the baseline for the environment
    Given the workspace is initialized with test data from "e2e/uc_rp_es_3"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" references resource profile "core-env-over" with baseline "prod"
    And the resource profile "core-env-over" in the environment instance has baseline "prod"
    And the environment instance has no resource profile "core-tmpl"
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "5"
    And the service "svc1" of application "app1" does not receive "TEMPLATE_PARAM"

  Scenario: UC-RP-SS-3: Cloud is the active side when the namespace has no baseline or override
    Given the workspace is initialized with test data from "e2e/uc_rp_ss_3"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "bss" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud references resource profile "cloud-env-over" with baseline "prod"
    And the namespace "bss" has no resource profile
    And the service "svc1" of application "app1" receives "BASELINE_MEMORY" as "prod-mem"
    And the service "svc1" of application "app1" receives "REPLICAS" as "5"
