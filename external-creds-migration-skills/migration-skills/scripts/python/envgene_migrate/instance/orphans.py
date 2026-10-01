"""Instance — orphaned Shared credential detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .macros import extract_cred_ids_from_mapping
from .yaml_io import open_yaml, try_decrypt_cred_file


def _iter_shared_files(repo: Path) -> tuple[list[Path], list[Path]]:
    """Return (repo_or_cluster_shared, env_scoped_shared)."""
    repo_cluster: list[Path] = []
    env_scoped: list[Path] = []
    env_root = repo / "environments"
    if not env_root.is_dir():
        return repo_cluster, env_scoped

    def _add_yml(folder: Path, bucket: list[Path]) -> None:
        if not folder.is_dir():
            return
        bucket.extend(sorted(folder.glob("*.yml")))
        bucket.extend(sorted(folder.glob("*.yaml")))

    # environments/credentials/*.yml (legacy)
    _add_yml(env_root / "credentials", repo_cluster)
    # environments/shared-credentials/*.yml (repo-wide)
    _add_yml(env_root / "shared-credentials", repo_cluster)

    for cluster_dir in sorted(p for p in env_root.iterdir() if p.is_dir()):
        if cluster_dir.name in ("credentials", "shared-credentials"):
            continue
        # environments/<cluster>/credentials/*.yml (legacy)
        _add_yml(cluster_dir / "credentials", repo_cluster)
        # environments/<cluster>/shared-credentials/*.yml (cluster-level shared)
        _add_yml(cluster_dir / "shared-credentials", repo_cluster)
        for env_dir in sorted(p for p in cluster_dir.iterdir() if p.is_dir()):
            inv = env_dir / "Inventory" / "credentials"
            _add_yml(inv, env_scoped)
    return repo_cluster, env_scoped


def _cred_ids_in_file(path: Path) -> set[str]:
    data = try_decrypt_cred_file(path) or open_yaml(path) or {}
    if not isinstance(data, dict):
        return set()
    body = data.get("credentials", data)
    if not isinstance(body, dict):
        return set()
    ids = set()
    for cid, entry in body.items():
        if isinstance(entry, dict) and ("type" in entry or "data" in entry):
            ids.add(str(cid))
    return ids


def _referenced_cred_ids(repo: Path) -> set[str]:
    refs: set[str] = set()
    patterns = [
        "environments/**/*.yml",
        "environments/**/*.yaml",
        "configuration/**/*.yml",
        "configuration/**/*.yaml",
    ]
    # Avoid scanning credential value files as "references" only — still OK:
    # Built-in fields and macros live in consumers.
    skip_parts = {
        "Credentials",
        "cloud-passport",  # still scan main yml; skip *-creds below
    }
    for pattern in patterns:
        for path in repo.glob(pattern):
            if not path.is_file():
                continue
            name = path.name
            if name.endswith("-creds.yml") or name.endswith("-creds.yaml"):
                continue
            if "Inventory/credentials" in str(path).replace("\\", "/"):
                continue
            if path.name in ("credentials.yml", "credentials.yaml") and "Credentials" in path.parts:
                continue
            data = open_yaml(path)
            if data is not None:
                extract_cred_ids_from_mapping(data, refs)
    return refs


def find_orphaned_shared_files(repo: Path) -> list[str]:
    repo_cluster, _env_scoped = _iter_shared_files(repo)
    # Env-scoped never flagged orphaned
    referenced = _referenced_cred_ids(repo)
    orphaned: list[str] = []
    for path in repo_cluster:
        declared = _cred_ids_in_file(path)
        if not declared:
            continue
        if declared.isdisjoint(referenced):
            orphaned.append(str(path.relative_to(repo)).replace("\\", "/"))
    return orphaned
