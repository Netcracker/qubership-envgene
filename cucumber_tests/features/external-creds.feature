Feature: External Credentials Management
  As an EnvGene pipeline
  I want to manage credentials stored in external secret stores
  So that sensitive data never lives encrypted in the repository

 # ── Group A - External Credential Context file (external-credentials.yaml) ──────────────────

 # why: A1 - Vault single-value credential with create:true emits a create_if_absent entry with data
Scenario: UC-EC-A1: Vault single-value create:true emits create_if_absent context entry
  Given the workspace is initialized with test data from "e2e/uc-ec-a1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the external credential context file contains "strategy: create_if_absent"
  And the external credential context file contains "value: _generateValue"

# why: A2 - GCP single credential emits a scalar _generateValue (GCP addresses the secret directly)
Scenario: UC-EC-A2: GCP single-value create:true emits scalar _generateValue context entry
  Given the workspace is initialized with test data from "e2e/uc-ec-a2"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the external credential context file contains "strategy: create_if_absent"
  And the external credential context file contains "data: _generateValue"

# why: A3 (sibling A1) - create absent or false emits fail_if_absent with no data field
Scenario: UC-EC-A3: create false emits fail_if_absent with no data field
  Given the workspace is initialized with test data from "e2e/uc-ec-a3"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the external credential context file contains "strategy: fail_if_absent"
  And the external credential context entry "consul-cred" has no data field

# why: A4 - no external credentials means the context file is not produced at all
Scenario: UC-EC-A4: no external credentials produces no context file
  Given the workspace is initialized with test data from "e2e/uc-ec-a4"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the external credential context file is absent
  
# why: A5 - a non-default secretStore adds the secret_store_id query parameter to the vals URI
Scenario: UC-EC-A5: non-default secretStore carries secret_store_id in the vals URI
  Given the workspace is initialized with test data from "e2e/uc-ec-a3"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the external credential context file contains "secret_store_id=prod_store"


 # ──────────── Group B - Reference shape in deployment credentials.yaml ──────────────────

 # why: B1 - helm-values flow emits a VALS ref+ URI string
Scenario: UC-EC-B1: SECRET_FLOW helm-values emits a VALS ref+ URI
  Given the workspace is initialized with test data from "e2e/uc-ec-b1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "ref+vault://"

# why: B2 - external-values with eso_support true emits an ESO object
Scenario: UC-EC-B2: SECRET_FLOW external-values with eso_support true emits an ESO object
  Given the workspace is initialized with test data from "e2e/uc-ec-b2"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "secretStoreId:"
  And the effective set deployment parameters contain "normalizedSecretName:"

# why: B3 (negative) - external-values with eso_support false fails at the ESO capability gate
Scenario: UC-EC-B3: SECRET_FLOW external-values with eso_support false fails at the ESO gate
  Given the workspace is initialized with test data from "e2e/uc-ec-b3"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "ESO disabled"

# why: B4/B5/B6 - the VALS URI fragment follows the store and the credential structure
Scenario: UC-EC-B4: Vault single-value VALS URI carries the value fragment
  Given the workspace is initialized with test data from "e2e/uc-ec-b1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "#/value"

Scenario: UC-EC-B6: multi-field credRef with property username carries the username fragment
  Given the workspace is initialized with test data from "e2e/uc-ec-b6"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "#/username"

# why: B7 - single-value credential on a flat store (GCP) carries no fragment
Scenario: UC-EC-B7: GCP single-value VALS URI has no fragment
  Given the workspace is initialized with test data from "e2e/uc-ec-b7"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "ref+gcpsecrets://"
  And the deployment credentials file does not contain "#/"

# why: B8 - a non-default secretStore adds secret_store_id to the deployment VALS URI (AWS uses & since
# it already carries ?region=)
Scenario: UC-EC-B8: non-default secretStore carries secret_store_id in the deployment VALS URI
  Given the workspace is initialized with test data from "e2e/uc-ec-b1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "secret_store_id=prod_store"

# why: B9 (negative) - a credRef with a property not declared in the credential's properties fails
Scenario: UC-EC-B9: credRef property mismatch fails Effective Set generation
  Given the workspace is initialized with test data from "e2e/uc-ec-b9"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "Invalid property"

# why: B10 (negative, independent of B9) - a credRef with no property on a multi-field credential fails
Scenario: UC-EC-B10: credRef without property against a multi-field credential fails
  Given the workspace is initialized with test data from "e2e/uc-ec-b10"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "no property provided"

# why: B11 - external-values multi-field emits an ESO object with secretKeys (sharpens B2)
Scenario: UC-EC-B11: external-values multi-field ESO object carries secretKeys
  Given the workspace is initialized with test data from "e2e/uc-ec-b11"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "secretKeys:"

# why: B12 (sibling B11) - external-values single-value emits an ESO object without secretKeys
Scenario: UC-EC-B12: external-values single-value ESO object omits secretKeys
  Given the workspace is initialized with test data from "e2e/uc-ec-b12"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "secretStoreId:"
  And the deployment credentials file does not contain "secretKeys:"


# ──────────────── Group C - Environment-instance validation ────────────────────────────

# why: C1 - an all-external credential instance generates successfully
Scenario: UC-EC-C1: all-external credential instance generates successfully
  Given the workspace is initialized with test data from "e2e/uc-ec-c1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully

# why: C2 (negative) - a mix of external and local credentials fails the single-category rule
Scenario: UC-EC-C2: mixed external and local credentials fail the single-category rule
  Given the workspace is initialized with test data from "e2e/uc-ec-c2"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "single category"

