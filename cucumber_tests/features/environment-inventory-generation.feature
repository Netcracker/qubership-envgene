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
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-ps-3"

  # ── Credentials ──────────────────────────────────────────────────────────────

  Scenario: UC-EINV-CR-1: Create credentials file
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_1_create.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is created at "cluster" scope
    And the decrypted credentials file "db_creds.yml" at "cluster" scope matches the reference "ref-uc-einv-cr-1"

  Scenario: UC-EINV-CR-2: Replace credentials file
    Given the workspace is initialized with test data from "e2e/uc_einv_cr_2"
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_2_replace.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is updated at "cluster" scope
    And the decrypted credentials file "db_creds.yml" at "cluster" scope matches the reference "ref-uc-einv-cr-2"

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
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-rp-3"

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
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-stv-3"

  # ── Atomic rollback ───────────────────────────────────────────────────────────

  # ── Minimal content ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-BASIC-1: Generate minimal Environment Inventory (init)
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_basic_1_minimal.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the "env_definition.yml" file is created
    And the generated env_definition contains minimal required fields
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-basic-1"

  # ── Rollback (Negative) ───────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-2: Rollback on invalid ENV_INVENTORY_CONTENT (schema validation failure)
    Given the repository has an initial state for rollback testing
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_at_all_2_invalid.json"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the repository state is identical to the initial state
    And the pipeline logs contain "Validation failed"

  Scenario: UC-EINV-AT-ALL-3: Failed run does not reach git_commit
    Given the repository has an initial state for rollback testing
    And the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_at_all_3_fail.json"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log does not contain "START: git_commit"

  # ── Combined Operations ───────────────────────────────────────────────────────

  Scenario: UC-EINV-MULTI-1: Apply combined payload with multiple object types in one run
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_multi_1_combine.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline logs contain "Processing parameters, action=create_or_replace, place=env. Target path"
    And the pipeline logs contain "Processing credentials, action=create_or_replace, place=cluster. Target path"
    And the pipeline logs contain "Processing resource_profiles, action=create_or_replace, place=env. Target path"
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-einv-multi-1"

  # ── Scope Variants ────────────────────────────────────────────────────────────

  Scenario Outline: UC-EINV-PS-4: Create paramset file at "<place>" scope
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_ps_4_<place>.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the paramset file "app_params.yml" is created at "<place>" scope

    Examples:
      | place   |
      | cluster |
      | site    |

  Scenario Outline: UC-EINV-CR-4: Create credentials file at "<place>" scope
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_cr_4_<place>.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the credentials file "db_creds.yml" is created at "<place>" scope

    Examples:
      | place |
      | env   |
      | site  |

  Scenario Outline: UC-EINV-RP-4: Create resource profile file at "<place>" scope
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_rp_4_<place>.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the resource_profile file "db_profile.yml" is created at "<place>" scope

    Examples:
      | place   |
      | cluster |
      | site    |

  Scenario Outline: UC-EINV-STV-4: Create Shared Template Variable file at "<place>" scope
    Given the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "einv/env_inventory_content/uc_einv_stv_4_<place>.json"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the shared_template_variable file "prod_vars.yml" is created at "<place>" scope

    Examples:
      | place   |
      | cluster |
      | site    |
