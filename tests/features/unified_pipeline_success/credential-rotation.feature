Feature: Unified Pipeline Successful Execution - credential-rotation.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-CR-TPR-1: Update Credential from Pipeline Parameter
    Given the workspace is initialized with test data from "cucumber/uc_cr_tpr_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-TPR-2: Update Credential from Deployment Parameter
    Given the workspace is initialized with test data from "cucumber/uc_cr_tpr_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-TPR-3: Update Credentials from Multiple rotation_items
    Given the workspace is initialized with test data from "cucumber/uc_cr_tpr_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}, {\"namespace\": \"test-env-namespace\", \"application\": \"test_app_2\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-LCH-1: Reject Affected Credential Update
    Given the workspace is initialized with test data from "cucumber/uc_cr_lch_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-LCH-2: Update Affected Credentials in Force Mode
    Given the workspace is initialized with test data from "cucumber/uc_cr_lch_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-VAL-1: Fail When No Affected Parameters Found
    Given the workspace is initialized with test data from "cucumber/uc_cr_val_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled
    Given the workspace is initialized with test data from "cucumber/uc_cr_enc_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled
    Given the workspace is initialized with test data from "cucumber/uc_cr_enc_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWVudi1uYW1lc3BhY2UiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0="
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-3: Update Credentials with Plaintext Payload when Encryption Is Disabled
    Given the workspace is initialized with test data from "cucumber/uc_cr_enc_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-CR-ENC-4: Update Credentials with Encrypted Payload when Encryption Is Disabled
    Given the workspace is initialized with test data from "cucumber/uc_cr_enc_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWVudi1uYW1lc3BhY2UiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0="
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
