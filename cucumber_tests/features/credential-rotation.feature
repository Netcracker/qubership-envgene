Feature: Credential Rotation - credential-rotation.md
  As an EnvGene operator
  I want to rotate credentials across all affected parameters
  So that credential changes are applied consistently across the environment instance

  # ────────────────────────────────────────────────────────────────────────────
  # TPR — Parameter Targeting
  # ────────────────────────────────────────────────────────────────────────────

  Scenario: UC-CR-TPR-1: Dry run with pipeline-context parameter produces report and non-zero exit
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"new-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root

  Scenario: UC-CR-TPR-2: Dry run with deployment-context parameter produces report and non-zero exit
    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_2"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"deployment\",\"parameter_key\":\"db.password\",\"parameter_value\":\"new-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root

  Scenario: UC-CR-TPR-3: Dry run with multiple rotation_items from different contexts
    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_3"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"new1\"},{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"deployment\",\"parameter_key\":\"db.password\",\"parameter_value\":\"new2\"},{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"runtime\",\"parameter_key\":\"config.secret\",\"parameter_value\":\"new3\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root

  Scenario: UC-CR-TPR-4: Rotate a secret credential field in force mode
    Given the workspace is initialized with test data from "e2e/uc_cr_tpr_4"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"TOKEN_PARAM\",\"parameter_value\":\"rotated-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "secret" equals "rotated-secret" in the env credentials file

  # ────────────────────────────────────────────────────────────────────────────
  # LCH — Affected Credential Handling
  # ────────────────────────────────────────────────────────────────────────────

  Scenario: UC-CR-LCH-1: Reject affected credential update when FORCE is false
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"new-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root
    And no credential files were modified by the rotation

  Scenario: UC-CR-LCH-3: Update shared credential file linked through Shared Credentials
    Given the workspace is initialized with test data from "e2e/uc_cr_lch_3"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SHARED_PARAM\",\"parameter_value\":\"rotated-shared\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root

  Scenario: UC-CR-LCH-4: Report affected parameter located in another environment under the same cluster
    Given the workspace is initialized with test data from "e2e/uc_cr_lch_4"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"ignored\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root

  Scenario: UC-CR-LCH-2: Update affected credentials in force mode
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"rotated-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "rotated-value" in the env credentials file

  # ────────────────────────────────────────────────────────────────────────────
  # VAL — Validation
  # ────────────────────────────────────────────────────────────────────────────

  Scenario: UC-CR-VAL-1: Fail when no affected parameters found for payload
    Given the workspace is initialized with test data from "e2e/uc_cr_val_1"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"ISOLATED_PARAM\",\"parameter_value\":\"ignored\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "No affected parameters found"
    And the "affected-sensitive-parameters.yaml" file does not exist at the workspace root

  Scenario: UC-CR-VAL-2: Single invalid rotation_item fails the whole job and preserves state
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"v1\"},{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"NON_EXISTENT_PARAM\",\"parameter_value\":\"v2\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And no credential files were modified by the rotation

  Scenario: UC-CR-VAL-3: Reject application specified together with pipeline context
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"v1\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Unsupported context"
    And no credential files were modified by the rotation

  Scenario: UC-CR-VAL-4: Reject GET_PASSPORT combined with CRED_ROTATION_PAYLOAD
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"ignored\"}]}"
    And the pipeline parameter "GET_PASSPORT" is set to "true"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When I run the credential rotation parameter check
    Then the orchestrator fails
    And the pipeline log contains "CRED_ROTATION_PAYLOAD and GET_PASSPORT cannot be used together"

  Scenario: UC-CR-VAL-5: Fail when CRED_ROTATION_PAYLOAD contains invalid namespace
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"nonexistent-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"new-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Target namespace/application file not found in environment instance"

  # ────────────────────────────────────────────────────────────────────────────
  # ENC — Encryption Processing
  # ────────────────────────────────────────────────────────────────────────────

  Scenario: UC-CR-ENC-1: Update credentials with plaintext payload when encryption is enabled
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc1-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc1-value" in the env credentials file

  Scenario: UC-CR-ENC-2: Update credentials with encrypted payload when encryption is enabled
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc2-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc2-value" in the env credentials file

  Scenario: UC-CR-ENC-3: Update credentials with plaintext payload when encryption is disabled
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc3-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc3-value" in the env credentials file

  Scenario: UC-CR-ENC-4: Update credentials with encrypted payload when encryption is disabled
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc4-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc4-value" in the env credentials file
