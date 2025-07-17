# EnvGene Error Catalog

This document catalogs all errors and validations performed by EnvGene components, providing a reference for troubleshooting and understanding the error handling process.

## Index

- [Error Structure](#error-structure)
- [Error Code Format](#error-code-format)
- [Error Codes](#error-codes)
  - [Credential Validation Errors](#credential-validation-errors)
    - [ENVGENE-4001: Missing or Undefined Credential](#envgene-4001-missing-or-undefined-credential)
- [Future Error Codes](#future-error-codes)

## Error Structure

Each error is documented with the following information:
- **ID**: Unique identifier for the error that appears in logs
- **Component**: Which EnvGene component generates the error
- **When**: At what stage of processing the error may occur
- **What**: Description of what triggers the error
- **Error**: Example error message that appears when the error occurs
- **Resolution**: Steps to resolve the error

## Error Code Format

EnvGene error codes follow the format: `ENVGENE-XXXX` where:

- `ENVGENE` - Component identifier (always ENVGENE for our component)
- `XXXX` - Error code number (padded with zeros on the left)

Error code ranges:

| Range      | Type          | Description                                      |
|------------|---------------|--------------------------------------------------|
| 0001-1499  | Business      | Errors in business logic                         |
| 1500-1999  | Technical     | Errors in technical logic                        |
| 3000-3999  | Inconsistency | Errors related to data/state inconsistency       |
| 4000-6999  | Validation    | Validation errors for input parameters           |
| 7000-7999  | Integration   | Integration errors with external systems         |
| 8000-8999  | Data source   | Errors related to data sources (DB, files, etc.) |

## Error Codes

### Credential Validation Errors

#### ENVGENE-4001: Missing Credential

- **ID**: ENVGENE-4001
- **Component**: Calculator CLI
- **When**: After credential processing but before finalizing the effective set generation
- **What**: Validates that no credential value equals "envgeneNullValue", which indicates a missing or undefined credential
- **Error**:
  ```text
  [ENVGENE-4001] Error: Missing credential detected
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

### Validation Errors (4000-6999)
- ENVGENE-4002: Invalid configuration format
- ENVGENE-4003: Missing required configuration field

### Integration Errors (7000-7999)
- ENVGENE-7001: External API connection failure
- ENVGENE-7002: External service timeout

### Data Source Errors (8000-8999)
- ENVGENE-8001: File not found
- ENVGENE-8002: Permission denied
