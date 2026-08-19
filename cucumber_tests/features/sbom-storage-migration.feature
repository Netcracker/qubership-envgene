Feature: SBOM Storage Migration - sbom-storage-migration.md
  As an EnvGene developer
  I want flat SBOM files to be removed automatically on the first run after upgrade
  So that the repository contains only the per-application layout going forward

  Scenario: UC-SBOM-MIG-1: First run after upgrade removes flat-layout SBOMs
    Given the workspace is initialized with test data from "e2e/uc_sbom_mig_1"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "SBOM retention policy is enabled"
    And the pipeline log contains "Removing legacy SBOM file"
    And no flat SBOM files remain directly under the sboms directory
