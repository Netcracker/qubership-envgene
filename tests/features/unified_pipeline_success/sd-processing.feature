Feature: Unified Pipeline Successful Execution - sd-processing.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-SD-1: Single SD_VERSION with `replace` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-2: Single SD_VERSION with `extended-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-9"

  Scenario: UC-SD-2a: Single SD_VERSION with `extended-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_2a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-3: Single SD_VERSION with `basic-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-11"

  Scenario: UC-SD-3a: Single SD_VERSION with `basic-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_3a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-4: Single SD_VERSION with `basic-exclusion-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-12"

  Scenario: UC-SD-4a: Single SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_4a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-5: Multiple SD_VERSION with `basic-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-13"

  Scenario: UC-SD-5a: Multiple SD_VERSION with `basic-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_5a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-14"

  Scenario: UC-SD-6: Multiple SD_VERSION with `basic-exclusion-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_6_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-15"

  Scenario: UC-SD-6a: Multiple SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_6a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-14"

  Scenario: UC-SD-8: Multiple SD_VERSION with `replace` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_8_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0,test_app_2:2.0.0"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-14"

  Scenario: UC-SD-9: Single SD_VERSION with SD_DELTA=true
    Given the workspace is initialized with test data from "cucumber/uc_sd_9_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_DELTA" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-9"

  Scenario: UC-SD-9a: Single SD_VERSION with SD_DELTA=true when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_9a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_DELTA" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-10: Single SD_VERSION with SD_DELTA=false
    Given the workspace is initialized with test data from "cucumber/uc_sd_10_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "test_app:1.0.0"
    And the pipeline parameter "SD_DELTA" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-11: Single SD_DATA with `replace` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_11_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-12: Single SD_DATA with `extended-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_12_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-9"

  Scenario: UC-SD-12a: Single SD_DATA with `extended-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_12a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-13: Single SD_DATA with `basic-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_13_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-11"

  Scenario: UC-SD-13a: Single SD_DATA with `basic-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_13a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-14: Single SD_DATA with `basic-exclusion-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_14_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-12"

  Scenario: UC-SD-14a: Single SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_14a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-15: Multiple SD_DATA with `basic-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_15_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-11"

  Scenario: UC-SD-15a: Multiple SD_DATA with `basic-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_15a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-16: Multiple SD_DATA with `basic-exclusion-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_16_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-12"

  Scenario: UC-SD-16a: Multiple SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_16a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "basic-exclusion-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-17: Multiple SD_DATA with `extended-merge` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_17_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-17a: Multiple SD_DATA with `extended-merge` mode when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_17a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "extended-merge"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-18: Multiple SD_DATA with `replace` mode
    Given the workspace is initialized with test data from "cucumber/uc_sd_18_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_REPO_MERGE_MODE" is set to "replace"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"

  Scenario: UC-SD-19: Single SD_DATA with SD_DELTA=true
    Given the workspace is initialized with test data from "cucumber/uc_sd_19_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_DELTA" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-9"

  Scenario: UC-SD-19a: Single SD_DATA with SD_DELTA=true when Full SD does not exist
    Given the workspace is initialized with test data from "cucumber/uc_sd_19a_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_DELTA" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-10"

  Scenario: UC-SD-20: Single SD_DATA with SD_DELTA=false
    Given the workspace is initialized with test data from "cucumber/uc_sd_20_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "json"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\": [{\"version\": \"test_app:1.0.0\", \"deployPostfix\": \"dp1\"}], \"deployGraph\": [{\"chunkName\": \"wave1\", \"apps\": [\"test_app:dp1\"]}]}"
    And the pipeline parameter "SD_DELTA" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-2"
