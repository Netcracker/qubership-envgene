Feature: Effective Set Generation - Deployment Context
  As an EnvGene developer
  I want to ensure the unified pipeline generates correct deployment context parameters
  So that generated environment instances have valid deployment configurations

  Scenario: UC-ES-DEP-14: deploy_param image keys
    Given the workspace is initialized with test data from "e2e/uc-es-dep-14"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-14"

  Scenario: UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline
    Given the workspace is initialized with test data from "e2e/uc-es-dep-15"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "DEPLOYMENT_SESSION_ID" is set to "test-session-abc123"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-15"

  Scenario: UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys
    Given the workspace is initialized with test data from "e2e/uc-es-dep-16"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "MANAGED_BY" is set to "test-manager"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-16"

  Scenario: UC-ES-DEP-20: Service-name collision routing
    Given the workspace is initialized with test data from "e2e/uc-es-dep-20"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-20"

  Scenario: UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs
    Given the workspace is initialized with test data from "e2e/uc-es-dep-22"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-22"

  Scenario: UC-ES-DEP-23: Public and private gateway URLs from deployment context
    Given the workspace is initialized with test data from "e2e/uc-es-dep-23"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-23"

  Scenario: UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a6"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a6"

  Scenario: UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a8"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"customKey\":{\"value\":\"customValue\"},\"region\":{\"value\":\"us-east-1\"}}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a8"

  Scenario: UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a9"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a9"

  Scenario: UC-ES-DEP-A11: Per-service layout and resource profiles
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a11"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a11"

  Scenario: UC-ES-DEP-A14: deployment mapping.yaml
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a14"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a14"

  Scenario: UC-ES-DEP-A15: Blue-green predefined deployment parameters
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a15"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "BG_STATE" is set to "{\"controllerNamespace\":\"controller-ns\",\"originNamespace\":{\"name\":\"bss-origin\",\"state\":\"active\",\"version\":\"1.0.0\"},\"peerNamespace\":{\"name\":\"bss-peer\",\"state\":\"idle\",\"version\":\"1.0.0\"},\"updateTime\":\"2024-01-01T00:00:00Z\"}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a15"

  Scenario: UC-ES-DEP-A16: App chart validation fails when enabled
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a16"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "EFFECTIVE_SET_CONFIG" is set to "{\"app_chart_validation\": true}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a16"

  Scenario: UC-ES-DEP-A18: App chart validation skipped when disabled
    Given the workspace is initialized with test data from "e2e/uc-es-dep-a18"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "EFFECTIVE_SET_CONFIG" is set to "{\"app_chart_validation\": false}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc-es-dep-a18"
