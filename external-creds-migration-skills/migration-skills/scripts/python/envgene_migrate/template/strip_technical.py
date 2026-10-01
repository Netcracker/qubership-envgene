"""Strip credential macros from technical/runtime context (Template only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .macros import (
    CompositeMacroError,
    surgical_strip_runtime_file,
)
from .plan_schema import read_plan

TECH_PARAMSETS_SOURCE = "technicalConfigurationParameterSets"


def _group_hits(
    hits: list[dict[str, Any]],
) -> dict[str, str]:
    """Map relative file path → strip mode source (last wins if mixed)."""
    by_file: dict[str, str] = {}
    for row in hits:
        rel = str(row.get("file") or "").replace("\\", "/")
        if not rel:
            continue
        source = str(row.get("source") or "technicalConfigurationParameters")
        # Prefer paramsets mode if any hit says so (whole body is runtime).
        if by_file.get(rel) == TECH_PARAMSETS_SOURCE:
            continue
        by_file[rel] = source
    return by_file


def strip_file(
    repo_root: Path,
    rel: str,
    *,
    source: str,
    dry_run: bool,
) -> tuple[int, str | None]:
    """Strip one file surgically (line edits only). Returns (removed_count, error)."""
    path = repo_root / rel
    if not path.is_file():
        return 0, f"missing file: {rel}"

    mode = "paramset" if source == TECH_PARAMSETS_SOURCE else "wrapper"
    try:
        count = surgical_strip_runtime_file(path, mode=mode, dry_run=dry_run)
    except CompositeMacroError as exc:
        return 0, str(exc)
    except OSError as exc:
        return 0, f"{rel}: {exc}"
    return count, None


def strip_technical_macros(
    repo_root: Path,
    *,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """Remove runtime credential macros listed in migration-plan.yaml.

    Returns (files_touched, macros_removed, errors).
    """
    plan = read_plan(cwd=cwd or Path.cwd())
    if plan.get("repo_type") and plan.get("repo_type") != "template":
        raise ValueError(
            f"plan repo_type={plan.get('repo_type')!r} requires --repo=template"
        )
    hits = list(plan.get("runtime_credential_macros") or [])
    if not hits:
        return 0, 0, []

    by_file = _group_hits(hits)
    files_touched = 0
    macros_removed = 0
    errors: list[str] = []

    for rel in sorted(by_file):
        count, err = strip_file(
            repo_root, rel, source=by_file[rel], dry_run=dry_run
        )
        if err:
            errors.append(err)
            continue
        if count:
            files_touched += 1
            macros_removed += count
            label = "would remove" if dry_run else "removed"
            print(f"[STRIP] {rel}: {label} {count} macro(s)", flush=True)
        else:
            print(f"[STRIP] {rel}: no removable macros found", flush=True)

    return files_touched, macros_removed, errors
