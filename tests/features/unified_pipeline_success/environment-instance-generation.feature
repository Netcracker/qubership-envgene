Feature: Unified Pipeline Successful Execution - environment-instance-generation.md
  As an EnvGene developer
  I want to ensure the unified pipeline completes successfully with various parameter combinations
  So that different use case triggers do not cause pipeline failures

  Scenario: UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-2: Namespace NOT in BG Domain without deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-3: Controller Namespace in BG Domain with deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-4: Controller Namespace in BG Domain without deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_4_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-5: Origin Namespace in BG Domain with deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_5_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-6: Origin Namespace in BG Domain without deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_6_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-7: Peer Namespace in BG Domain with deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_7_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-NF-8: Peer Namespace in BG Domain without deploy_postfix
    Given the workspace is initialized with test data from "cucumber/uc_eig_nf_8_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-TA-1: Environment Instance Generation with `artifact` only
    Given the workspace is initialized with test data from "cucumber/uc_eig_ta_1_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-TA-2: Environment Instance Generation with `artifact` and `bgNsArtifacts` and BG Domain
    Given the workspace is initialized with test data from "cucumber/uc_eig_ta_2_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-TA-3: Environment Instance Generation with `artifact` and `bgNsArtifacts` and without BG Domain
    Given the workspace is initialized with test data from "cucumber/uc_eig_ta_3_base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"

  Scenario: UC-EIG-ES-4: Ignore `CUSTOM_PARAMS` when `GENERATE_EFFECTIVE_SET` is false
    Given the workspace is initialized with test data from "cucumber/uc_eig_es_4_base"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "false"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-group-1"
