# EnvGen Validation Catalog

This document catalogs all validations performed by EnvGen components, providing a reference for troubleshooting and understanding the validation process.

## Index

- [Validation Structure](#validation-structure)
- [Validations](#validations)
  - [Credential Validations](#credential-validations)
    - [VAL-CRED-001: Credential Null Value Validation](#val-cred-001-credential-null-value-validation)
- [Future Validations](#future-validations)

## Validation Structure

Each validation is documented with the following information:
- **ID**: Unique identifier for the validation that appears in logs
- **Component**: Which EnvGen component performs the validation
- **When**: At what stage of processing the validation occurs
- **What**: Description of what is being validated
- **Error**: Example error message that appears when validation fails
- **Resolution**: Steps to resolve the validation error

## Validations

### Credential Validations

#### VAL-CRED-001: Credential Null Value Validation

- **ID**: VAL-CRED-001
- **Component**: Calculator CLI
- **When**: After credential processing but before finalizing the effective set generation
- **What**: Validates that no credential value equals "envgeneNullValue", which indicates a missing or undefined credential
- **Error**:
  ```text
  [CRED-001] Error: Invalid credential value detected
  File: <path-to-credentials-file>
  Credential: <credential-key>
  Value: "envgeneNullValue"

  This indicates that a required credential is missing or undefined. Please define this credential in your environment configuration.
  ```
- **Resolution**:
  1. Identify the missing credential from the error message
  2. Define the credential in the appropriate environment configuration file
  3. Re-run the effective set generation

## Future Validations

This section lists planned validations that are not yet implemented:
- TBD
