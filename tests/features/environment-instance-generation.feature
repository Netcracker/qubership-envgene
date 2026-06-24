Feature: Environment Instance Generation
  As an EnvGene orchestrator
  I want to generate Environment Instance objects from Environment Templates
  So that I can build the deployment structure for the environment

  Background:
    Given an Environment Inventory exists for "test-cluster/test-env"
    And the pipeline has ENV_BUILD set to "true"

  Scenario: UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix
    Given a template descriptor specifies namespace "core.yml.j2" with deploy_postfix "core"
    When the Instance pipeline is started
    Then the namespace folder "core" is created in the environment instance

  Scenario: UC-EIG-NF-5: Origin Namespace in BG Domain with deploy_postfix
    Given a template descriptor specifies namespace "bss.yml.j2" with deploy_postfix "bss"
    And the namespace is part of a BG Domain with role "origin"
    When the Instance pipeline is started
    Then the namespace folder "bss-origin" is created in the environment instance

  Scenario: UC-EIG-TA-1: Environment Instance Generation with artifact only
    Given the environment inventory specifies "envTemplate.artifact" as "project-env-template:v1.2.3"
    When the Instance pipeline is started
    Then all namespaces are rendered using "project-env-template:v1.2.3"

  Scenario: UC-EIG-ES-2: Generate Effective Set with SD_DATA or SD_VERSION
    Given the pipeline has GENERATE_EFFECTIVE_SET set to "true"
    And SD_DATA is provided in the pipeline parameters
    When the Instance pipeline is started
    Then the effective set is generated successfully
    And the effective set includes data from SD_DATA

  Scenario: UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments
    Given multiple environment inventories exist for "test-cluster/env1" and "test-cluster/env2"
    And the pipeline has ENV_NAMES set to "test-cluster/env1,test-cluster/env2"
    When the Instance pipeline is started
    Then the environment instance for "test-cluster/env1" is generated successfully
    And the environment instance for "test-cluster/env2" is generated successfully
