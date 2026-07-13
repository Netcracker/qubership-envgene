Feature: Environment Inventory Generation
  As an EnvGene orchestrator
  I want to generate or modify Environment Inventory files based on input content
  So that I can automate the setup of the environment configurations

  Background:
    Given the pipeline has ENV_BUILD set to "false"

  # ── env_definition.yml ──────────────────────────────────────────────────────

  Scenario: UC-EINV-ED-1: Create env_definition.yml
  # Call chain: generate_env_new_approach() → validate_yaml_by_scheme_or_fail(env-inventory-content.schema.json)
  #   → handle_env_inv_content() → handle_env_def() → writeYamlToFile(Inventory/env_definition.yml) → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); env_definition.yml is created at
  #   environments/<cluster>/<env>/Inventory/; file content equals the request payload (strict match)
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition"
    Then it validates "envDefinition" against the request schema
    And it validates "envDefinition.content" against the "env_definition.yml" schema
    And the "env_definition.yml" file is created
    And its content matches the payload

  Scenario: UC-EINV-ED-2: Replace env_definition.yml
  # Call chain: generate_env_new_approach() → validate_yaml_by_scheme_or_fail(env-inventory-content.schema.json)
  #   → handle_env_inv_content() → handle_env_def() → writeYamlToFile(Inventory/env_definition.yml) overwrites the existing file unconditionally → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); existing env_definition.yml is replaced;
  #   file content equals the request payload (strict match)
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition"
    Then it validates "envDefinition" against the request schema
    And it validates "envDefinition.content" against the "env_definition.yml" schema
    And the "env_definition.yml" file is updated
    And its content matches the payload

  Scenario: UC-EINV-ED-3: Delete env_definition.yml
  # Call chain: generate_env_new_approach() → handle_env_inv_content() → handle_env_def()
  #   → action == DELETE → delete_dir(env_dir) removes the entire <cluster>/<env>/ directory
  # Verifies: env_definition.yml no longer exists; the parent environment directory is also deleted
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for "envDefinition"
    Then the "env_definition.yml" file is deleted
    And the environment directory is deleted

  # ── Paramsets ────────────────────────────────────────────────────────────────

  Scenario: UC-EINV-PS-1: Create paramset file
  # Call chain: handle_objects(env_dir, paramSets, "parameters", "Inventory", encrypt=False)
  #   → resolve_path(Place.ENV) → Inventory/parameters/app_params.yml
  #   → writeYamlToFile() → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); app_params.yml is created under
  #   Inventory/parameters/; file content equals the request payload (strict match)
    Given the target paramset file "app_params" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for paramset "app_params" at "env" scope
    Then it validates "paramSets" against the request schema
    And it validates "paramSets[].content" against the "parameters.yml" schema
    And the paramset file "app_params.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-PS-2: Replace paramset file
  # Call chain: handle_objects(env_dir, paramSets, "parameters", "Inventory", encrypt=False)
  #   → resolve_path(Place.ENV) → Inventory/parameters/app_params.yml
  #   → writeYamlToFile() overwrites the existing file → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); existing app_params.yml is replaced;
  #   file content equals the request payload (strict match)
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for paramset "app_params" at "env" scope
    Then it validates "paramSets" against the request schema
    And it validates "paramSets[].content" against the "parameters.yml" schema
    And the paramset file "app_params.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-PS-3: Delete paramset file
  # Call chain: handle_objects() → action == DELETE → deleteFileIfExists(app_params.yml)
  #   (directory is not touched)
  # Verifies: app_params.yml is deleted; parent Inventory/parameters/ directory still exists
    Given the target paramset file "app_params" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for paramset "app_params" at "env" scope
    Then the paramset file "app_params.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Credentials ──────────────────────────────────────────────────────────────

  Scenario: UC-EINV-CR-1: Create credentials file
  # Call chain: handle_objects(env_dir, credentials, "credentials", "Inventory", encrypt=True)
  #   → resolve_path(Place.CLUSTER) → <cluster>/credentials/db_creds.yml (Inventory folder ignored)
  #   → writeYamlToFile() → encrypt_file() (Fernet encrypts data.username / data.password) → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); db_creds.yml is created at cluster scope;
  #   file contains the credential key and correct "type" field (data values not compared — Fernet-encrypted)
    Given the target credentials file "db_creds" does not exist at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for credentials "db_creds" at "cluster" scope
    Then it validates "credentials" against the request schema
    And it validates "credentials[].content" against the "credentials.yml" schema
    And the credentials file "db_creds.yml" is created at "cluster" scope
    And its content matches the payload

  Scenario: UC-EINV-CR-2: Replace credentials file
  # Call chain: handle_objects(env_dir, credentials, "credentials", "Inventory", encrypt=True)
  #   → resolve_path(Place.CLUSTER) → <cluster>/credentials/db_creds.yml (Inventory folder ignored)
  #   → writeYamlToFile() → encrypt_file() (Fernet encrypts data.username / data.password) overwrites the existing file → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); existing db_creds.yml is replaced;
  #   file contains the credential key and correct "type" field (data values not compared — Fernet-encrypted)
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for credentials "db_creds" at "cluster" scope
    Then it validates "credentials" against the request schema
    And it validates "credentials[].content" against the "credentials.yml" schema
    And the credentials file "db_creds.yml" is updated at "cluster" scope
    And its content matches the payload

  Scenario: UC-EINV-CR-3: Delete credentials file
  # Call chain: handle_objects() → action == DELETE → deleteFileIfExists(db_creds.yml)
  #   (directory is not touched)
  # Verifies: db_creds.yml is deleted; parent <cluster>/credentials/ directory still exists
    Given the target credentials file "db_creds" exists at "cluster" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for credentials "db_creds" at "cluster" scope
    Then the credentials file "db_creds.yml" is deleted at "cluster" scope
    And its parent directory is not deleted

  # ── Resource Profiles ────────────────────────────────────────────────────────

  Scenario: UC-EINV-RP-1: Create resource profile override file
  # Call chain: handle_objects(env_dir, resourceProfiles, "resource_profiles", "Inventory", encrypt=False)
  #   → resolve_path(Place.ENV) → Inventory/resource_profiles/db_profile.yml
  #   → writeYamlToFile() → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); db_profile.yml is created under
  #   Inventory/resource_profiles/; file content equals the request payload (strict match)
    Given the target resource_profile file "db_profile" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for resource_profile "db_profile" at "env" scope
    Then it validates "resourceProfiles" against the request schema
    And it validates "resourceProfiles[].content" against the "resourceProfiles.yml" schema
    And the resource_profile file "db_profile.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-RP-2: Replace resource profile override file
  # Call chain: handle_objects(env_dir, resourceProfiles, "resource_profiles", "Inventory", encrypt=False)
  #   → resolve_path(Place.ENV) → Inventory/resource_profiles/db_profile.yml
  #   → writeYamlToFile() overwrites the existing file → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); existing db_profile.yml is replaced;
  #   file content equals the request payload (strict match)
    Given the target resource_profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for resource_profile "db_profile" at "env" scope
    Then it validates "resourceProfiles" against the request schema
    And it validates "resourceProfiles[].content" against the "resourceProfiles.yml" schema
    And the resource_profile file "db_profile.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-RP-3: Delete resource profile override file
  # Call chain: handle_objects() → action == DELETE → deleteFileIfExists(db_profile.yml)
  #   (directory is not touched)
  # Verifies: db_profile.yml is deleted; parent Inventory/resource_profiles/ directory still exists
    Given the target resource_profile file "db_profile" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for resource_profile "db_profile" at "env" scope
    Then the resource_profile file "db_profile.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Shared Template Variables ─────────────────────────────────────────────────

  Scenario: UC-EINV-STV-1: Create Shared Template Variable file
  # Call chain: handle_objects(env_dir, sharedTemplateVariables, "shared_template_variables", "", encrypt=False)
  #   → resolve_path(Place.ENV, inventory="") → shared_template_variables/prod_vars.yml (no Inventory folder)
  #   → writeYamlToFile() → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); prod_vars.yml is created directly under
  #   <env>/shared_template_variables/ (not inside Inventory/); file content equals the request payload
    Given the target shared_template_variable file "prod_vars" does not exist at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for shared_template_variable "prod_vars" at "env" scope
    Then it validates "sharedTemplateVariables" against the request schema
    And it validates "sharedTemplateVariables[].content" against the "shared_template_variables.yml" schema
    And the shared_template_variable file "prod_vars.yml" is created at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-STV-2: Replace Shared Template Variable file
  # Call chain: handle_objects(env_dir, sharedTemplateVariables, "shared_template_variables", "", encrypt=False)
  #   → resolve_path(Place.ENV, inventory="") → shared_template_variables/prod_vars.yml (no Inventory folder)
  #   → writeYamlToFile() overwrites the existing file → beautifyYaml()
  # Verifies: JSON Schema validation passes (returncode == 0); existing prod_vars.yml is replaced;
  #   file content equals the request payload (strict match)
    Given the target shared_template_variable file "prod_vars" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for shared_template_variable "prod_vars" at "env" scope
    Then it validates "sharedTemplateVariables" against the request schema
    And it validates "sharedTemplateVariables[].content" against the "shared_template_variables.yml" schema
    And the shared_template_variable file "prod_vars.yml" is updated at "env" scope
    And its content matches the payload

  Scenario: UC-EINV-STV-3: Delete Shared Template Variable file
  # Call chain: handle_objects() → action == DELETE → deleteFileIfExists(prod_vars.yml)
  #   (directory is not touched)
  # Verifies: prod_vars.yml is deleted; parent shared_template_variables/ directory still exists
    Given the target shared_template_variable file "prod_vars" exists at "env" scope
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "delete" for shared_template_variable "prod_vars" at "env" scope
    Then the shared_template_variable file "prod_vars.yml" is deleted at "env" scope
    And its parent directory is not deleted

  # ── Atomic rollback ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails
  # Call chain: generate_env_new_approach() → validate_yaml_by_scheme_or_fail() raises on invalid "action"
  #   enum value → orchestrator exits before any writeYamlToFile() call
  # Verifies: pipeline exits with non-zero code; logs contain "Validation failed";
  #   filesystem tree after the run is byte-for-byte identical to the pre-run snapshot
  #   (compare_directories(pre_run_snapshot_dir, base_dir))
    Given the repository has an initial state for rollback testing
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying multiple operations where one fails
    Then the pipeline fails
    And the pipeline logs contain a readable error message explaining the failure reason
    And the repository state is identical to the initial state

  # ── Minimal content ───────────────────────────────────────────────────────────

  Scenario: UC-EINV-BASIC-1: Generate minimal Environment Inventory (init)
  # Call chain: generate_env_new_approach() → handle_env_inv_content() → handle_env_def()
  #   → writeYamlToFile(Inventory/env_definition.yml) → beautifyYaml()
  # Verifies: env_definition.yml is created from the minimal valid payload (inventory + envTemplate only);
  #   the written file contains both top-level keys "inventory" and "envTemplate"
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "create_or_replace" for "envDefinition" with minimal content
    Then the "env_definition.yml" file is created
    And the generated env_definition contains minimal required fields

  # ── ENV_INVENTORY_INIT (deprecated, backward compat) ──────────────────────────

  @xfail
  Scenario: UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist
  # Call chain: ENV_INVENTORY_CONTENT absent → generate_env() (deprecated) → handle_env_inventory_init()
  #   → Environment.__post_init__() tries to read Credentials/credentials.yml → FileNotFoundError
  # Verifies: expected to fail (@xfail) — deprecated path crashes because the test workspace does not
  #   provide environments/<cluster>/<env>/Credentials/credentials.yml (platform-independent)
    Given the target environment inventory file does not exist
    When the Instance pipeline is started with ENV_INVENTORY_INIT set to "true"
    Then the "env_definition.yml" file is created

  Scenario: UC-EINV-INIT-2: Init inventory when env_definition.yml already exists
  # Call chain: ENV_INVENTORY_CONTENT absent, env_definition.yml present → generate_env() (deprecated)
  #   → handle_env_inventory_init() reads and rewrites the existing file
  # Verifies: env_definition.yml still exists after the run (not deleted); pipeline exits with code 0
  #   (backward-compatibility: deprecated path does not crash when the file is already present)
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_INVENTORY_INIT set to "true"
    Then the "env_definition.yml" file is updated
    And the pipeline succeeds

  # ── Template Version Update ───────────────────────────────────────────────────

  Scenario: UC-EINV-TV-1-PERSISTENT: Apply ENV_TEMPLATE_VERSION in PERSISTENT mode
  # Call chain: handle_env_def() receives ENV_TEMPLATE_VERSION + mode=PERSISTENT
  #   → content["envTemplate"]["artifact"] = env_template_version (overwrites existing value)
  # Verifies: env_definition.yml.envTemplate.artifact equals the new version "env-templates:2.0.0"
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_TEMPLATE_VERSION set to "env-templates:2.0.0" and update mode "PERSISTENT"
    Then the "env_definition.yml" file has envTemplate.artifact equal to "env-templates:2.0.0"

  Scenario: UC-EINV-TV-1-TEMPORARY: Apply ENV_TEMPLATE_VERSION in TEMPORARY mode
  # Call chain: handle_env_def() receives ENV_TEMPLATE_VERSION + mode=TEMPORARY
  #   → content["generatedVersions"]["generateEnvironmentLatestVersion"] = env_template_version
  #   → envTemplate.artifact is NOT modified
  # Verifies: generatedVersions.generateEnvironmentLatestVersion equals "env-templates:2.0.0";
  #   envTemplate.artifact retains original value "env-templates:1.0.0" (no overwrite)
    Given the target environment inventory file exists
    When the Instance pipeline is started with ENV_TEMPLATE_VERSION set to "env-templates:2.0.0" and update mode "TEMPORARY"
    Then the "env_definition.yml" file has generatedVersions.generateEnvironmentLatestVersion equal to "env-templates:2.0.0"
    And the "env_definition.yml" file envTemplate.artifact is not changed

  # ── Rollback (Negative) ───────────────────────────────────────────────────────

  Scenario: UC-EINV-AT-ALL-2: Rollback on invalid ENV_INVENTORY_CONTENT (schema validation failure)
  # Call chain: generate_env_new_approach() → validate_yaml_by_scheme_or_fail() raises on
  #   inventory field being a string instead of an object → orchestrator exits before any file write
  # Verifies: pipeline exits with non-zero code; filesystem tree is identical to pre-run snapshot
  #   (compare_directories(pre_run_snapshot_dir, base_dir)); logs contain "Validation failed"
    Given the target environment inventory file exists
    When the Instance pipeline is started with invalid ENV_INVENTORY_CONTENT that fails during processing
    Then the pipeline fails
    And the repository state is identical to the initial state
    And the pipeline logs contain "Validation failed"
