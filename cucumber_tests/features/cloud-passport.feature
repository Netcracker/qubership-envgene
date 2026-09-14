Feature: Cloud Passport association - cloud-passport.md
  As an EnvGene operator
  I want environments to automatically associate and merge a Cloud Passport during build
  So that cloud.yml reflects passport-provided infrastructure parameters, each traceable to its
  source

  # process_cloud_passport (scripts/cloud_passport/cloud_passport.py) runs unconditionally as
  # part of env_build's cloud processing, so ENV_BUILDER=true alone is enough to trigger it -
  # none of these scenarios need GENERATE_EFFECTIVE_SET or the real Effective Set CLI.

  Background:
    Given the pipeline parameter "ENV_BUILDER" is set to "true"

  # ── UC-01: auto-association with the cluster default passport ──────────────────
  # No inventory.cloudPassport is set, so the system walks up to the cluster level and picks
  # cloud-passport/passport.yml (the fixed default name) automatically.

  Scenario: UC-01: Environment inherits cluster Cloud Passport automatically
    Given the workspace is initialized with test data from "e2e/uc_cp_01_auto_association"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the cloud.yml contains "apiUrl: https://uc01-api.example.com"
    And the cloud.yml contains "ZOOKEEPER_ADDRESS: zookeeper.zookeeper:2181"
    # UC-05: every passport-derived parameter carries an inline traceability comment
    And the cloud.yml parameter "apiUrl" has traceability comment "cloud passport: passport version: 1.5"
    And the cloud.yml parameter "ZOOKEEPER_ADDRESS" has traceability comment "cloud passport: passport version: 1.5"

  # ── UC-02: explicit named passport, resolved ahead of the cluster default ──────
  # inventory.cloudPassport names "custom-passport" explicitly; a decoy default
  # cloud-passport/passport.yml also exists at the same level and must NOT be picked.

  Scenario: UC-02: Environment uses explicitly named Cloud Passport
    Given the workspace is initialized with test data from "e2e/uc_cp_02_explicit_named"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "apiUrl: https://custom-api.example.com"
    And the cloud.yml contains "STORAGE_ADDRESS: storage.example.com:9000"
    And the cloud.yml does not contain "decoy-default-api"
    And the cloud.yml parameter "apiUrl" has traceability comment "cloud passport: custom-passport version: 2.0"

  # why: find_passport_by_env_definition (business_helper.py) raises FileNotFoundError for an
  # unresolvable explicit name, uncaught, so the whole build fails - the doc's "build fails with
  # an error" alternate flow. (The doc's other alternate flow, "if multiple matches exist: the
  # build fails with a duplicate-passport error", is not covered here: find_yaml_file - used for
  # this explicit-name lookup - returns the first os.walk match with no duplicate check at all;
  # only the separate auto-association lookup, findPassportInDefaultDirByName, has that check.
  # That's a doc/code divergence for a future fix, not something to pin to unstable directory
  # walk order.)
  Scenario: UC-02 alternate flow: build fails when the explicitly named passport has no match
    Given the workspace is initialized with test data from "e2e/uc_cp_02_no_match"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "does-not-exist"

  # ── UC-03: no passport anywhere, no explicit name - build proceeds unaffected ──

  Scenario: UC-03: Environment builds without Cloud Passport
    Given the workspace is initialized with test data from "e2e/uc_cp_03_no_passport"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline log contains "No cloud passport definition found. Cloud passport processing skipped"
    And the cloud.yml does not contain "cloud passport:"

  # ── UC-04: explicit passport resolved from the env's own Inventory (custom location) ──
  # find_passport_by_env_definition searches env_dir/Inventory before the cluster level, so a
  # passport placed there is found without ever needing a cluster-level cloud-passport/ dir.

  Scenario: UC-04: Environment uses passport from custom location
    Given the workspace is initialized with test data from "e2e/uc_cp_04_custom_location"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "apiUrl: https://custom-location-api.example.com"
    And the cloud.yml contains "STORAGE_ADDRESS: storage-custom.example.com:9000"
    And the cloud.yml parameter "apiUrl" has traceability comment "cloud passport: custom-passport version: 2.5"

  # ── UC-06/UC-07/UC-08/UC-09: mixed cluster (business + infra) passport isolation ──
  # Shared fixture "uc_cp_06_mixed_cluster": one cluster, two environments, two passports -
  # cloud-passport/passport.yml (business default) and cloud-passport/passport-infra.yml.

  # why: the business environment has no inventory.cloudPassport, so it auto-associates the
  # cluster default (business) passport and only ever sees business-only keys.
  Scenario: UC-06: Business environments auto-associate the business passport in a mixed cluster
    Given the workspace is initialized with test data from "e2e/uc_cp_06_mixed_cluster"
    And environment is "mixed-cluster/business-env"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "apiUrl: https://business-api.example.com"
    And the cloud.yml contains "BSS_WORKLOAD_KEY: business-only-value"
    And the cloud.yml does not contain "INFRA_WORKLOAD_KEY"
    And the cloud.yml parameter "BSS_WORKLOAD_KEY" has traceability comment "cloud passport: passport version: 3.0"

  # why: the infra environment names inventory.cloudPassport: passport-infra explicitly, so it
  # resolves passport-infra.yml and never inherits the cluster's business default passport.
  Scenario: UC-07: Infra environments use an explicit infra passport in a mixed cluster
    Given the workspace is initialized with test data from "e2e/uc_cp_06_mixed_cluster"
    And environment is "mixed-cluster/infra-env"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "apiUrl: https://infra-api.example.com"
    And the cloud.yml contains "INFRA_WORKLOAD_KEY: infra-only-value"
    And the cloud.yml does not contain "BSS_WORKLOAD_KEY"
    And the cloud.yml parameter "INFRA_WORKLOAD_KEY" has traceability comment "cloud passport: passport-infra version: 4.0"

  # why: only the business passport exists here (no passport-infra at all), and the infra
  # environment has no explicit inventory.cloudPassport - it falls back to the same
  # cluster-default auto-association as a business environment, so it incorrectly inherits
  # business-only keys. EnvGene's own responsibility ends at cloud.yml generation; the doc's
  # downstream "infra deployer fails" consequence is outside this repository's scope.
  Scenario: UC-08: Mixed cluster failure when infra relies on auto-association
    Given the workspace is initialized with test data from "e2e/uc_cp_08_infra_auto_association"
    And environment is "mixed-cluster/infra-env"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "BSS_WORKLOAD_KEY: business-only-value"
    And the cloud.yml parameter "BSS_WORKLOAD_KEY" has traceability comment "cloud passport: passport version: 3.0"

  # why: reuses UC-06's exact fixture and scenario - that cluster already has the infra passport
  # and infra environment introduced (the doc's "after" state). Getting the identical
  # business-only outcome proves that adding an infra passport, and pointing the infra
  # environment at it, does not change business environment behaviour.
  Scenario: UC-09: Backward compatibility for existing business environments
    Given the workspace is initialized with test data from "e2e/uc_cp_06_mixed_cluster"
    And environment is "mixed-cluster/business-env"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the cloud.yml contains "apiUrl: https://business-api.example.com"
    And the cloud.yml contains "BSS_WORKLOAD_KEY: business-only-value"
    And the cloud.yml does not contain "INFRA_WORKLOAD_KEY"
    And the cloud.yml parameter "BSS_WORKLOAD_KEY" has traceability comment "cloud passport: passport version: 3.0"
