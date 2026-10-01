"""Domain errors for migration-cli."""


class MigrationCliError(Exception):
    """Base error for migration-cli commands."""


class ValidationError(MigrationCliError):
    """Input validation failed."""


class MatchError(MigrationCliError):
    """Credential value could not be matched."""
