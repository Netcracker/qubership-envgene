Feature: SBOM Retention - sbom-retention.md
  As an EnvGene developer
  I want to ensure the SBOM retention policy correctly manages SBOM files
  So that the Instance Repository size stays within limits

  Scenario: UC-SBOM-1: SBOM retention disabled - no cleanup
    Given the workspace is initialized with test data from "e2e/uc-sbom-1"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is disabled"
    And no SBOM files were removed

  Scenario: UC-SBOM-2: All applications within per-application limit - no files deleted
    Given the workspace is initialized with test data from "e2e/uc-sbom-2"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And no SBOM files were removed
    And the SBOM directory "app-a" contains 7 files
    And the SBOM directory "app-b" contains 4 files
    And the SBOM directory "app-c" contains 10 files

  Scenario: UC-SBOM-3: Per-application retention keeps 10 most recent versions
    Given the workspace is initialized with test data from "e2e/uc-sbom-3"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And SBOM mtimes are assigned by version index in "app-a"
    And SBOM mtimes are assigned by version index in "app-b"
    And SBOM mtimes are assigned by version index in "app-c"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And 7 SBOM files were removed in total
    And the SBOM directory "app-a" contains 10 files
    And the SBOM directory "app-b" contains 10 files
    And the SBOM directory "app-c" contains 8 files
    And the SBOM directory "app-a" contains exactly the files "app-a-v5.sbom.json,app-a-v6.sbom.json,app-a-v7.sbom.json,app-a-v8.sbom.json,app-a-v9.sbom.json,app-a-v10.sbom.json,app-a-v11.sbom.json,app-a-v12.sbom.json,app-a-v13.sbom.json,app-a-v14.sbom.json"
    And the SBOM directory "app-b" contains exactly the files "app-b-v2.sbom.json,app-b-v3.sbom.json,app-b-v4.sbom.json,app-b-v5.sbom.json,app-b-v6.sbom.json,app-b-v7.sbom.json,app-b-v8.sbom.json,app-b-v9.sbom.json,app-b-v10.sbom.json,app-b-v11.sbom.json"

  Scenario: UC-SBOM-4: Per-application retention with custom version count
    Given the workspace is initialized with test data from "e2e/uc-sbom-4"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And SBOM mtimes are assigned by version index in "postgres"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And 7 SBOM files were removed in total
    And the SBOM directory "postgres" contains 3 files
    And the SBOM directory "postgres" contains exactly the files "postgres-v7.sbom.json,postgres-v8.sbom.json,postgres-v9.sbom.json"

  Scenario: UC-SBOM-5: Total /sboms/ size exceeds 600 MB - keeps newest per application
    Given the workspace is initialized with test data from "e2e/uc-sbom-5"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And SBOM mtimes are assigned by version index in "app1"
    And SBOM mtimes are assigned by version index in "app2"
    And SBOM mtimes are assigned by version index in "app3"
    And the SBOM files are inflated to exceed the size limit
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And the pipeline log contains "SBOM directory exceeds size limit"
    And only the single most recent SBOM file remains in each application directory
    And the SBOM directory "app1" contains exactly the files "app1-v7.sbom.json"
    And the SBOM directory "app2" contains exactly the files "app2-v4.sbom.json"
    And the SBOM directory "app3" contains exactly the files "app3-v9.sbom.json"

  Scenario: UC-SBOM-6: Legacy flat SBOM files at the top of /sboms/ are removed
    Given the workspace is initialized with test data from "e2e/uc-sbom-6"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Removing legacy SBOM file:"
    And no flat SBOM files remain at the top of the sboms directory
    And the SBOM directory "app-a" contains 3 files

  Scenario: UC-SBOM-7: Enabled retention without keep_versions_per_app skips per-application cleanup
    Given the workspace is initialized with test data from "e2e/uc-sbom-7"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "SBOM retention policy is enabled"
    And no SBOM files were removed
    And the SBOM directory "app-a" contains 15 files
