Feature: SBOM Storage Migration

  Scenario: UC-SBOM-MIG-1: First run after upgrade
    Given the Environment Workspace is created from "uc_sbom_mig_1_base"
    And legacy flat SBOM files are present in the sboms directory
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the orchestrator completes successfully
    And no flat SBOM files remain in the root sboms directory
    And SBOM files are relocated to per-application subdirectories
