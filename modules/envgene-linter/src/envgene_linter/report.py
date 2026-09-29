from __future__ import annotations

import json
from pathlib import Path

from .model import Finding
from .rulemeta import RULES

JSON_REPORT_FILENAME = "envgene-linter-report.json"

RULE_ORDER = (
    "PLACE-1", "PLACE-2", "PLACE-3", "PLACE-4", "PLACE-6", "PLACE-7", "PLACE-8", "PLACE-9", "PLACE-10",
    "SEC-1", "SEC-3", "SEC-4", "SEC-5", "INT-2", "INT-3", "INT-4", "NAME-1", "NAME-2", "NAME-3", "NAME-4", "NAME-8", "VAL-4", "TPL-1",
    "TPL-4", "TPL-6",
)


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()


def rule_sort_key(rule: str) -> tuple[int, int | str]:
    if rule in RULE_ORDER:
        return (0, RULE_ORDER.index(rule))
    return (1, rule)


def render_json(
    findings: list[Finding], root: Path, *, disabled_rules: tuple[str, ...] = (),
    not_applicable_rules: tuple[str, ...] = (),
) -> str:
    excluded = set(disabled_rules) | set(not_applicable_rules)
    items = []
    for finding in sorted(findings, key=lambda item: rule_sort_key(item.rule)):
        if finding.rule in excluded:
            continue
        meta = RULES.get(finding.rule)
        items.append({
            "rule_id": finding.rule,
            "rule_title": meta.description if meta is not None else finding.rule,
            "files": [
                f"{relative_path(loc.path, root)}:{loc.line}:{loc.column}"
                for loc in finding.file_locations()
            ],
            "issue": finding.message,
            "action": finding.action.value,
            "fix_suggestion": finding.hint,
        })
    return json.dumps(items, ensure_ascii=False, indent=2) + "\n"


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


def render(findings: list[Finding], *, disabled_rules: tuple[str, ...] = (),
           not_applicable_rules: tuple[str, ...] = ()) -> str:
    by_rule: dict[str, list[Finding]] = {rule: [] for rule in RULE_ORDER if rule not in disabled_rules}
    for item in findings:
        if item.rule not in disabled_rules and item.rule not in not_applicable_rules:
            by_rule.setdefault(item.rule, []).append(item)
    if not by_rule:
        return "No rules enabled\n"
    return "\n\n".join(
        f"{rule}\nNot applicable" if rule in not_applicable_rules else _block(rule, items)
        for rule, items in by_rule.items()
    ) + "\n"
