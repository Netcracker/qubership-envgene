Feature: Environment Instance Generation Negative and Parameter Override Tests
  As an EnvGene developer
  I want to ensure pipeline failures on invalid input and pipeline success on valid parameter overrides
  So that the pipeline is robust

  Scenario: TC-EIG-NEG-001: Build Instance with Wrong Cluster
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "invalid-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Exception"

  @xfail
  Scenario: TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENVGENE_PROJECT" is set to "wrong-project"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails

  Scenario: TC-EIG-NEG-003: Build Instance with Wrong Environment
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/invalid-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Exception"

  Scenario: TC-EIG-NEG-004: Build Instance with Wrong Template
    Given the workspace is initialized with test data from "e2e/env-wrong-template"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/env-wrong-template"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails

  Scenario: TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_TEMPLATE_VERSION" is set to "v2.0"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin)
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_TEMPLATE_VERSION_ORIGIN" is set to "v2.1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer)
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_TEMPLATE_VERSION_PEER" is set to "v2.2"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "ENV_SPECIFIC_PARAMS" is set to "{\"foo\": \"bar\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job)
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "APP_REG_DEFS_JOB" is set to "https://ci.example.com/job/123"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "APP_DEFS_PATH" is set to "/custom/path/apps"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "REG_DEFS_PATH" is set to "/custom/path/regs"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "NS_BUILD_FILTER" is set to "core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "DEPLOYMENT_SESSION_ID" is set to "ds-12345"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotate\": true}"
    And the config parameter "sops" is set to true
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "GH_ADDITIONAL_PARAMS" is set to "--debug"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "BG_MANAGE" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "origin"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  Scenario: TC-EIG-PARAM-015: Build Instance with BG_STATE provided
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "origin"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
