"""Check envTemplate.artifact across Instance env_definition files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .yaml_io import open_yaml


def _env_definition_paths(repo_root: Path) -> list[Path]:
    root = repo_root / "environments"
    if not root.is_dir():
        return []
    out: list[Path] = []
    out.extend(sorted(root.glob("*/Inventory/env_definition.yml")))
    out.extend(sorted(root.glob("*/Inventory/env_definition.yaml")))
    out.extend(sorted(root.glob("*/*/Inventory/env_definition.yml")))
    out.extend(sorted(root.glob("*/*/Inventory/env_definition.yaml")))
    # de-dupe while preserving order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def _artifact_from_doc(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    env_template = data.get("envTemplate")
    if not isinstance(env_template, dict):
        return None
    art = env_template.get("artifact")
    if art is None:
        return None
    return str(art).strip() or None


def check_template_versions(
    repo_root: Path, expect: str
) -> tuple[bool, list[str]]:
    """Return (ok, detail_lines). ok True when every env_definition matches expect."""
    expect_n = expect.strip()
    paths = _env_definition_paths(repo_root)
    if not paths:
        return False, [
            "No environments/**/Inventory/env_definition.yml(.yaml) found under "
            f"{repo_root}"
        ]

    mismatches: list[str] = []
    for path in paths:
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        data = open_yaml(path)
        actual = _artifact_from_doc(data)
        if actual is None:
            mismatches.append(f"{rel}: envTemplate.artifact missing or empty")
        elif actual != expect_n:
            mismatches.append(f"{rel}: artifact={actual!r} (expected {expect_n!r})")

    if mismatches:
        return False, mismatches
    return True, [f"OK: {len(paths)} env_definition file(s) have artifact={expect_n!r}"]
