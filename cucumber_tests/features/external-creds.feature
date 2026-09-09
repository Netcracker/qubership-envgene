Feature: External Credentials Management
  As an EnvGene pipeline
  I want to manage credentials stored in external secret stores
  So that sensitive data never lives encrypted in the repository

#===================================================================================
#Group V — environment-instance validation (stage: env_build)
#Feature: External Credentials - environment-instance validation
#===================================================================================

# why: EC-V-1 external-only happy path — env build writes a homogeneous external credentials file
  Scenario: UC-EC-V-1: External-only environment instance builds and writes external-only credentials
    Given the workspace is initialized with test data from "e2e/uc_ec_v_1_external_only"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the environment credentials file contains only credentials of type "external"

# why: EC-V-1 legacy reachability smoke — the legacy ENV_BUILDER entrypoint reaches the same validation
  Scenario: UC-EC-V-1b: Legacy env build reaches external credential validation
    Given the workspace is initialized with test data from "e2e/uc_ec_v_1_external_only"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the environment credentials file contains only credentials of type "external"

# why: EC-V-2 local-only regression — the external path does not disturb the local path
  Scenario: UC-EC-V-2: Local-only environment instance builds and writes no external credentials
    Given the workspace is initialized with test data from "e2e/uc_ec_v_2_local_only"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the environment credentials file contains no credentials of type "external" 

# why: EC-V-3 unresolved reference — fails naming the missing external credential
  Scenario: UC-EC-V-3: Unresolved external credential reference fails env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_3_missing_source"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log shows "are not found in any external credential source"

# why: EC-V-4 external macro in a local env — mixed-category, env_build rejects it
  Scenario: UC-EC-V-4: External credential reference in a local-only environment fails env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_4_extref_in_local"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log shows "Found external credential references in parameters in local cred only environment"

# why: EC-V-5 local macro in an external env — mixed-category, env_build rejects it
  Scenario: UC-EC-V-5: Local credential macro in an external-only environment fails env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_5_localmacro_in_external"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log shows "Found local credential macros in external cred only environment"

# why: EC-V-6 mixed types in the merged credentials file — validate_cred_types rejects it
  Scenario: UC-EC-V-6: Mixed credential types in the merged credentials file fail env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_6_mixed_types"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log shows "Only external credentials allowed. Found:"

# why: EC-V-7 credRef in technicalConfigurationParameters — runtime context forbids external creds
  Scenario: UC-EC-V-7: External credRef in technicalConfigurationParameters fails env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_7_credref_in_runtime"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log shows "technicalConfigurationParameters"

# why: EC-V-8 orphan external Credential — warning only, build still succeeds
  Scenario: UC-EC-V-8: Unreferenced external credential warns but does not fail env build
    Given the workspace is initialized with test data from "e2e/uc_ec_v_8_orphan_external"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log shows "exist in external credential source but are not referred"

#===================================================================================
#Group D — deployment effective-set reference shape (stage: generate_effective_set)
#Feature: External Credentials - deployment effective-set references
#===================================================================================

# why: EC-D-1 VALS multi-field vault — each leaf is a ref+vault://…#/<property> string
  Scenario: UC-EC-D-1: helm-values multi-field credential emits VALS references with property fragments
    Given the workspace is initialized with test data from "e2e/uc_ec_d_1_vals_multi"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "DB_ADMIN_USER: ref+vault://secret/test-cluster/test-env/db/app-db-cred#/username"
    And the effective set deployment parameters contain "DB_ADMIN_PASSWORD: ref+vault://secret/test-cluster/test-env/db/app-db-cred#/password"

# why: EC-D-1 legacy reachability smoke — legacy ES entrypoint reaches the deployment credentials file
  Scenario: UC-EC-D-1b: Legacy effective-set run emits VALS references
    Given the workspace is initialized with test data from "e2e/uc_ec_d_1_vals_multi"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_DATA" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "DB_ADMIN_USER: ref+vault://secret/test-cluster/test-env/db/app-db-cred#/username"

# why: EC-D-2 VALS single-value vault — the fragment is #/value (sibling of EC-D-1: no properties)
  Scenario: UC-EC-D-2: helm-values single-value vault credential emits a VALS reference with #/value
    Given the workspace is initialized with test data from "e2e/uc_ec_d_1_vals_multi"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "CONSUL_ADMIN_TOKEN: ref+vault://secret/test-cluster/consul-admin-cred#/value"

# why: EC-D-6 VALS single-value non-vault — plain text, no #/ fragment, secret_store_id query present
  Scenario: UC-EC-D-6: helm-values single-value non-default-store credential omits the fragment
    Given the workspace is initialized with test data from "e2e/uc_ec_d_6_vals_gcp_named_store"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the deployment credentials value for "CONSUL_ADMIN_TOKEN" contains "secret_store_id=gcp_store"
    And the deployment credentials value for "CONSUL_ADMIN_TOKEN" does not contain "#/"

