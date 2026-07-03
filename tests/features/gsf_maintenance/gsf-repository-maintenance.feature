Feature: GSF Repository Maintenance

  Scenario: UC-GSF-TMP-1: Initialize Template Repository via GSF
    Given a new Template Repository exists without EnvGene-specific files
    When GSF install is run with a template package image and initialization parameters
    Then the Template Repository is initialized with required files
    And group_id and artifact_id are set in build_vars.sh
    And the repository matches the reference structure

  Scenario: UC-GSF-TMP-2: Upgrade Template Repository via GSF
    Given a Template Repository exists with a previous EnvGene template package version
    When GSF install is run with a target template package image
    Then the Template Repository is upgraded to the target version
    And restricted files are preserved according to policy

  Scenario: UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0)
    Given a legacy Template Repository exists with a previous EnvGene template package version before 2.85.0
    When GSF install is run with a target template package image on the legacy repository
    Then the legacy repository is migrated to the current package format
    And legacy formats are normalized

  Scenario: UC-GSF-TMP-3: Downgrade Template Repository via GSF
    Given a Template Repository exists with a later EnvGene template package version
    When GSF install is run with an older template package image
    Then the Template Repository is switched to the older version
    And files from the later version are removed

  Scenario: UC-GSF-INST-1: Initialize Instance Repository via GSF
    Given a new Instance Repository exists without EnvGene-specific files
    When GSF install is run with an instance package image
    Then the Instance Repository is initialized with required files
    And the repository matches the reference instance structure

  Scenario: UC-GSF-INST-2: Upgrade Instance Repository via GSF
    Given an Instance Repository exists with a previous EnvGene instance package version
    When GSF install is run with a target instance package image
    Then the Instance Repository is upgraded to the target version
    And pipeline_vars are preserved according to policy

  Scenario: UC-GSF-INST-3: Downgrade Instance Repository via GSF
    Given an Instance Repository exists with a later EnvGene instance package version
    When GSF install is run with an older instance package image
    Then the Instance Repository is switched to the older version
    And files from the later instance version are removed
