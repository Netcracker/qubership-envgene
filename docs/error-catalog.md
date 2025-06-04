# EnvGene Error Catalog

This document catalogs all errors and validations performed by EnvGene components, providing a reference for troubleshooting and understanding the error handling process.

## Index

- [Error Structure](#error-structure)
- [Error Codes](#error-codes)
  - [Credential Validation Errors](#credential-validation-errors)
    - [ERR-CRED-VAL-001: Missing or Undefined Credential](#err-cred-val-001-missing-or-undefined-credential)
- [Future Error Codes](#future-error-codes)

## Error Structure

Each error is documented with the following information:
- **ID**: Unique identifier for the error that appears in logs
- **Component**: Which EnvGene component generates the error
- **When**: At what stage of processing the error may occur
- **What**: Description of what triggers the error
- **Error**: Example error message that appears when the error occurs
- **Resolution**: Steps to resolve the error

## Error Codes

### Credential Validation Errors

#### ERR-CRED-VAL-001: Missing Credential

- **ID**: ERR-CRED-VAL-001
- **Component**: Calculator CLI
- **When**: After credential processing but before finalizing the effective set generation
- **What**: Validates that no credential value equals "envgeneNullValue", which indicates a missing or undefined credential
- **Error**:
  ```text
  [ERR-CRED-VAL-001] Error: Missing or undefined credential detected
  Environment Credentials file path: <path-to-credentials-file>
  Credential ID: <credential-key>
  Credential Value: "envgeneNullValue"

  This indicates that a required credential is missing or undefined. Please define this credential in your environment configuration.
  ```
- **Resolution**:
  1. Identify the missing credential from the error message
  2. Define the credential in the appropriate environment configuration file
  3. Re-run the effective set generation

## Future Error Codes

This section lists planned error codes that are not yet implemented:
- TBD
