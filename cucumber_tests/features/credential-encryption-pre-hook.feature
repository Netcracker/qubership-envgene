Feature: Credential Files Encryption Using Git Commit Hook
  As an EnvGene pipeline
  I want to encrypt credential files using Fernet or SOPS backends
  So that sensitive data is protected at rest

  # TC-004-001: crypt:true encrypts only supported fields
  Scenario: TC-004-001 Encryption enabled with supported fields using Fernet
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "Fernet"
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs
    Then the encrypt module completes successfully
    And the credentials file "credentials.yml" has encrypted sensitive fields
    And the credentials file "credentials.yml" field "type" is not encrypted

  # TC-004-002: crypt:false — no encryption
  Scenario: TC-004-002 Encryption skipped when disabled
    Given the config parameter "crypt" is set to false
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs
    Then the encrypt module completes successfully
    And the credentials file "credentials.yml" has no encrypted fields

  # TC-004-003: Fernet missing secret_key fails
  Scenario: TC-004-003 Secret key mandatory for Fernet encryption
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "Fernet"
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs without SECRET_KEY
    Then the encrypt module fails

  # TC-004-004: Fernet successful encryption
  Scenario: TC-004-004 Successful encryption using Fernet
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "Fernet"
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs
    Then the encrypt module completes successfully
    And the credentials file "credentials.yml" field "username" starts with "[encrypted:AES256_Fernet]"
    And the credentials file "credentials.yml" field "password" starts with "[encrypted:AES256_Fernet]"
    And the credentials file "credentials.yml" field "secret" starts with "[encrypted:AES256_Fernet]"
    And the credentials file "credentials.yml" is valid YAML

  # TC-004-005: Already Fernet-encrypted file is skipped
  Scenario: TC-004-005 Skip encryption if file already encrypted using Fernet
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "Fernet"
    And a credentials file "credentials.yml" is already encrypted with Fernet
    When the encrypt_cred_files module runs
    Then the encrypt module completes successfully
    And the credentials file "credentials.yml" has encrypted sensitive fields

  # TC-004-006: SOPS missing age key fails
  Scenario: TC-004-006 age_key mandatory for SOPS encryption
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "SOPS"
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs without ENVGENE_AGE_PUBLIC_KEY
    Then the encrypt module fails

  # TC-004-007: SOPS successful encryption
  @skip_win32
  Scenario: TC-004-007 Successful encryption using SOPS
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "SOPS"
    And a credentials file "credentials.yml" exists with plaintext values
    When the encrypt_cred_files module runs with SOPS mock
    Then the encrypt module completes successfully
    And the credentials file "credentials.yml" is valid YAML

  # TC-004-008: Already SOPS-encrypted file is skipped
  Scenario: TC-004-008 Skip encryption if file already encrypted using SOPS
    Given the config parameter "crypt" is set to true
    And the config parameter "crypt_backend" is set to "SOPS"
    And a credentials file "credentials.yml" is already encrypted with SOPS
    When the encrypt_cred_files module runs with SOPS mock
    Then the encrypt module completes successfully
