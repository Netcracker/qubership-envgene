from __future__ import annotations

from .model import Finding

RULE_ORDER = (
    "PLACE-1", "PLACE-2", "PLACE-3", "PLACE-4", "PLACE-6", "PLACE-7", "PLACE-8", "PLACE-9", "PLACE-10",
    "SEC-1", "SEC-3", "SEC-4", "SEC-5", "INT-2", "INT-3", "INT-4", "NAME-1", "NAME-2", "NAME-3", "NAME-4",
)


def _location_lines(finding: Finding) -> str:
    return "\n".join(
        f"{item.path}:{item.line}:{item.column}" for item in finding.file_locations()
    )


def _block(rule: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{rule}\nNo findings"
    chunks = [
        f"{_location_lines(finding)}\n{finding.severity.value}\n{finding.message}\n{finding.hint}"
        for finding in findings
    ]
    return f"{rule}\n" + "\n\n".join(chunks)


def render(findings: list[Finding], *, disabled_rules: tuple[str, ...] = ()) -> str:
    by_rule: dict[str, list[Finding]] = {rule: [] for rule in RULE_ORDER}
    for item in findings:
        if item.rule not in disabled_rules:
            by_rule.setdefault(item.rule, []).append(item)
    return "\n\n".join(
        f"{rule}\nDisabled" if rule in disabled_rules else _block(rule, items)
        for rule, items in by_rule.items()
    ) + "\n"
