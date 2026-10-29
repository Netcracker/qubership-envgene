Feature: Cred store - cred-store.md
  As an EnvGene operator
  I want the pipeline to keep credentials in memory and write only changed cred files, encrypted
  So that cred files never land decrypted on disk and Git shows only real credential changes

  Scenario: UC-CS-ENC-1: A plain cred file is encrypted at the end of a run with crypt true
    Given the workspace is initialized with test data from "e2e/uc_cp_01_auto_association"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cred file "environments/test-cluster/test-env/Credentials/credentials.yml" is SOPS-encrypted
    And in the cred file "environments/test-cluster/test-env/Credentials/credentials.yml" the value of "dummy-cred.data.secret" is encrypted
    And in the cred file "environments/test-cluster/test-env/Credentials/credentials.yml" the value of "dummy-cred.type" is plain
    And the decrypted cred file "environments/test-cluster/test-env/Credentials/credentials.yml" has "dummy-cred.data.secret" equal to "dummy-secret"

  Scenario: UC-CS-DIFF-1: A run that changes no cred leaves encrypted cred files byte-equal
    Given the workspace is initialized with test data from "e2e/uc_cp_01_auto_association"
    And the cred files of the environment are SOPS-encrypted with the test key
    And the cred files are recorded as a baseline
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And every cred file is byte-equal to the baseline

  Scenario: UC-CS-DIFF-2: Rotating one cred value changes only its ciphertext
    Given the workspace is initialized with test data from "e2e/uc_cr_common_sops"
    And the cred files of the environment are SOPS-encrypted with the test key
    And the cred files are recorded as a baseline
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"TOKEN_PARAM\",\"parameter_value\":\"rotated-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And in the cred file "environments/test-cluster/test-env/Credentials/credentials.yml" only the value of "token-cred.data.secret" has a new ciphertext
    And the decrypted cred file "environments/test-cluster/test-env/Credentials/credentials.yml" has "token-cred.data.secret" equal to "rotated-secret"

  Scenario: UC-CS-FAIL-1: A failed run writes no cred file
    Given the workspace is initialized with test data from "e2e/uc_cp_02_no_match"
    And the cred files are recorded as a baseline
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And every cred file is byte-equal to the baseline

  Scenario: UC-CS-FAIL-2: A cred file that fails the creds schema fails the run and no cred file is written
    Given the workspace is initialized with test data from "e2e/uc_cs_invalid_cred"
    And the cred files are recorded as a baseline
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "Cred file validation failed"
    And every cred file is byte-equal to the baseline

  Scenario: UC-CS-FER-1: A cred file with Fernet tokens fails the run and is left as is
    Given the workspace is initialized with test data from "e2e/uc_cs_fernet_creds"
    And the cred files are recorded as a baseline
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "encrypted with Fernet"
    And every cred file is byte-equal to the baseline

  Scenario: UC-CS-ES-1: Literal values in collision-credentials.yaml are encrypted with SOPS
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_5"
    And the pipeline has GENERATE_EFFECTIVE_SET set to "true"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"web\":\"collision-value\",\"override_key\":\"injected-value\"}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the "test-app" collision-credentials.yaml is SOPS-encrypted
    And in the "test-app" collision-credentials.yaml the value of "web" is encrypted

  Scenario: UC-CS-ES-2: VALS and ESO references in the deployment credentials are not encrypted
    Given the workspace is initialized with test data from "e2e/uc_ec_d_5_mixed_flows"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "ns-vals" for "app-vals:1.0"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "ns-eso" for "app-eso:1.0"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the deployment credentials files are not SOPS-encrypted
    And the deployment credentials for application "app-vals" hold VALS references
    And the deployment credentials for application "app-eso" hold ESO references

  Scenario: UC-CS-ES-3: A second Effective Set run with the same inputs leaves ES cred files byte-equal
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_5"
    And the pipeline has GENERATE_EFFECTIVE_SET set to "true"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"web\":\"collision-value\"}}"
    When the unified pipeline orchestrator runs
    And the cred files are recorded as a baseline
    And the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the "test-app" collision-credentials.yaml is byte-equal to the baseline

  Scenario: UC-CS-ES-4: A new literal key in an ES cred file is encrypted
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_5"
    And the pipeline has GENERATE_EFFECTIVE_SET set to "true"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"web\":\"v1\"}}"
    When the unified pipeline orchestrator runs
    And the pipeline parameter "CUSTOM_PARAMS" is changed to "{\"deployment\":{\"web\":\"v1\",\"worker\":\"w1\"}}"
    And the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And in the "test-app" collision-credentials.yaml the value of "web" is encrypted
    And in the "test-app" collision-credentials.yaml the value of "worker" is encrypted
