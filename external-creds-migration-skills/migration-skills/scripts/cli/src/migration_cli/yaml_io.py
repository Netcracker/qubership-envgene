"""YAML load/dump helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    """Load a YAML document from ``path``."""
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(path: Path, data: Any) -> None:
    """Write ``data`` as YAML to ``path``, replacing any previous file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)
