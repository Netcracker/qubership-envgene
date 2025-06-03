# EnvGene Error Handling Best Practices Guide

## Table of Contents
1. [Overview](#overview)
2. [Error Handling Principles](#error-handling-principles)
3. [When and Where to Catch Errors](#when-and-where-to-catch-errors)
4. [Error Classification](#error-classification)
5. [Writing User-Friendly Error Messages](#writing-user-friendly-error-messages)
6. [Error Handling Patterns](#error-handling-patterns)
7. [Logging Best Practices](#logging-best-practices)
8. [Examples](#examples)
9. [Checklist](#checklist)
10. [Testing Error Scenarios](#testing-error-scenarios)

## Overview

This guide establishes best practices for error handling in EnvGene pipelines to ensure that error messages are:
- **User-friendly**: Understandable by non-technical users
- **Actionable**: Provide clear guidance on how to resolve the issue
- **Specific**: Include relevant context and details
- **Consistent**: Follow established patterns across the codebase

## Error Handling Principles

1. **Fail Fast, Fail Loud**: Detect and report errors as soon as they occur.
2. **Be Specific**: Provide detailed error messages that explain what went wrong and why.
3. **Be Helpful**: Include guidance on how to fix the issue.
4. **Be Consistent**: Follow the established error handling patterns.
5. **Log Appropriately**: Ensure errors are logged with sufficient context for debugging.

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

| Error Type           | When to Use                      | Example                              |
|----------------------|----------------------------------|--------------------------------------|
| `ValueError`         | Invalid parameter values         | Invalid input format                 |
| `TypeError`          | Incorrect parameter types       | Wrong type passed to function        |
| `ReferenceError`     | Missing required resources      | Required file not found             |
| `EnvironmentError`   | Environment-related issues      | Missing environment variables       |
| `RuntimeError`       | Other runtime errors            | Unexpected state in the application |
| `CustomError`        | Domain-specific error cases     | See Error Catalog                   |


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

4. **Use Error Codes**:
   ```python
   # ERR-MOD-001: Module initialization failed
   raise RuntimeError("[ERR-MOD-VAL-001] Failed to initialize module. Check configuration.")
   ```

### DON'T:
1. Expose sensitive information (passwords, tokens, etc.)
2. Use technical jargon without explanation
3. Be vague or generic

## Error Handling Patterns

### 1. Input Validation

```python
def process_config(config):
    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")
    
    if 'api_key' not in config:
        raise ValueError("Missing required configuration: 'api_key'")
    
    # Process config...
```

### 2. Resource Handling

```python
def load_template(template_path):
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise ReferenceError(f"Template file not found: {template_path}")
    except IOError as e:
        raise RuntimeError(f"Error reading template file {template_path}: {str(e)}")
```

### 3. External Command Execution

```python
def run_external_command(cmd):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError("Failed to execute command. See logs for details.")
```

## Logging Best Practices

1. **Log Errors with Context**:
   ```python
   try:
       # Some operation
   except Exception as e:
       logger.error(
           "Failed to process configuration. "
           f"File: {config_file}, Error: {str(e)}",
           exc_info=True  # Include stack trace in logs
       )
       raise  # Re-raise with original traceback
   ```

2. **Use Appropriate Log Levels**:
   - `DEBUG`: Detailed information for debugging
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: Indication that something unexpected happened
   - `ERROR`: Serious problems that prevent normal execution
   - `CRITICAL`: Severe errors that cause premature termination

## Examples

### Good Error Message

```python
def validate_credentials(credentials):
    if not isinstance(credentials, dict):
        raise TypeError(
            "Credentials must be a dictionary. "
            f"Got {type(credentials).__name__} instead."
        )
    
    required_fields = ['username', 'password', 'domain']
    missing = [field for field in required_fields if field not in credentials]
    
    if missing:
        raise ValueError(
            f"Missing required credential fields: {', '.join(missing)}. "
            "Please provide all required credentials."
        )
```

### Good Logging Pattern

```python
try:
    result = some_operation()
except SomeSpecificError as e:
    logger.error(
        "Failed to complete operation. "
        f"Context: {context}, Error: {str(e)}",
        exc_info=True
    )
    raise RuntimeError("Operation failed. See logs for details.") from e
```

## Checklist

### Before Submitting Code:
- [ ] All error messages are clear and actionable
- [ ] Error messages include relevant context
- [ ] Sensitive information is not logged or exposed
- [ ] Error codes are used where appropriate
- [ ] Logs provide sufficient information for debugging
- [ ] All error scenarios are tested

### Error Message Review:
- [ ] Is the error message understandable by a non-technical user?
- [ ] Does it explain what went wrong?
- [ ] Does it suggest how to fix the issue?
- [ ] Is it specific enough to identify the problem?
- [ ] Is the error code included in the error message?

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

Every error message in EnvGene MUST include an error code that follows the naming convention below. This is a strict requirement to ensure consistent error handling and documentation.

### Error Code Naming Convention

All error codes in EnvGene must follow this consistent pattern:

```
ERR-<MODULE>-<TYPE>-<NUMBER>
```

Where:
- `ERR`: Prefix indicating this is an error code
- `<MODULE>`: 3-5 letter abbreviation of the module or component (e.g., `CRED` for Credentials, `TEMPL` for Template Rendering)
- `<TYPE>`: 3-5 letter abbreviation of the error type (e.g., `VAL` for Validation, `LOD` for Loading)
- `<NUMBER>`: 3-digit number (padded with leading zeros) unique within the module and type

### Examples:
- `ERR-CRED-VAL-001`: First validation error in the Credentials module
- `ERR-CONF-LOD-002`: Second configuration loading error

### Error Code Documentation Requirements

1. **Mandatory Documentation**:
   - Every error code MUST be documented in the `error-catalog.md` file
   - The documentation MUST include all required sections (ID, Component, When, What, Error, Resolution)
   - Example:
     ```markdown
     ### ERR-MOD-VAL-001: Invalid Module Configuration
     
     - **ID**: ERR-MOD-VAL-001
     - **Component**: Module Loader
     - **When**: During module initialization
     - **What**: Required module configuration is missing or invalid
     - **Error**: 
       ```
       [ERR-MOD-VAL-001] Invalid module configuration. Missing required field: {field_name}
       ```
     - **Resolution**:
       1. Check the module configuration file
       2. Ensure all required fields are present and valid
       3. Refer to the module documentation for configuration requirements
     ```

2. **Code Implementation**:
   - Always include the error code at the beginning of the error message
   - Use the format: `[ERROR-CODE] Error message details`
   - Example:
     ```python
     raise ValueError("[ERR-MOD-VAL-001] Invalid module configuration. Missing required field: {field_name}")
     ```

3. **Maintenance Guidelines**:
   - Keep module and type abbreviations consistent across the codebase
   - When adding a new error code, use the next available number in the sequence
   - If a module or type becomes too broad, consider splitting it into more specific categories
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
- [ ] All error messages include error codes
- [ ] Error codes follow the naming convention (ERR-MOD-TYPE-NNN)
- [ ] Error messages are clear, actionable, and user-friendly
- [ ] Sensitive information is not exposed in error messages
- [ ] Error messages include all necessary context for debugging
- [ ] Errors are logged with appropriate severity levels

#### Documentation
- [ ] All error codes are documented in the error catalog
- [ ] Documentation includes all required sections (ID, Component, When, What, Error, Resolution)
- [ ] Error documentation includes examples of both error message and resolution steps
- [ ] Related errors are cross-referenced in the documentation

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
