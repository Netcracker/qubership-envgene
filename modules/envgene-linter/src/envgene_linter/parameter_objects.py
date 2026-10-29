"""Filesystem safety and finding eligibility for parameter consumers."""

from __future__ import annotations

from pathlib import Path

from .model import RepoIndex
from .source_scope import is_generated_output


def safe_parameter_path(index: RepoIndex, path: Path) -> bool:
    try:
        logical = path.absolute().relative_to(index.root)
        physical = path.resolve().relative_to(index.root)
        return ".git" not in logical.parts and ".git" not in physical.parts and path.is_file()
    except (ValueError, OSError, RuntimeError):
        return False


def authored_parameter_path(index: RepoIndex, path: Path) -> bool:
    return safe_parameter_path(index, path) and not is_generated_output(index, path)
