"""Self-contained HTML check report for an instance repository."""

from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

from .model import Action, Finding, IssueType
from .report import RULE_ORDER
from .rulemeta import RULES

REPORT_FILENAME = "envgene-linter-report.html"

_CHIP_CLASS = {
    IssueType.WARNING.value: "chip-warning",
    IssueType.ERROR.value: "chip-error",
    IssueType.INFORMATION.value: "chip-information",
    Action.FIX.value: "chip-fix",
    Action.REVIEW.value: "chip-review",
}

_CSS = """
:root { color-scheme: light; }
body {
  font: 15px/1.45 system-ui, sans-serif;
  max-width: 56rem;
  margin: 2rem auto;
  padding: 0 1.25rem 3rem;
  color: #1a1a1a;
}
h1 {
  font: 700 1.7rem/1.2 Georgia, "Times New Roman", serif;
  margin: 0 0 1.4rem;
}
details.rule-section {
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  padding: 0.65rem 0.85rem 0.35rem;
  margin: 0 0 1rem;
}
details.rule-section + details.rule-section { margin-top: 0.85rem; }
summary.rule-id {
  font: 600 1.15rem/1.3 Georgia, "Times New Roman", serif;
  cursor: pointer;
  margin: 0 0 0.6rem;
}
.finding {
  margin: 0 0 0.85rem;
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
  display: grid;
  grid-template-columns: 6.5rem 1fr;
  font-size: 0.95rem;
}
.label {
  padding: 0.5rem 0.7rem;
  background: #f3f3f3;
  font-size: 0.7rem;
  font-weight: 400;
  color: #666;
  border-bottom: 1px solid #eee;
}
.value {
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #eee;
}
.finding > div:nth-last-child(-n+2) { border-bottom: 0; }
.file { font-family: ui-monospace, monospace; font-size: 0.88em; }
.chip {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.6rem;
  font-size: 0.8rem;
  border: 1px solid #bbb;
  background: #eee;
}
.chip-warning { background: #fff3cd; border-color: #e0c36a; }
.chip-error { background: #fde8e8; border-color: #e39a9a; }
.chip-information { background: #e8eef5; border-color: #b0bec5; }
.chip-fix { background: #e8f0fe; border-color: #9db7e8; }
.chip-review { background: #eee; border-color: #bbb; }
"""


def report_path(root: Path) -> Path:
    return root / REPORT_FILENAME


def ensure_report_ignored(root: Path) -> None:
    path = root / ".gitignore"
    names = {REPORT_FILENAME, f"/{REPORT_FILENAME}"}
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(line.strip() in names for line in text.splitlines()):
            return
        if text and not text.endswith("\n"):
            text += "\n"
        path.write_text(f"{text}{REPORT_FILENAME}\n", encoding="utf-8")
        return
    path.write_text(f"{REPORT_FILENAME}\n", encoding="utf-8")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()


def _rule_sort_key(rule: str) -> tuple[int, int | str]:
    if rule in RULE_ORDER:
        return (0, RULE_ORDER.index(rule))
    return (1, rule)


def _chip(value: str) -> str:
    cls = _CHIP_CLASS.get(value, "chip-review")
    return f'<span class="chip {cls}">{html.escape(value)}</span>'


def _file_html(item: Finding, root: Path) -> str:
    lines = []
    for loc in item.file_locations():
        text = f"{_relative(loc.path, root)}:{loc.line}:{loc.column}"
        lines.append(f'<span class="file">{html.escape(text)}</span>')
    return "<br>\n".join(lines)


def _card(item: Finding, root: Path) -> list[str]:
    rows = (
        ("FILE", _file_html(item, root)),
        ("ISSUE", html.escape(item.message)),
        ("TYPE", _chip(item.issue_type.value)),
        ("ACTION", _chip(item.action.value)),
        ("FIX SUGGESTION", html.escape(item.hint)),
    )
    parts = ['<div class="finding">']
    for label, value in rows:
        parts.append(f'<div class="label">{html.escape(label)}</div>')
        parts.append(f'<div class="value">{value}</div>')
    parts.append("</div>")
    return parts


def render_html(findings: list[Finding], root: Path) -> str:
    by_rule: dict[str, list[Finding]] = defaultdict(list)
    for item in findings:
        by_rule[item.rule].append(item)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Envgene Linter Report</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        "<h1>Envgene Linter Report</h1>",
    ]
    if not findings:
        parts.append("<p>No findings</p>")
    else:
        for rule in sorted(by_rule, key=_rule_sort_key):
            meta = RULES.get(rule)
            title = f"{rule}: {meta.description}" if meta is not None else rule
            parts.append('<details class="rule-section">')
            parts.append(f'<summary class="rule-id">{html.escape(title)}</summary>')
            for item in by_rule[rule]:
                parts.extend(_card(item, root))
            parts.append("</details>")
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)