# why: EC-D-3 ESO multi-field — object with secretKeys per property
  Scenario: UC-EC-D-3: external-values multi-field credential emits an ESO reference object with secretKeys
    Given the workspace is initialized with test data from "e2e/uc_ec_d_3_eso_multi"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the deployment credentials value for "DB_ADMIN_USER" is an ESO reference to "test-cluster/test-env/db/app-db-cred" with key "username"
    And the deployment credentials value for "DB_ADMIN_PASSWORD" is an ESO reference to "test-cluster/test-env/db/app-db-cred" with key "password"

 # why: EC-D-4 ESO single-value — object with no secretKeys (sibling of EC-D-3)
  Scenario: UC-EC-D-4: external-values single-value credential emits an ESO reference object with no secretKeys
    Given the workspace is initialized with test data from "e2e/uc_ec_d_3_eso_multi"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the deployment credentials value for "CONSUL_ADMIN_TOKEN" is an ESO reference to "test-cluster/consul-admin-cred" with no secret keys

# why: EC-D-5 mixed flows — one app gets VALS refs, another app gets ESO refs in the same effective set
  Scenario: UC-EC-D-5: Mixed SECRET_FLOW shapes produce both VALS and ESO references in one effective set
    Given the workspace is initialized with test data from "e2e/uc_ec_d_5_mixed_flows"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "ns-vals" for "app-vals:1.0" 
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "ns-eso" for "app-eso:1.0" 
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the deployment credentials for application "app-vals" hold VALS references
    And the deployment credentials for application "app-eso" hold ESO references

# why: EC-D-7 ESO gate — external-values with eso_support absent in SBOM fails at ES stage
  Scenario: UC-EC-D-7: external-values with ESO disabled fails ES generation
    Given the workspace is initialized with test data from "e2e/uc_ec_d_7_eso_gate"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "generate_effective_set" has status "FAILED"
    And the pipeline log shows "Secret Flow is "external-values" with ESO disabled which is not supported"

# why: EC-D-8 mixed creds at ES — env_build skipped, pre-populated mixed credentials rejected by Java validator
  Scenario: UC-EC-D-8: Mixed external and local credentials at ES stage are rejected
    Given the workspace is initialized with test data from "e2e/uc_ec_d_8_mixed_at_es"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "generate_effective_set" has status "FAILED"
    And the pipeline log shows "mixture of external and non-external credentials is not allowed"

# why: EC-D-9 bad credRef property — property name not in credential's properties list fails ES generation
  Scenario: UC-EC-D-9: credRef property absent from Credential.properties fails ES generation
    Given the workspace is initialized with test data from "e2e/uc_ec_d_9_bad_property"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "generate_effective_set" has status "FAILED"
    And the pipeline log shows "Invalid property"

# why: EC-D-10 unbound store — credential references a secret store absent from secret-stores.yml fails ES generation
  Scenario: UC-EC-D-10: Credential referencing undefined secret store fails ES generation
    Given the workspace is initialized with test data from "e2e/uc_ec_d_10_unbound_store"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline step "generate_effective_set" has status "FAILED"
    And the pipeline log shows "not found in secret file for credential"

#===================================================================================
#Group CTX — external-credential context file (stage: generate_effective_set)
#Feature: External Credentials - deployment effective-set references
#===================================================================================

# why: EC-CTX-1 vault single-value create:true → create_if_absent with value field set to _generateValue
  Scenario: UC-EC-CTX-1: Vault single-value create:true credential emits create_if_absent context entry with value field
    Given the workspace is initialized with test data from "e2e/uc_ec_v_1_external_only"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the external credential context entry "consul-admin-cred" has strategy "create_if_absent"
    And the external credential context entry "consul-admin-cred" has vals "ref+vault://secret/test-cluster/consul-admin-cred"
    And the external credential context entry "consul-admin-cred" has data field "value" equal to "_generateValue"

# why: EC-CTX-2 vault multi-field create:true → create_if_absent with property-keyed data map
  Scenario: UC-EC-CTX-2: Vault multi-field create:true credential emits create_if_absent context entry with property fields
    Given the workspace is initialized with test data from "e2e/uc_ec_v_1_external_only"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the external credential context entry "app-db-cred" has strategy "create_if_absent"
    And the external credential context entry "app-db-cred" has data field "username" equal to "_generateValue"
    And the external credential context entry "app-db-cred" has data field "password" equal to "_generateValue"

# why: EC-CTX-3 create:false → fail_if_absent with no data field
  Scenario: UC-EC-CTX-3: create:false credential emits fail_if_absent context entry without data
    Given the workspace is initialized with test data from "e2e/uc_ec_ctx_3_fail_if_absent"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the external credential context entry "consul-admin-cred" has strategy "fail_if_absent"
    And the external credential context entry "consul-admin-cred" has no data field

# why: EC-CTX-4 GCP single-value create:true → create_if_absent with scalar _generateValue (not a map) (sibling of EC-CTX-1)
  Scenario: UC-EC-CTX-4: GCP single-value create:true credential emits create_if_absent context entry with scalar data
    Given the workspace is initialized with test data from "e2e/uc_ec_d_6_vals_gcp_named_store"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the external credential context entry "consul-admin-cred" has strategy "create_if_absent"
    And the external credential context entry "consul-admin-cred" has a scalar data value "_generateValue"

# why: EC-CTX-5 local-only environment → no external-credential context file produced
  Scenario: UC-EC-CTX-5: Local-only environment produces no external credential context file
    Given the workspace is initialized with test data from "e2e/uc_ec_v_2_local_only"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with deployPostfix "core" for "app1:1.0"
    And the environment AppDefs and RegDefs paths are resolved for the deploy
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the external credential context file does not exist
