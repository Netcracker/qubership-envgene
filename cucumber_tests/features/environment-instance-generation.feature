Feature: Environment Instance Generation - environment-instance-generation.md
  As an EnvGene orchestrator
  I want to generate environment instances from templates
  So that namespace folders, artifact selection, and effective-set generation work correctly

  # ── Namespace Folder Name Generation ────────────────────────────────────────
  # Mock artifact (test-artifact:v1) provides a single Namespace.yml.j2 template
  # with name: dummy-namespace.  deploy_postfix overrides the folder name; without
  # it the folder defaults to the template stem ("Namespace").
  # For BG roles the suffix (-origin / -peer) is added based on bg_domain.yml.

  Scenario Outline: UC-EIG-NF: Namespace folder name - <description>
    Given the workspace is initialized with test data from "e2e/<test_data_dir>"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace folder "<expected_folder>" exists in the environment instance

    Examples:
      | description                                 | test_data_dir | expected_folder    |
      | non-BG with deploy_postfix                  | uc_eig_nf_1   | core               |
      | non-BG without deploy_postfix               | uc_eig_nf_2   | Namespace          |
      | controller in BG Domain with deploy_postfix | uc_eig_nf_3   | controller         |
      | controller in BG Domain no deploy_postfix   | uc_eig_nf_4   | Namespace          |
      | origin in BG Domain with deploy_postfix     | uc_eig_nf_5   | bss-origin         |
      | origin in BG Domain no deploy_postfix       | uc_eig_nf_6   | Namespace-origin   |
      | peer in BG Domain with deploy_postfix       | uc_eig_nf_7   | bss-peer           |
      | peer in BG Domain no deploy_postfix         | uc_eig_nf_8   | Namespace-peer     |

  # ── Template Artifact Selection ─────────────────────────────────────────────

  Scenario: UC-EIG-TA-1: All objects rendered with single artifact when bgNsArtifacts absent
    Given the workspace is initialized with test data from "e2e/uc_eig_ta_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Use template resolving"

  Scenario: UC-EIG-TA-2: BG namespaces rendered when BG Domain present
    Given the workspace is initialized with test data from "e2e/uc_eig_ta_2"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace folder "bss-origin" exists in the environment instance
    And the namespace folder "bss-peer" exists in the environment instance

  Scenario: UC-EIG-TA-3: bgNsArtifacts ignored when BG Domain absent
    Given the workspace is initialized with test data from "e2e/uc_eig_ta_3"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Use template resolving"

  # ── Effective Set Generation in Instance Pipeline ────────────────────────────

  Scenario: UC-EIG-ES-1: Effective Set generated without SD_DATA or SD_VERSION
    Given the workspace is initialized with test data from "e2e/uc_eig_es_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "START: generate_effective_set"
    And the pipeline log does not contain "START: process_sd"

  Scenario: UC-EIG-ES-2: Effective Set generated with SD_DATA
    Given the workspace is initialized with test data from "e2e/uc_eig_es_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "SD_DATA" is set to "{\"applications\":[{\"version\":\"test_app:1.0.0\",\"deployPostfix\":\"dp1\"}],\"deployGraph\":[{\"chunkName\":\"wave1\",\"apps\":[\"test_app:dp1\"]}]}"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "START: process_sd"
    And the pipeline log contains "START: generate_effective_set"

  Scenario: UC-EIG-ES-3: CUSTOM_PARAMS applied when GENERATE_EFFECTIVE_SET is true
    Given the workspace is initialized with test data from "e2e/uc_eig_es_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "param1=value1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "START: generate_effective_set"

  Scenario: UC-EIG-ES-4: generate_effective_set skipped when GENERATE_EFFECTIVE_SET is false
    Given the workspace is initialized with test data from "e2e/uc_eig_es_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "false"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "param1=value1"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log does not contain "START: generate_effective_set"

  # ── Multiple Environments Processing ────────────────────────────────────────

  Scenario: UC-EIG-ME-1: Multiple environments processed in parallel
    Given the workspace is initialized with test data from "e2e/uc_eig_me_1"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/env-a\ntest-cluster/env-b"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace folder "core" exists in environment "test-cluster/env-a"
    And the namespace folder "core" exists in environment "test-cluster/env-b"
