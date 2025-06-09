# EnvGene Error Handling Best Practices Guide

## Table of Contents
1. [Error Handling Principles](#error-handling-principles)
2. [When and Where to Catch Errors](#when-and-where-to-catch-errors)
3. [Error Classification](#error-classification)
4. [Writing User-Friendly Error Messages](#writing-user-friendly-error-messages)
5. [Error Code Format](#error-code-format)
6. [Error Message Propagation](#error-message-propagation)
7. [Examples](#examples)
8. [Checklist](#checklist)
9. [Error Handling PR Template Requirements](#error-handling-pr-template-requirements)
10. [Testing Error Scenarios](#testing-error-scenarios)

> **Important Resources:**
> - [Error Catalog](./error-catalog.md): Complete catalog of all error codes
> - [PR Template](../.github/PULL_REQUEST_TEMPLATE/pull_request_template.md): Standard PR template with error handling requirements

## Error Handling Principles

This guide establishes best practices for error handling in EnvGene pipelines to ensure that error messages are:

1. **User-friendly**: Understandable by non-technical users
2. **Actionable**: Provide clear guidance on how to resolve the issue
3. **Specific**: Include relevant context and details
4. **Consistent**: Follow established patterns across the codebase
5. **Fail Fast, Fail Loud**: Detect and report errors as soon as they occur
6. **Log Appropriately**: Ensure errors are logged with sufficient context for debugging

## When and Where to Catch Errors

### Catch Errors At:
1. **External Boundaries**:
   - File I/O operations
   - Network requests
   - External command execution
   - Data validation points

2. **Domain Logic Entry Points**:
   - Public API methods
   - Command-line interface handlers
   - Event handlers

### Don't Catch:
1. **Programming Errors**: Let these bubble up to reveal bugs in development.
2. **Errors You Can't Handle**: If you can't meaningfully handle an error, let it propagate.

## Error Classification

EnvGene provides a set of custom error classes in [`python/envgene/envgenehelper/errors.py`](../python/envgene/envgenehelper/errors.py) that should be used for consistent error handling across the codebase:

| Error Type           | When to Use                      | Example                              |
|----------------------|----------------------------------|--------------------------------------|
| `ValueError`         | Invalid parameter values         | Invalid input format                 |
| `TypeError`          | Incorrect parameter types        | Wrong type passed to function        |
| `ReferenceError`     | Missing required resources       | Required file not found              |
| `EnvironmentError`   | Environment-related issues       | Missing environment variables        |
| `RuntimeError`       | Other runtime errors             | Unexpected state in the application  |
| `ValidationError`    | Input validation failures        | Schema validation failure            |
| `IntegrationError`   | External system integration      | API call failure                     |

All these error classes inherit from the base `EnvGeneError` class, which supports error codes and formatted error messages.


## Writing User-Friendly Error Messages

### DO:
1. **Be Clear and Concise**:
   ```python
   # Good
   raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
   
   # Bad
   raise ValueError("Format error")
   ```

2. **Be Specific**:
   ```python
   # Good
   raise ReferenceError(f"Required configuration file not found: {config_path}")
   ```

3. **Provide Context**:
   ```python
   raise EnvironmentError(
       "Missing required environment variable 'API_KEY'. "
       "Please set it in your environment or .env file."
   )
   ```

4. **Use Error Codes** (see [Error Catalog](./error-catalog.md) for all codes):
   ```python
   # ENVGENE-0001: Module initialization failed
   raise RuntimeError("[ENVGENE-0001] Failed to initialize module. Check configuration.")
   ```

### DON'T:
1. Expose sensitive information (passwords, tokens, etc.)
2. Use technical jargon without explanation
3. Be vague or generic

## Error Code Format

EnvGene error codes must follow the format: `ENVGENE-XXXX` where (see [Error Catalog](./error-catalog.md) for the complete list of error codes):

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

Example usage in code:

```python
from envgenehelper.errors import ValidationError

def validate_config(config):
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary", error_code="ENVGENE-4001")
    
    if 'api_key' not in config:
        raise ValidationError("Missing required configuration: 'api_key'", error_code="ENVGENE-4002")
```

## Error Message Propagation

It's critical to ensure that user-friendly error messages are correctly propagated to the pipeline output and not swallowed by higher-level handlers. Follow these guidelines:

1. **Preserve Original Error Context**:
   ```python
   try:
       # Operation that might fail
   except EnvGeneError as e:
       # Add context but preserve the original error
       raise RuntimeError(f"Pipeline execution failed: {str(e)}") from e
   ```

2. **Bubble Up Important Errors**:
   - Don't catch exceptions unless you can handle them meaningfully
   - When re-raising, use the `from` syntax to preserve the traceback
   - Ensure top-level handlers display the full error message to users

3. **Pipeline Output Handling**:
   - All pipeline components must report errors to a central error handler
   - The central error handler must format errors consistently
   - User-facing interfaces must display the formatted error message

## Examples

### Good Error Message

```python
from envgenehelper.errors import ValidationError, TypeError

def validate_credentials(credentials):
    if not isinstance(credentials, dict):
        raise TypeError(
            "Credentials must be a dictionary. "
            f"Got {type(credentials).__name__} instead.",
            error_code="ENVGENE-4001"
        )
    
    required_fields = ['username', 'password', 'domain']
    missing = [field for field in required_fields if field not in credentials]
    
    if missing:
        raise ValidationError(
            f"Missing required credential fields: {', '.join(missing)}. "
            "Please provide all required credentials.",
            error_code="ENVGENE-4002"
        )
```

### Good Error Propagation Pattern

```python
from envgenehelper.errors import IntegrationError

try:
    result = api_client.fetch_data()
except ApiClientError as e:
    # Convert to our error type with proper code
    raise IntegrationError(
        f"Failed to fetch data from API: {str(e)}",
        error_code="ENVGENE-7001"
    ) from e
```

## Checklist

Use this checklist to ensure your error handling follows best practices:

- [ ] Errors are caught at appropriate boundaries
- [ ] Error messages are user-friendly and actionable
- [ ] Error codes follow the `ENVGENE-XXXX` format
- [ ] Custom error classes from `envgenehelper.errors` are used
- [ ] Sensitive information is not exposed in error messages
- [ ] Errors are properly propagated to pipeline output
- [ ] Error messages are properly cataloged in error-catalog.md

## Error Handling PR Template Requirements

All pull requests that introduce new code or modify existing code **MUST** include the error handling checklist in the PR description. This is automatically included in the [standard PR template](../.github/PULL_REQUEST_TEMPLATE/pull_request_template.md) and is a mandatory requirement to ensure consistent error handling across the codebase.

```markdown
## Error Handling Checklist

### Error Implementation
- [ ] Custom error classes from `envgenehelper.errors` are used for all error cases
- [ ] All error messages include error codes following the ENVGENE-XXXX format
- [ ] Error messages are user-friendly and provide clear guidance on how to resolve the issue
- [ ] No sensitive information is exposed in error messages
- [ ] Errors are properly propagated to pipeline output and not swallowed by handlers

### Error Documentation
- [ ] All new error codes are documented in error-catalog.md
- [ ] Documentation includes all required sections (ID, Component, When, What, Error, Resolution)
- [ ] Error code ranges are used appropriately (business: 0001-1499, validation: 4000-6999, etc.)

### Error Testing
- [ ] Tests are included for error scenarios
- [ ] Error messages are verified to be displayed correctly in the pipeline output
```

Reviewers **MUST** verify that all items in the checklist are properly addressed before approving the PR.

## Testing Error Scenarios

1. **Unit Tests**: Test error conditions in isolation
   ```python
   def test_invalid_credentials():
       with pytest.raises(ValueError) as excinfo:
           validate_credentials({})
       assert "Missing required credential fields" in str(excinfo.value)
   ```

2. **Error Simulation**: Test how the system handles:
   - Missing files
   - Network failures
   - Invalid inputs
   - Permission issues

## Error Code Requirements

### Mandatory Error Codes

Every error message in EnvGene MUST include an error code that follows the naming convention below. This is a strict requirement to ensure consistent error handling and documentation. All error codes must be documented in the [Error Catalog](./error-catalog.md).

### Error Code Naming Convention

All error codes in EnvGene must follow this consistent pattern:

```
ENVGENE-XXXX
```

Where:
- `ENVGENE`: Component identifier (always ENVGENE for our component)
- `XXXX`: Error code number (padded with zeros on the left)

This format aligns with the standard error code format used by other components in the system.

### Error Code Documentation Requirements

1. **Mandatory Documentation**:
   - Every error code MUST be documented in the `error-catalog.md` file
   - The documentation MUST include all required sections (ID, Component, When, What, Error, Resolution)
   - Example:
     ```markdown
     #### ENVGENE-4001: Invalid Configuration
     
     - **ID**: ENVGENE-4001
     - **Component**: Configuration Validator
     - **When**: During configuration validation
     - **What**: Required configuration is missing or invalid
     - **Error**: 
       ```
       [ENVGENE-4001] Invalid configuration. Missing required field: {field_name}
       ```
     - **Resolution**:
       1. Check the configuration file
       2. Ensure all required fields are present and valid
       3. Refer to the documentation for configuration requirements
     ```

2. **Code Implementation**:
   - Use the EnvGeneError classes from `envgenehelper.errors`
   - Include the error code when raising exceptions
   - Example:
     ```python
     from envgenehelper.errors import ValidationError
     raise ValidationError(f"Invalid configuration. Missing required field: {field_name}", error_code="ENVGENE-4001")
     ```

3. **Maintenance Guidelines**:
   - Use the appropriate error code range based on the error type
   - When adding a new error code, use the next available number in the sequence
   - Update the error catalog before merging any code that introduces new error codes

4. **Code Review Checklist**

#### Error Coverage
- [ ] All external system calls (file I/O, network, subprocesses) have proper error handling
- [ ] All input validations have corresponding error cases
- [ ] All third-party library calls that can raise exceptions are wrapped in try-catch blocks
- [ ] All error cases from the function's documentation are handled
- [ ] Edge cases (null/empty inputs, boundary values) have appropriate error handling
- [ ] Timeout scenarios are handled for long-running operations
- [ ] Resource cleanup (files, connections, etc.) happens in finally blocks or using context managers

#### Error Implementation
- [ ] Custom error classes from [`envgenehelper.errors`](../python/envgene/envgenehelper/errors.py) are used
- [ ] All error messages include error codes
- [ ] Error codes follow the naming convention (ENVGENE-XXXX)
- [ ] Error messages are clear, actionable, and user-friendly
- [ ] Sensitive information is not exposed in error messages
- [ ] Error messages include all necessary context for debugging
- [ ] Errors are properly propagated to pipeline output

#### Documentation
- [ ] All error codes are documented in the [error catalog](./error-catalog.md)
- [ ] Documentation includes all required sections (ID, Component, When, What, Error, Resolution)
- [ ] Error documentation includes examples of both error message and resolution steps

## Error Catalog Maintenance

The error catalog (`error-catalog.md`) is the single source of truth for all error codes in EnvGene. It must be kept up-to-date and accurate.

### Catalog Structure

1. **Error Code Index**:
   - Grouped by component or category
   - Links to detailed error documentation

2. **Error Documentation**:
   Each error MUST be documented with the following sections:
   - **ID**: The full error code (e.g., ERR-MOD-VAL-001)
   - **Component**: Which part of the system generates this error
   - **When**: Under what conditions this error occurs
   - **What**: Description of the error condition
   - **Error**: The exact error message format (including the error code)
   - **Resolution**: Step-by-step guide to resolve the issue

### Maintenance Process

1. **Adding a New Error**:
   - Add the error code to the appropriate section in the catalog
   - Include all required documentation
   - Update any related documentation or references

2. **Updating an Error**:
   - Update the error message in code and documentation simultaneously
   - If the error code changes, add a deprecation notice
   - Update any affected tests

3. **Deprecating an Error**:
   - Mark as deprecated in the catalog
   - Add information about the replacement error code if applicable
   - Keep the documentation for at least one release cycle before removal

## Review and Update

This guide should be reviewed and updated:
- When new error patterns are identified
- When new components are added
- When existing error handling is found to be insufficient

---

*This guide should be treated as a living document and updated based on team feedback and evolving best practices.*