# why: C3 (negative, independent of C2) - a credRef to an absent credId fails naming the source
Scenario: UC-EC-C3: unresolved credRef fails naming the missing credential
  Given the workspace is initialized with test data from "e2e/uc-ec-c3"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "not found in any external credential source"

# why: C5 - an orphan external credential warns but does not fail
Scenario: UC-EC-C5: orphan external credential warns and generation continues
  Given the workspace is initialized with test data from "e2e/uc-ec-c5"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the pipeline log contains "exist in external credential source but are not referred in environment"

# why: C6 - an external credential template with an explicit remoteRefPath is rendered into the env creds
Scenario: UC-EC-C6: external credential template with explicit remoteRefPath is rendered
  Given the workspace is initialized with test data from "e2e/uc-ec-c6"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the environment credentials file contains "remoteRefPath: my/explicit/path"

# why: C7 (sibling C6) - a template without remoteRefPath gets the default <cloud>/<env> injected
Scenario: UC-EC-C7: external credential template without remoteRefPath gets the default path
  Given the workspace is initialized with test data from "e2e/uc-ec-c7"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the environment credentials file contains "remoteRefPath: test-cluster/test-env"

# why: C8 (negative) - a credRef to a local credential fails: it must be type external
Scenario: UC-EC-C8: credRef to a local credential fails in external credentials environment
  Given the workspace is initialized with test data from "e2e/uc-ec-c8"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "Found local credential macros"

# why: C9 (negative, independent) - an external-only environment with no secret-stores.yml fails
Scenario: UC-EC-C9: missing secret in external mode fails Effective Set generation
  Given the workspace is initialized with test data from "e2e/uc-ec-c9"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "secret-stores.yml is not found"


# ────────────────────  Group D - Pipeline context ────────────────────────────────────

# why: D1 - a sensitive e2eParameter credRef resolves to a VALS reference in the pipeline context
Scenario: UC-EC-D1: e2eParameter credRef emits a VALS reference in the pipeline context
  Given the workspace is initialized with test data from "e2e/uc-ec-d1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  # NEW STEP NEEDED: assert content of a pipeline context credentials file
  And the pipeline credentials file contains "ref+vault://"

# why: D2 - the pipeline context stays VALS even under SECRET_FLOW external-values (unlike deployment)
Scenario: UC-EC-D2: pipeline context stays VALS under SECRET_FLOW external-values
  Given the workspace is initialized with test data from "e2e/uc-ec-d2"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the pipeline credentials file contains "ref+vault://"

# why: D3 - a per-consumer pipeline file is produced for a matched consumer parameter
Scenario: UC-EC-D3: a matched consumer parameter produces a per-consumer pipeline credentials file
  Given the workspace is initialized with test data from "e2e/uc-ec-d3"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "EFFECTIVE_SET_CONFIG" is set to "{\"version\":\"v2.0\",\"contexts\":{\"pipeline\":{\"consumers\":[{\"name\":\"argocd\",\"version\":\"v1.0\",\"schema\":{\"$schema\":\"http://json-schema.org/draft-04/schema#\",\"type\":\"object\",\"properties\":{\"INTEGRATION_TOKEN\":{\"type\":\"string\",\"default\":\"admin\"}},\"required\":[\"DB_USERNAME\"]}}]}}}"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the per-consumer pipeline credentials file "argocd" contains "ref+vault://"


# ──────────────────── Group E - Topology context ────────────────────────────────────

# why: E1 - a Namespace.credentialsId built-in reference to an external Credential emits a VALS
# reference at k8s_tokens.<namespace>
Scenario: UC-EC-E1: Namespace.credentialsId to an external Credential emits a VALS reference in topology
  Given the workspace is initialized with test data from "e2e/uc-ec-e1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  # NEW STEP NEEDED: assert content of the topology context credentials file
  And the topology credentials file contains "ref+vault://"


# ──────────────────── Group F - Runtime context ────────────────────────────────────

# why: F1 (negative) - a credRef in technicalConfigurationParameters is rejected; the runtime context
# does not accept sensitive parameters via external Credentials
Scenario: UC-EC-F1: credRef in technicalConfigurationParameters is rejected
  Given the workspace is initialized with test data from "e2e/uc-ec-f1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "technicalConfigurationParameters"


# ──────────────────── Group G - System credentials ────────────────────────────────────

# why: G1 (negative) - a system Credential must not declare create:true (system creds are pre-created)
Scenario: UC-EC-G1: system Credential with create:true is rejected
  Given the workspace is initialized with test data from "e2e/uc-ec-g1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "must not have create"


# ───────────────── Group H - Built-in credential references ─────────────────────────────
# why: H1 - a Cloud built-in reference (for example maasConfig.credentialsId) to an external Credential
# emits VALS references for the fields it reads in the deployment context
Scenario: UC-EC-H1: Cloud built-in reference to an external Credential emits VALS in deployment
  Given the workspace is initialized with test data from "e2e/uc-ec-h1"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the effective set deployment parameters contain "ref+vault://"

# why: H2 (negative) - a built-in reference reading username and password must be backed by a credential
# whose properties declare both fields
Scenario: UC-EC-H2: built-in reference with a property-shape mismatch fails generation
  Given the workspace is initialized with test data from "e2e/uc-ec-h2"
  And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
  And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
  When the unified pipeline orchestrator runs
  Then the pipeline fails
  And the pipeline log contains "property"