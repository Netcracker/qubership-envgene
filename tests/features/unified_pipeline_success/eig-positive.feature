Feature: Environment Instance Generation - Positive Scenarios
  As an EnvGene developer
  I want to ensure the unified pipeline builds environment instances successfully
  So that environment generation works for the most common real-world cases

  # NOTE: All scenarios below use ENV_BUILD=true which triggers beautifyYaml → sortYaml
  # → jschon_tools.process_json_doc. The installed jschon_tools version does not expose
  # process_json_doc (known environment issue). Tests are marked @xfail and will pass
  # once jschon_tools is updated.

  @xfail
  Scenario: TC-EIG-POS-001: Build Instance (Basic Build)
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  @xfail
  Scenario: TC-EIG-POS-003: Build Instance with Effective Set and Single SD Data
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  @xfail
  Scenario: TC-EIG-POS-006: Build Instance with Inventory Init and Multiple SD Versions
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  @xfail
  Scenario: TC-EIG-POS-007: Build Instance with Inventory Init and Single SD Data
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully

  @xfail
  Scenario: TC-EIG-POS-008: Build Instance with SD Delta and SD Merge
    Given the workspace is initialized with test data from "e2e/with-sd"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_DELTA" is set to "true"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
