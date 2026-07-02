Feature: Unified Pipeline Successful Execution - credential-rotation.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-CR-TPR-1: Update Credential from Pipeline Parameter

    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_1"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"context\": \"pipeline\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_tpr_1"

  Scenario: UC-CR-TPR-2: Update Credential from Deployment Parameter

    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_2"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_tpr_2"

  Scenario: UC-CR-TPR-3: Update Credentials from Multiple rotation_items

    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_3"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"context\": \"pipeline\", \"parameter_key\": \"pipeline_password\", \"parameter_value\": \"new_password\"}, {\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}, {\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"runtime\", \"parameter_key\": \"runtime_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_tpr_3"

  Scenario: UC-CR-LCH-1: Reject Affected Credential Update

    Given the workspace is initialized with test data from "e2e/uc_cr_lch_1"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_lch_1"

  Scenario: UC-CR-LCH-2: Update Affected Credentials in Force Mode

    Given the workspace is initialized with test data from "e2e/uc_cr_lch_2"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_lch_2"

  Scenario: UC-CR-VAL-1: Fail When No Affected Parameters Found

    Given the workspace is initialized with test data from "e2e/uc_cr_val_1"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_val_1"

  Scenario: UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled

    Given the workspace is initialized with test data from "e2e/uc_cr_enc_1"
    And the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_enc_1"

  Scenario: UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled

    Given the workspace is initialized with test data from "e2e/uc_cr_enc_2"
    And the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWVudi1uYW1lc3BhY2UiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0="
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_enc_2"

  Scenario: UC-CR-ENC-3: Update Credentials with Plaintext Payload when Encryption Is Disabled

    Given the workspace is initialized with test data from "e2e/uc_cr_enc_3"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\": [{\"namespace\": \"test-env-namespace\", \"application\": \"test_app\", \"context\": \"deployment\", \"parameter_key\": \"db_password\", \"parameter_value\": \"new_password\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_enc_3"

  Scenario: UC-CR-ENC-4: Update Credentials with Encrypted Payload when Encryption Is Disabled

    Given the workspace is initialized with test data from "e2e/uc_cr_enc_4"
    And the config parameter "crypt" is set to false
    And the config parameter "crypt_backend" is set to "SOPS"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "dummy"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "dummy"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWVudi1uYW1lc3BhY2UiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0="
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "uc_cr_enc_4"
