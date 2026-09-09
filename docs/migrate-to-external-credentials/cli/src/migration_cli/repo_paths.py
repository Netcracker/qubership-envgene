"""Instance Repository path helpers for credential discovery."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def find_env_definitions(repo: Path) -> list[Path]:
    root = repo / "environments"
    if not root.is_dir():
        return []
    return sorted(root.glob("*/*/Inventory/env_definition.yml")) + sorted(
        root.glob("*/*/Inventory/env_definition.yaml")
    )


def find_context_files(repo: Path) -> list[Path]:
    """All External Credential Context files under environments/."""
    root = repo / "environments"
    if not root.is_dir():
        return []
    return sorted(root.glob("*/*/effective-set/external-credential/external-credentials.yaml")) + sorted(
        root.glob("*/*/effective-set/external-credential/external-credentials.yml")
    )


def scope_from_context_path(path: Path) -> tuple[str, str]:
    """Return (cluster, env) from an Effective Set context path."""
    normalised = str(path).replace("\\", "/")
    match = re.search(
        r"environments/(?P<cluster>[^/]+)/(?P<env>[^/]+)/effective-set"
        r"/external-credential/external-credentials\.ya?ml$",
        normalised,
        re.IGNORECASE,
    )
    if match:
        return match.group("cluster"), match.group("env")
    parts = Path(normalised).parts
    try:
        idx = parts.index("effective-set")
        return parts[idx - 2], parts[idx - 1]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Cannot derive cluster/env from context path: {path}") from exc


def parse_cluster_env(env_def_path: Path, repo: Path) -> tuple[str, str]:
    rel = env_def_path.relative_to(repo / "environments")
    return rel.parts[0], rel.parts[1]


def normalize_shared_stem(raw: str) -> tuple[str, bool]:
    stem = raw.strip()
    for ext in (".yml", ".yaml"):
        if stem.lower().endswith(ext):
            return stem[: -len(ext)], True
    return stem, False


def resolve_shared_file(repo: Path, cluster: str, env: str, stem: str) -> Path | None:
    candidates = [
        repo / "environments" / cluster / env / "Inventory" / "credentials" / f"{stem}.yml",
        repo / "environments" / cluster / env / "Inventory" / "credentials" / f"{stem}.yaml",
        repo / "environments" / cluster / "shared-credentials" / f"{stem}.yml",
        repo / "environments" / cluster / "shared-credentials" / f"{stem}.yaml",
        repo / "environments" / cluster / "credentials" / f"{stem}.yml",
        repo / "environments" / cluster / "credentials" / f"{stem}.yaml",
        repo / "environments" / "credentials" / f"{stem}.yml",
        repo / "environments" / "credentials" / f"{stem}.yaml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_passport_creds(repo: Path, cluster: str, passport_name: str) -> Path | None:
    base = repo / "environments" / cluster / "cloud-passport"
    for ext in (".yml", ".yaml"):
        path = base / f"{passport_name}-creds{ext}"
        if path.is_file():
            return path
    return None


def classify_path(path: Path, repo: Path) -> str:
    """Classify a credential-related file by path rules (mirrors migration-skill common.py)."""
    try:
        rel = path.relative_to(repo).as_posix()
    except ValueError:
        rel = path.as_posix()

    if "/cloud-passport/" in rel and (
        rel.endswith("-creds.yml")
        or rel.endswith("-creds.yaml")
        or Path(rel).name.endswith("-creds.yml")
        or Path(rel).name.endswith("-creds.yaml")
    ):
        return "cloud_passport_creds"
    if "/Inventory/credentials/" in rel:
        return "shared_credentials_env"
    if rel.startswith("environments/credentials/"):
        return "shared_credentials_repo"
    if "/shared-credentials/" in rel:
        return "shared_credentials_cluster"
    if re.search(r"^environments/[^/]+/credentials/", rel):
        return "shared_credentials_cluster"
    if rel.startswith("configuration/credentials/"):
        return "system_credentials"
    if "/Credentials/credentials.yml" in rel or "/Credentials/credentials.yaml" in rel:
        return "generated_credentials"
    return "unknown"


def bucket_kind(path: Path, repo: Path) -> str:
    """Map a credential file path to collect bucket: cloud|shared|repository_shared|env|skip."""
    file_class = classify_path(path, repo)
    if file_class == "cloud_passport_creds":
        return "cloud"
    if file_class == "shared_credentials_repo":
        return "repository_shared"
    if file_class == "shared_credentials_cluster":
        return "shared"
    if file_class == "shared_credentials_env":
        return "env"
    return "skip"


def load_env_definition(path: Path) -> dict[str, Any]:
    import yaml

    with path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    return doc if isinstance(doc, dict) else {}
