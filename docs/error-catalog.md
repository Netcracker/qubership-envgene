# EnvGene Error Catalog

This document catalogs all errors and validations performed by EnvGene components, providing a reference for troubleshooting and understanding the error handling process.

- [EnvGene Error Catalog](#envgene-error-catalog)
  - [Error Structure](#error-structure)
  - [Error Code Format](#error-code-format)
  - [Error Codes](#error-codes)
    - [Credential Validation Errors](#credential-validation-errors)
      - [ENVGENE-4001: Missing Credential](#envgene-4001-missing-credential)
      - [ENVGENE-4002: Invalid configuration format](#envgene-4002-invalid-configuration-format)
      - [ENVGENE-4003: Missing required configuration field](#envgene-4003-missing-required-configuration-field)
      - [ENVGENE-4004: Termination condition encountered](#envgene-4004-termination-condition-encountered)
    - [Data Validation Errors](#data-validation-errors)
      - [ENVGENE-3002: Invalid Data Type](#envgene-3002-invalid-data-type)
    - [File and Integration Errors](#file-and-integration-errors)
      - [ENVGENE-8001: File not found](#envgene-8001-file-not-found)
      - [ENVGENE-8003: Invalid Path](#envgene-8003-invalid-path)
  - [Future Error Codes](#future-error-codes)
    - [Validation Errors (4000-6999)](#validation-errors-4000-6999)
    - [Integration Errors (7000-7999)](#integration-errors-7000-7999)
    - [Data Source Errors (8000-8999)](#data-source-errors-8000-8999)

## Error Structure

Each error is documented with the following information:

- **ID**: Unique identifier for the error that appears in logs
- - **Component**: Which EnvGene component generates the error
- - **When**: At what stage of processing the error may occur
- - **What**: Description of what triggers the error
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

#### ENVGENE-4002: Invalid configuration format

- **ID**: ENVGENE-4002
- **Component**: Envgene
- **When**:During validation of input payload, environment files, or context resolution in cred rotation job
- **What**: Raised due to json/yaml parsing errors, incorrect input values, unsupported encryption types or encryption/decryption failure
- **Error**:

```text
[ENVGENE-4002] Error: Invalid configuration format
Failed to parse JSON content in CRED_ROTATION_PAYLOAD. Error:
Extra data: line 2 column 18 (char 18)

This indicates invalid json content in payload. Please check the payload.

[ENVGENE-4002] Invalid configuration format: Failed to parse JSON content in CRED_ROTATION_PAYLOAD. Error:
 Extra data: line 2 column 18.

 This indicates input payload provided is in wrong format.It should be given as json string Please check the payload.

 [ENVGENE-4002] Invalid configuration format: Current encryption type is Fernet. Only SOPS is supported for CRED_ROTATION_PAYLOAD and for encrypting/decrypting credential files.Please refer to the configuration at CI_PROJECT_DIR/configurations/config.yaml.

  This indicates that encryption type given in config.yaml is 'Fernet'. Since SOPS is only supported, Only SOPS can be used in cred rotation job to decrypt and encrypt cred rotation payload and credential files.

  [ENVGENE-4002] Invalid configuration format: Invalid configuration format.Failed to Encrypt the credential file {file} due to {error}

  This indicates that Something went wrong while trying to encrypt the credential files back after file updation

  [ENVGENE-4002] Invalid configuration format: Invalid configuration format.Failed to Decrypt the credential file {file} due to {error}

  This indicates that Something went wrong while trying to decrypt the credential files. Please check if the file was encrypted with Fernet and config has it as SOPS.

  [ENVGENE-4002] Invalid configuration format: Invalid configuration format.Failed to read the credential file {file}

  This indicates that Something went wrong while trying to read the credential files. Please check if the syntax of file is correct
```

- **Resolution**:

1. Verify YAML or JSON syntax .
2. Ensure all required input fields are present and correctly formatted.
3. Check for unsupported credential field in cred rotation payload.
4. Ensure correct encryption tool and configuration (SOPS only supported).

#### ENVGENE-4003: Missing required configuration field

- **ID**: ENVGENE-4003
- **Component**: Envgene
- **When**: During validation of input payload, environment files, or context resolution in cred rotation job
- **What**: Raised when expected fields like target parameter, context specified in payload or credential macro for target parameter are missing in the credential, namespace or application files
- **Error**:

```text
[ENVGENE-4003] Error: Missing required configuration field
Credential macro not found in target file <file> in the context <context>.

Points to absence of credential pattern eg: "${creds.get(<credid>).username} .Please verify the parameter key in target file.

[ENVGENE-4003] Missing required configuration field: Parameter key <param> not found in environment instance for the given context under specified namespace or application in cred rotation payload.

Points to absence of target parameter given in cred rotation payload. Recheck if the target parameter is actually present in file.

[ENVGENE-4003] Missing required configuration field: Context deployment not found in <file> for key <param>. Please check the context for the parameter.

This indicates that context value given in payload is not present in target file. Recheck the files  if this context is available.
```

- **Resolution**:

1. Ensure required fields are defined in YAML files in the project directory
2. Ensure target parameter keys have credential macros in the specified target file.
3. Check input payload for valid structure and value

#### ENVGENE-4004: Termination condition encountered

- **ID**: ENVGENE-4004
- **Component**: Envgene
- **When**: After evaluating credential payloads or identifying affected parameters in cred rotation job
- **What**: Raised when no affected parameters are found or force flag is not enabled during updates
- **Error**:

```text
[ENVGENE-4004] Error: Termination condition encountered
No affected parameters found for the given CRED_ROTATION_PAYLOAD in the current environment instance. Hence Terminating the job.

The error denotes that there are parameters that had the same cred id as target parameter. Please check if parameter key and other details are correct in payload.

[ENVGENE-4004] Invalid state for job completion: Affected parameters have been identified. You can find the list of affected parameters in the artifact of this job, in the file <artifcat location>. Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled. Terminating the job.

This error denotes that CRED_ROTATION_FORCE is set as False by user and hence no file updates are done and job will be terminated.

```

- **Resolution**:

1. Ensure credentials are mapped and in use
2. Use the force flag (CRED\_ROTATION\_FORCE) if needed
3. Recheck cred rotation payload list

### Data Validation Errors

#### ENVGENE-3002: Invalid Data Type

- **ID**: ENVGENE-3002
- **Component**: Envgene
- **When**: While processing target key in YAML files for parameters in cred rotation job
- **What**: Raised when a value is not of expected type (e.g., string ) for target parameter
- **Error**:

```text
[ENVGENE-3002] Error: Invalid Data Type: Expected string at <parameter>, got <class <type>>. Incorrect value for the targt parameter.

Points to incorrect data type instead of credential macro being present. Please check if target parameter mentioned in payload is correct.
```

- **Resolution**:

1. Check the value of target parameter if its a valid credential expression

### File and Integration Errors

#### ENVGENE-8001: File not found

- **ID**: ENVGENE-8001
- **Component**: Envgene
- **When**: While processing target or affected parameters in cred rotation job
- **What**: Raised when the file for a parameter cannot be located
- **Error**:

```text
[ENVGENE-8001] Error: File not found
Failed to find namespace YAML file in the directory <directory>. Please check if the namespace file is present.

This indicate that the namespace file is not present in namespace directory . Please check if file is present.
```

- **Resolution**:

1. Check folder structure: project_dir/environments/cluster/env
2. Verify existence of namespace or application YAML

#### ENVGENE-8003: Invalid Path

- **ID**: ENVGENE-8003
- **Component**: Envgene
- **When**: During lookup of shared credential files in cred rotation job
- **What**: Raised if expected directory hierarchy is broken
- **Error**:

```text
[ENVGENE-8003] Error: Invalid path hierarchy
<folder> is not a parent of <folder>. Something wrong with the folder structure in environment instance. Expected structure: project_dir/environments/cluster/env.
```

- **Resolution**:

1. Ensure environment folder hierarchy follows standard layout

---

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
