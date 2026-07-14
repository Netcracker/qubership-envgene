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
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And 7 SBOM files were removed in total
    And the SBOM directory "app-a" contains 10 files
    And the SBOM directory "app-b" contains 10 files
    And the SBOM directory "app-c" contains 8 files

  Scenario: UC-SBOM-4: Per-application retention with custom version count
    Given the workspace is initialized with test data from "e2e/uc-sbom-4"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And 7 SBOM files were removed in total
    And the SBOM directory "postgres" contains 3 files

  Scenario: UC-SBOM-5: Total /sboms/ size exceeds 1200 MB - keeps newest per application
    Given the workspace is initialized with test data from "e2e/uc-sbom-5"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    And the SBOM files are inflated to exceed the size limit
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "SBOM retention policy is enabled"
    And the pipeline log contains "SBOM directory exceeds size limit"
    And only the single most recent SBOM file remains in each application directory
