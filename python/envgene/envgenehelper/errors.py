"""
EnvGene Error Classes

This module defines custom error classes for EnvGene pipelines to ensure consistent
error handling and reporting across the codebase.
"""

class EnvGeneError(Exception):
    """Base class for all EnvGene exceptions."""

    def __init__(self, message, error_code=None):
        """
        Initialize the exception with a message and optional error code.

        Args:
            message (str): Human-readable error message
            error_code (str, optional): Error code following the format ENVGENE-XXXX
        """
        self.error_code = error_code
        if error_code:
            message = f"[{error_code}] {message}"
        super().__init__(message)


class ValueError(EnvGeneError):
    """
    Raised when a function receives an argument with the right type but inappropriate value.
    Examples:
        - Invalid input format
        - Value out of allowed range
        - Invalid configuration value
    """
    pass


class TypeError(EnvGeneError):
    """
    Raised when a function receives an argument of the wrong type.
    Examples:
        - Expected string but received integer
        - Expected dictionary but received list
    """
    pass


class ReferenceError(EnvGeneError):
    """
    Raised when a required resource is missing or cannot be accessed.
    Examples:
        - Required file not found
        - Required configuration not available
        - Required dependency missing
    """
    pass


class EnvironmentError(EnvGeneError):
    """
    Raised when an environment-related issue prevents normal operation.
    Examples:
        - Missing environment variables
        - Insufficient permissions
        - Incompatible environment configuration
    """
    pass


class RuntimeError(EnvGeneError):
    """
    Raised when an error occurs during execution that doesn't fall into other categories.
    Examples:
        - Unexpected state in the application
        - Internal error in processing logic
        - Unhandled edge case
    """
    pass


class ValidationError(EnvGeneError):
    """
    Raised when input validation fails.
    Examples:
        - Schema validation failure
        - Data integrity check failure
        - Business rule validation failure
    """
    pass


class IntegrationError(EnvGeneError):
    """
    Raised when an error occurs during integration with external systems.
    Examples:
        - API call failure
        - External service unavailable
        - Authentication failure with external service
    """
    pass
