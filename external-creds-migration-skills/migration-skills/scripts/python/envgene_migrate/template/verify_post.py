"""Post-apply verification (DoD)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .macros import BUILTIN_CRED_FIELDS
from .yaml_io import open_yaml


class VerifyError(Exception):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


def _cred_entries(data: Any) -> Iterable[tuple[str, dict]]:
    if not isinstance(data, dict):
        return
    # Flat map of cred-id → entry, or wrapped under credentials:
    root = data.get("credentials", data) if isinstance(data.get("credentials"), dict) else data
    if not isinstance(root, dict):
        return
    for cid, entry in root.items():
        if cid in ("apiVersion", "kind", "metadata", "type") and not isinstance(entry, dict):
            continue
        if isinstance(entry, dict) and ("type" in entry or "data" in entry or "remoteRefPath" in entry):
            yield str(cid), entry


def verify_cred_file(path: Path) -> list[str]:
    issues: list[str] = []
    data = open_yaml(path)
    if data is None:
        return issues
    for cid, entry in _cred_entries(data):
        if "data" in entry:
            issues.append(f"{path}: [{cid}] still has data field")
        if entry.get("type") != "external":
            issues.append(f"{path}: [{cid}] type is not external")
        rrp = entry.get("remoteRefPath")
        if not rrp:
            issues.append(f"{path}: [{cid}] remoteRefPath missing or empty")
    return issues


def verify_builtins_untouched(data: Any, path: Path) -> list[str]:
    issues: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in BUILTIN_CRED_FIELDS and isinstance(v, dict) and v.get("$type") == "credRef":
                    issues.append(
                        f"{path}: Built-in field {k} must stay plain credId string"
                    )
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return issues


def verify_deleted(paths: list[str], repo_root: Path) -> list[str]:
    issues = []
    for rel in paths:
        if (repo_root / rel).exists():
            issues.append(f"to_delete file still present: {rel}")
    return issues


def run_verification(
    *,
    repo_root: Path,
    touched_cred_files: list[Path],
    touched_consumer_files: list[Path],
    to_delete: list[str],
) -> None:
    issues: list[str] = []
    for p in touched_cred_files:
        issues.extend(verify_cred_file(p))
    for p in touched_consumer_files:
        data = open_yaml(p)
        if data is not None:
            issues.extend(verify_builtins_untouched(data, p))
    issues.extend(verify_deleted(to_delete, repo_root))
    if issues:
        raise VerifyError(issues)
