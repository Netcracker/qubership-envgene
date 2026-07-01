Feature: Credential Files Encryption Using Git Commit Hook - TC-004
  As an EnvGene developer
  I want to ensure credential files are automatically encrypted during git commit
  So that sensitive information is not stored in plaintext in the repository

  Scenario: TC-004-001: Encryption Enabled with Supported Fields
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "Fernet" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists
    And a valid Fernet secret key is available in the git directory
    When a git commit is executed
    Then the commit completes successfully
    And the credential file is encrypted with "Fernet"

  @xfail
  Scenario: TC-004-002: Encryption Skipped When Disabled
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt disabled
    And a valid credential file "configuration/credentials/credentials.yml" exists
    When a git commit is executed
    Then the commit completes successfully
    And the credential file remains unencrypted

  Scenario: TC-004-003: Secret Key Mandatory for Fernet
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "Fernet" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists
    And the Fernet secret key is missing
    When a git commit is executed
    Then the commit fails with message "SECRET_KEY is required for Fernet encryption"
    And the credential file remains unencrypted

  Scenario: TC-004-004: Successful Encryption Using Fernet
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "Fernet" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists
    And a valid Fernet secret key is available in the git directory
    When a git commit is executed
    Then the commit completes successfully
    And the credential file is encrypted with "Fernet"

  Scenario: TC-004-005: Skip Encryption if File Already Encrypted Using Fernet
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "Fernet" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists and is already encrypted with "Fernet"
    And a valid Fernet secret key is available in the git directory
    When a git commit is executed
    Then the commit completes successfully
    And the commit log contains "File already encrypted; encryption skipped"

  Scenario: TC-004-006: age_key Mandatory for SOPS
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "SOPS" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists
    And the SOPS age key is missing
    When a git commit is executed
    Then the commit fails with message "ENVGENE_AGE_PUBLIC_KEY is required for SOPS encryption"
    And the credential file remains unencrypted

  Scenario: TC-004-007: Successful Encryption Using SOPS
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "SOPS" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists
    And a valid SOPS age key is available in the git directory
    When a git commit is executed
    Then the commit completes successfully
    And the credential file is encrypted with "SOPS"

  Scenario: TC-004-008: Skip Encryption if File Already Encrypted Using SOPS
    Given a local git repository is initialized in the workspace
    And the configuration file "configuration/config.yml" has crypt enabled with "SOPS" backend
    And a valid credential file "configuration/credentials/credentials.yml" exists and is already encrypted with "SOPS"
    And a valid SOPS age key is available in the git directory
    When a git commit is executed
    Then the commit completes successfully
    And the commit log contains "File already encrypted; encryption skipped"
