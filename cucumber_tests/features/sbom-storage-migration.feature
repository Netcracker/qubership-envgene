Feature: SBOM Storage Migration - sbom-storage-migration.md
  As an EnvGene developer
  I want flat SBOM files to be removed automatically on the first run after upgrade
  So that the repository contains only the per-application layout going forward

  # why: replaces the current UC-SBOM-MIG-1 body so it tests what UC-SBOM-6 does not -
  # the "first run after upgrade" starting from a pure flat layout, and idempotency:
  # a second run finds nothing to migrate (Result 3 of sbom-storage-migration.md).
  # Needs the uc-sbom-mig-1 fixture reduced to flat files only (no test_app/ subdir).
  Scenario: UC-SBOM-MIG-1: First run after upgrade migrates flat SBOMs exactly once
    Given the workspace is initialized with test data from "e2e/uc-sbom-mig-1"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the environment instance "test-cluster/test-env" matches the reference "ref-uc-sbom"
    And the pipeline log contains "Removing legacy SBOM file:"
    And no flat SBOM files remain at the top of the sboms directory
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And no flat SBOM files remain at the top of the sboms directory
    And no SBOM files were removed
