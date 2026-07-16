Feature: Environment Inventory Generation
  As an EnvGene orchestrator
  I want to generate or modify Environment Inventory files based on input content
  So that I can automate the setup of the environment configurations

  Background:
    Given the pipeline has ENV_BUILD set to "false"

  # ── env_definition.yml ──────────────────────────────────────────────────────

  Scenario: UC-EINV-ED-1: Create env_definition.yml
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ed_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is created
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-ed-1"

  Scenario: UC-EINV-ED-2: Replace env_definition.yml
    Given the workspace is initialized with test data from "e2e/uc_einv_ed_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ed_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is updated
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-ed-2"

  Scenario: UC-EINV-ED-3: Delete env_definition.yml
    Given the workspace is initialized with test data from "e2e/uc_einv_ed_3"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ed_3_delete.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is deleted
    And the environment directory is deleted

  # ── Paramsets ────────────────────────────────────────────────────────────────

  Scenario: UC-EINV-PS-1: Create paramset file
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ps_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the paramset file "app_params.yml" is created at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-ps-1"

  Scenario: UC-EINV-PS-2: Replace paramset file
    Given the workspace is initialized with test data from "e2e/uc_einv_ps_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ps_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the paramset file "app_params.yml" is updated at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-ps-2"

  Scenario: UC-EINV-PS-3: Delete paramset file
    Given the workspace is initialized with test data from "e2e/uc_einv_ps_3"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ps_3_delete.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the paramset file "app_params.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Credentials ──────────────────────────────────────────────────────────────

  Scenario: UC-EINV-CR-1: Create credentials file
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is created at "cluster" scope

  Scenario: UC-EINV-CR-2: Replace credentials file
    Given the workspace is initialized with test data from "e2e/uc_einv_cr_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is updated at "cluster" scope

  Scenario: UC-EINV-CR-3: Delete credentials file
    Given the workspace is initialized with test data from "e2e/uc_einv_cr_3"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_3_delete.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is deleted at "cluster" scope
    And its parent directory is not deleted

  # ── Resource Profiles ────────────────────────────────────────────────────────

  Scenario: UC-EINV-RP-1: Create resource profile override file
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_rp_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the resource_profile file "db_profile.yml" is created at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-rp-1"

  Scenario: UC-EINV-RP-2: Replace resource profile override file
    Given the workspace is initialized with test data from "e2e/uc_einv_rp_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_rp_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the resource_profile file "db_profile.yml" is updated at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-rp-2"

  Scenario: UC-EINV-RP-3: Delete resource profile override file
    Given the workspace is initialized with test data from "e2e/uc_einv_rp_3"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_rp_3_delete.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the resource_profile file "db_profile.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Shared Template Variables ─────────────────────────────────────────────────

  Scenario: UC-EINV-STV-1: Create Shared Template Variable file
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_stv_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the shared_template_variable file "prod_vars.yml" is created at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-stv-1"

  Scenario: UC-EINV-STV-2: Replace Shared Template Variable file
    Given the workspace is initialized with test data from "e2e/uc_einv_stv_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_stv_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the shared_template_variable file "prod_vars.yml" is updated at "env" scope
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-stv-2"

  Scenario: UC-EINV-STV-3: Delete Shared Template Variable file
    Given the workspace is initialized with test data from "e2e/uc_einv_stv_3"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_stv_3_delete.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the shared_template_variable file "prod_vars.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Atomic rollback ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails
    Given the repository has an initial state for rollback testing
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_at_all_1_rollback.json"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline logs contain a readable error message explaining the failure reason
    And the repository state is identical to the initial state

  # ── Minimal content ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-BASIC-1: Generate minimal Environment Inventory (init)
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_basic_1_minimal.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is created
    And the generated env_definition contains minimal required fields
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-basic-1"

  # ── ENV_INVENTORY_INIT (deprecated, backward compat) ──────────────────────────

  @xfail
  Scenario: UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist
    Given the ENV_INVENTORY_INIT is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is created

  Scenario: UC-EINV-INIT-2: Init inventory when env_definition.yml already exists
    Given the workspace is initialized with test data from "e2e/uc_einv_init_2"
    And the ENV_INVENTORY_INIT is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is updated
    And the pipeline succeeds

  # ── Template Version Update ───────────────────────────────────────────────────

  Scenario: UC-EINV-TV-1-PERSISTENT: Apply ENV_TEMPLATE_VERSION in PERSISTENT mode
    Given the workspace is initialized with test data from "e2e/uc_einv_tv_1_persistent"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ed_1_create.json"
    And the ENV_TEMPLATE_VERSION is set to "env-templates:2.0.0" and update mode is "PERSISTENT"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file has envTemplate.artifact equal to "env-templates:2.0.0"

  Scenario: UC-EINV-TV-1-TEMPORARY: Apply ENV_TEMPLATE_VERSION in TEMPORARY mode
    Given the workspace is initialized with test data from "e2e/uc_einv_tv_1_temporary"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ed_1_create.json"
    And the ENV_TEMPLATE_VERSION is set to "env-templates:2.0.0" and update mode is "TEMPORARY"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file has generatedVersions.generateEnvironmentLatestVersion equal to "env-templates:2.0.0"
    And the "env_definition.yml" file envTemplate.artifact is not changed

  # ── Rollback (Negative) ───────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-2: Rollback on invalid ENV_INVENTORY_CONTENT (schema validation failure)
    Given the repository has an initial state for rollback testing
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_at_all_2_invalid.json"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the repository state is identical to the initial state
    And the pipeline logs contain "Validation failed"
