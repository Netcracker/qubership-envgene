Feature: SBOM Retention
  As a system administrator
  I want to automatically clean up cached SBOM files
  So that I can manage the Instance Repository size

  Background:
    Given an Instance Repository exists with an "/sboms/" directory

  Scenario: UC-SBOM-1: SBOM retention disabled - no cleanup
    Given SBOM files exist in "/sboms/application-name/"
    And SBOM retention is disabled in "/configuration/config.yml"
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the effective set is generated successfully
    And no SBOM files are deleted
    And the pipeline log shows "SBOM retention policy is disabled"

  Scenario: UC-SBOM-2: All applications within per-application limit - no files deleted
    Given SBOM files exist for multiple applications with the following counts:
      | Application | Count |
      | app-a       | 7     |
      | app-b       | 4     |
      | app-c       | 10    |
    And SBOM retention is enabled with "keep_versions_per_app" set to 10
    And the total size of "/sboms/" is 200 MB, which is below the 1200 MB limit
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the effective set is generated successfully
    And no SBOM files are deleted
    And the pipeline log shows "SBOM retention policy is enabled for directory <path>/sboms"
    And the pipeline log shows "Directory size 200.00 MB"

  Scenario: UC-SBOM-3: Per-application retention keeps 10 most recent versions
    Given SBOM files exist for multiple applications with the following counts:
      | Application | Count |
      | app-a       | 15    |
      | app-b       | 12    |
      | app-c       | 8     |
    And SBOM retention is enabled with "keep_versions_per_app" set to 10
    And the total size of "/sboms/" is 500 MB, which is below the 1200 MB limit
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the effective set is generated successfully
    And 7 SBOM files are deleted in total
    And the following SBOM files remain per application:
      | Application | Kept | Deleted |
      | app-a       | 10   | 5       |
      | app-b       | 10   | 2       |
      | app-c       | 8    | 0       |
    And the pipeline log shows "Only 10 files will remain in <path>/sboms/app-a"
    And the pipeline log shows "Only 10 files will remain in <path>/sboms/app-b"

  Scenario: UC-SBOM-4: Per-application retention with custom version count
    Given 10 SBOM files exist for the application "postgres" under "/sboms/postgres/"
    And SBOM retention is enabled with "keep_versions_per_app" set to 3
    And the total size of "/sboms/" is 350 MB, which is below the 1200 MB limit
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the effective set is generated successfully
    And 7 SBOM files are deleted in total
    And the 3 most recently modified files are kept for "postgres"
    And the pipeline log shows "Only 3 files will remain in <path>/sboms/postgres"

  Scenario: UC-SBOM-5: Total /sboms/ size exceeds 1200 MB - keeps newest per application
    Given SBOM files exist for several applications with each containing 10 or fewer files
    And SBOM retention is enabled with "keep_versions_per_app" set to 10
    And the total size of "/sboms/" is 1300 MB, which is above the 1200 MB limit
    When the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true
    Then the effective set is generated successfully
    And only the single most recent SBOM file remains under each application directory
    And the pipeline log shows "Directory size 1300.00 MB"
    And the pipeline log shows "SBOM directory exceeds size limit, starting cleanup: <path>/sboms"
    And the pipeline log shows "Only 1 files will remain in <path>/sboms/<application-name>"
