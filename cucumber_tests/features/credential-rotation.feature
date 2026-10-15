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
    And the affected-sensitive-parameters.yaml report names "OTHER_PARAM" in context "pipeline" and environment "test-env" as affected for target "SOME_PARAM"

  Scenario: UC-CR-TPR-2: Dry run with deployment-context parameter produces report and non-zero exit
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"deployment\",\"parameter_key\":\"db.password\",\"parameter_value\":\"new-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root
    And the affected-sensitive-parameters.yaml report names "db.other" in context "deployment" and environment "test-env" as affected for target "db.password"

  Scenario: UC-CR-TPR-3: Dry run with multiple rotation_items from different contexts
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"new1\"},{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"deployment\",\"parameter_key\":\"db.password\",\"parameter_value\":\"new2\"},{\"namespace\":\"test-ns\",\"application\":\"test-app\",\"context\":\"runtime\",\"parameter_key\":\"config.secret\",\"parameter_value\":\"new3\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root
    And the affected-sensitive-parameters.yaml report names "OTHER_PARAM" in context "pipeline" and environment "test-env" as affected for target "SOME_PARAM"
    And the affected-sensitive-parameters.yaml report names "db.other" in context "deployment" and environment "test-env" as affected for target "db.password"
    And the affected-sensitive-parameters.yaml report names "config.backup" in context "runtime" and environment "test-env" as affected for target "config.secret"

  Scenario: UC-CR-TPR-4: Rotate a secret credential field in force mode
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"TOKEN_PARAM\",\"parameter_value\":\"rotated-secret\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "token-cred" field "secret" equals "rotated-secret" in the env credentials file

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
    And the shared credential "shared-db-cred" field "password" equals "rotated-shared" in shared credential file "shared-db-cred"

  # NOTE (2026-10-07, per review): the original fixture also had a same-env sibling
  # (OTHER_PARAM) referencing the same cred, so "affected" would be non-empty even
  # if the cross-environment search were completely broken - the oracle (report
  # exists) could not tell the two apart. The same-env sibling has been removed:
  # test-env/test-ns now ONLY defines the target SOME_PARAM, so the lone affected
  # match can only come from the cross-environment lookup in test-env-2/test-ns2.
  Scenario: UC-CR-LCH-4: Report affected parameter located in another environment under the same cluster
    Given the workspace is initialized with test data from "e2e/uc_cr_lch_4"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"ignored\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled"
    And the "affected-sensitive-parameters.yaml" file exists at the workspace root
    And the affected-sensitive-parameters.yaml report names "CROSS_ENV_PARAM" in context "pipeline" and environment "test-env-2" as affected for target "SOME_PARAM"

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

  # NOTE (2026-10-07, per review): this scenario locked a code defect rather than
  # the documented contract. docs/use-cases/credential-rotation.md (PR #1800,
  # already merged) defines the target behavior as "rotate the target and
  # complete with no report" when no OTHER parameter shares its credential. The
  # code (process_entry_in_payload/run_cred_rotation) still raises "No affected
  # parameters found" and aborts without rotating in that case - see
  # xfail_cr_no_affected_rotation in conftest.py. Tagged @xfail_cr_no_affected_rotation
  # (strict) so this flips to an unexpected-pass failure the day the code fix
  # lands, instead of silently staying green on the wrong contract.
  @xfail_cr_no_affected_rotation
  Scenario: UC-CR-VAL-1: Rotate target when no affected parameters exist
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"ISOLATED_PARAM\",\"parameter_value\":\"rotated-isolated\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "isolated-cred" field "password" equals "rotated-isolated" in the env credentials file
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
  #
  # NOTE (2026-10-07, per review): the code branches only on `crypt` (true/false) -
  # see validate_env_vars()/get_crypt() - there is no independent "payload is
  # encrypted" switch, and with crypt:false an actually-encrypted payload would
  # fail JSON parsing rather than being decrypted. The four original ENC-1..4
  # scenarios (plaintext/encrypted payload x enabled/disabled encryption) therefore
  # collapsed to two distinct, reachable code paths: ENC-1 now exercises the
  # crypt:true + SOPS decrypt-then-reencrypt branch (through the mocked `sops`
  # binary - this proves the branch runs, not that real cryptography is correct),
  # ENC-3 keeps exercising the crypt:false branch. Docs (docs/use-cases/
  # credential-rotation.md) describe four flows and need a follow-up correction to
  # match - left for the maintainer, not done here.
  # ────────────────────────────────────────────────────────────────────────────

  Scenario: UC-CR-ENC-1: Update credentials when encryption is enabled (SOPS)
    Given the workspace is initialized with test data from "e2e/uc_cr_common_sops"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENVGENE_AGE_PRIVATE_KEY" is set to "AGE-SECRET-KEY-TEST0000000000000000000000000000000000000000"
    And the pipeline parameter "PUBLIC_AGE_KEYS" is set to "age1test0000000000000000000000000000000000000000000000000000000"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc1-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc1-value" in the env credentials file

  Scenario: UC-CR-ENC-3: Update credentials with plaintext payload when encryption is disabled
    Given the workspace is initialized with test data from "e2e/uc_cr_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "CRED_ROTATION_PAYLOAD" is set to "{\"rotation_items\":[{\"namespace\":\"test-ns\",\"context\":\"pipeline\",\"parameter_key\":\"SOME_PARAM\",\"parameter_value\":\"enc3-value\"}]}"
    And the pipeline parameter "CRED_ROTATION_FORCE" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credential "db-cred" field "password" equals "enc3-value" in the env credentials file
