"""Build-time rule switches. Edit these booleans before building the package."""

from .rulemeta import RULES

# True runs the rule. False skips it and marks it Disabled in CLI/HTML reports.
# Use Python booleans, not strings. Keep an entry for every implemented rule.
RULE_ENABLED: dict[str, bool] = {
    "PLACE-1": True,
    "PLACE-2": True,
    "PLACE-3": True,
    "PLACE-4": True,
    "PLACE-6": True,
    "PLACE-7": True,
    "PLACE-8": True,
    "PLACE-9": True,
    "PLACE-10": True,
    "SEC-1": True,
    "SEC-3": True,
    "SEC-4": True,
    "SEC-5": True,
    "INT-2": True,
    "INT-3": True,
    "INT-4": True,
    "NAME-1": False,
    "NAME-2": True,
    "NAME-3": False,
    "NAME-4": False,
}


class RuleConfigError(ValueError):
    """The source configuration does not match the implemented rules."""


def disabled_rules() -> tuple[str, ...]:
    if set(RULE_ENABLED) != set(RULES):
        raise RuleConfigError(
            "Invalid rule configuration: rule_config.py must contain exactly "
            "one flag for every implemented rule."
        )
    if any(type(value) is not bool for value in RULE_ENABLED.values()):
        raise RuleConfigError(
            "Invalid rule configuration: rule_config.py flags must be True or False."
        )
    return tuple(rule for rule in RULES if not RULE_ENABLED[rule])
