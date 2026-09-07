"""YAML load/dump with optional Jinja2 line stripping for .j2 templates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_JINJA2_BLOCK_LINE_RE = re.compile(r"^\{%[-]?.*[-]?%\}$")
_JINJA2_STANDALONE_EXPR_LINE_RE = re.compile(r"^\{\{.*\}\}$")


def strip_jinja2_for_yaml(content: str) -> str:
    """Remove full-line Jinja2 tags so yaml.safe_load can parse .j2 files.

    Quoted ``{{ }}`` inside YAML scalar values are left untouched. Removed
    lines become empty lines so line numbers stay aligned for diagnostics.
    """
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if _JINJA2_BLOCK_LINE_RE.match(stripped):
            lines.append("")
            continue
        if _JINJA2_STANDALONE_EXPR_LINE_RE.match(stripped):
            lines.append("")
            continue
        lines.append(line)
    return "\n".join(lines)


def load_yaml(path: Path, *, strip_jinja: bool | None = None) -> Any:
    """Load YAML. Strip Jinja block lines for ``*.j2`` unless overridden."""
    with path.open(encoding="utf-8") as fh:
        content = fh.read()
    if strip_jinja is None:
        strip_jinja = path.name.endswith(".j2")
    if strip_jinja:
        content = strip_jinja2_for_yaml(content)
    return yaml.safe_load(content)


def dump_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(
            data,
            fh,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
