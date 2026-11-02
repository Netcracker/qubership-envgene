Feature: envgeneNullValue validation - envgene-null-value-validation.md
  As an EnvGene operator
  I want unresolved envgeneNullValue values to block the pipeline
  So that no placeholder value can leave the generate_effective_set stage

  # Every scenario triggers the instance pipeline with ENV_NAMES and
  # GENERATE_EFFECTIVE_SET=true, the P1 stage of the use cases. The
  # environment instance is pre-generated (pre-requisites 1-3 of every UC):
  # the "uc_nvv_common" fixture is a fully rendered instance, so no env build
  # runs and the validation sees exactly the fixture content plus whatever
  # the Given steps inject.

  Scenario: UC-NVV-1: Unresolved parameter blocks pipeline
    Given the workspace is initialized with test data from "e2e/uc_nvv_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And a deploy parameter "API_URL" is set to "envgeneNullValue" in namespace "core"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Error while validating parameters:"
    And the pipeline log contains "namespace.core.deployParameters.API_URL - is not set"
    And the pipeline step "generate_effective_set" has status "FAILED"

  Scenario: UC-NVV-2: Unresolved credential blocks pipeline
    Given the workspace is initialized with test data from "e2e/uc_nvv_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the environment instance has these unresolved credentials:
      | cred_id                | type             |
      | dbaas-cluster-dba-cred | usernamePassword |
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Error while validating credentials:"
    And the pipeline log contains "credId: dbaas-cluster-dba-cred - username or password is not set"
    And the pipeline log does not contain "credId: consul-admin-cred - secret is not set"
    And the pipeline step "generate_effective_set" has status "FAILED"

  Scenario: UC-NVV-3: All values resolved
    Given the workspace is initialized with test data from "e2e/uc_nvv_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Validation of parameters is completed"
    And the pipeline log contains "Validation of credentials is completed"
    And the pipeline step "generate_effective_set" has status "SUCCESS"

  Scenario: UC-NVV-4: Multiple unresolved values reported together
    Given the workspace is initialized with test data from "e2e/uc_nvv_common"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the environment instance has these unresolved credentials:
      | cred_id                | type             |
      | dbaas-cluster-dba-cred | usernamePassword |
      | consul-admin-cred      | secret           |
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the pipeline log contains "Error while validating credentials:"
    And the pipeline log contains "credId: dbaas-cluster-dba-cred - username or password is not set"
    And the pipeline log contains "credId: consul-admin-cred - secret is not set"
    And the pipeline step "generate_effective_set" has status "FAILED"
