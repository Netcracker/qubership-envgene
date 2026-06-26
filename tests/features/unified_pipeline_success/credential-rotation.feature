Feature: Unified Pipeline Successful Execution - credential-rotation.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-CR-TPR-1: Update Credential from Pipeline Parameter
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-TPR-2: Update Credential from Deployment Parameter
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-TPR-3: Update Credentials from Multiple rotation_items
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string-with-multiple-rotation-items>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-LCH-1: Reject Affected Credential Update
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-LCH-2: Update Affected Credentials in Force Mode
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-VAL-1: Fail When No Affected Parameters Found
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<plaintext-json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<encrypted-json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-3: Update Credentials with Plaintext Payload when Encryption Is Disabled
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<plaintext-json-in-string>"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-4: Update Credentials with Encrypted Payload when Encryption Is Disabled
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "<encrypted-json-in-string>"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
