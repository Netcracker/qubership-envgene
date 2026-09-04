"""Instance Repository helpers. Shared macro/YAML logic lives in extcreds_mig."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_SHARED = Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from extcreds_mig.constants import (  # noqa: E402
    BUILTIN_FIELD_NAMES,
    CREDS_GET_RE,
    DEFAULT_SECRET_STORE,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    HASH_CREDS_RE,
    PROVIDER_MARKERS,
    STUB_VALUES,
    SUPPORTED_LOCAL_TYPES,
    TECHNICAL_KEYS,
    UNSUPPORTED_LOCAL_TYPES,
)
from extcreds_mig.emit import emit  # noqa: E402
from extcreds_mig.macros import (  # noqa: E402
    base_external_entry,
    collect_referenced_cred_ids,
    find_macro_issues,
    find_remaining_macros,
    heuristic_provider_markers,
    path_contains_cred_id,
    walk_replace_macros,
)
from extcreds_mig.yaml_io import dump_yaml, load_yaml  # noqa: E402

EXIT_AMBIGUOUS = EXIT_NEEDS_INPUT

__all__ = [
    "BUILTIN_FIELD_NAMES",
    "CREDS_GET_RE",
    "DEFAULT_SECRET_STORE",
    "EXIT_AMBIGUOUS",
    "EXIT_ERROR",
    "EXIT_NEEDS_INPUT",
    "EXIT_OK",
    "HASH_CREDS_RE",
    "PROVIDER_MARKERS",
    "STUB_VALUES",
    "SUPPORTED_LOCAL_TYPES",
    "TECHNICAL_KEYS",
    "UNSUPPORTED_LOCAL_TYPES",
    "base_external_entry",
    "build_decision_record",
    "classify_path",
    "collect_referenced_cred_ids",
    "discover_shared_credential_files",
    "dump_yaml",
    "emit",
    "find_env_definitions",
    "find_macro_issues",
    "find_remaining_macros",
    "heuristic_provider_markers",
    "is_credential_mapping",
    "is_stub_data",
    "iter_credential_entries",
    "iter_yaml_files",
    "load_yaml",
    "normalize_shared_stem",
    "parse_cluster_env",
    "path_contains_cred_id",
    "repo_path",
    "resolve_passport_creds",
    "resolve_shared_file",
    "tier_defaults_for_class",
    "walk_replace_macros",
]


def repo_path(repo: Path, *parts: str) -> Path:
    return repo.joinpath(*parts)


def find_env_definitions(repo: Path) -> list[Path]:
    root = repo / "environments"
    if not root.is_dir():
        return []
    return sorted(root.glob("*/*/Inventory/env_definition.yml")) + sorted(
        root.glob("*/*/Inventory/env_definition.yaml")
    )


def parse_cluster_env(env_def_path: Path, repo: Path) -> tuple[str, str]:
    rel = env_def_path.relative_to(repo / "environments")
    parts = rel.parts
    return parts[0], parts[1]


def is_credential_mapping(node: Any) -> bool:
    return isinstance(node, dict) and "type" in node


def iter_credential_entries(doc: Any) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(doc, dict):
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for key, value in doc.items():
        if key in ("---",):
            continue
        if is_credential_mapping(value):
            out.append((str(key), value))
    return out


def classify_path(path: Path, repo: Path) -> str:
    """Classify a credential-related file by path rules."""
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
    if "/cloud-passport/" in rel:
        return "cloud_passport_main"
    if "/Inventory/credentials/" in rel:
        return "shared_credentials_env"
    if rel.startswith("environments/credentials/") or rel.startswith(
        "environments/credentials\\"
    ):
        return "shared_credentials_repo"
    if "/shared-credentials/" in rel:
        return "shared_credentials_cluster"
    if re.search(r"^environments/[^/]+/credentials/", rel):
        return "shared_credentials_cluster"
    if rel in (
        "configuration/credentials/credentials.yml",
        "configuration/credentials/credentials.yaml",
    ) or rel.startswith("configuration/credentials/"):
        return "system_credentials"
    if "/app-deployer/" in rel and ("creds" in Path(rel).name.lower()):
        return "system_credentials"
    if "/Credentials/credentials.yml" in rel or "/Credentials/credentials.yaml" in rel:
        return "generated_credentials"
    if "/effective-set/" in rel:
        return "generated_effective_set"
    if "/parameters/" in rel or "/Inventory/" in rel:
        return "parameters"
    if rel in ("configuration/deployer.yml", "configuration/integration.yml"):
        return "system_config"
    return "other"


def tier_defaults_for_class(
    file_class: str, rel_path: str
) -> tuple[str, str, str, bool | None, str | None]:
    """Return tier, scope, creationOwner proposal, proposedCreate, path hint."""
    parts = rel_path.split("/")
    cluster = parts[1] if len(parts) > 1 and parts[0] == "environments" else None
    environment = None
    if len(parts) > 2 and parts[0] == "environments":
        if "Inventory" in parts and parts[2] not in ("cloud-passport", "shared-credentials"):
            environment = parts[2]

    if file_class == "cloud_passport_creds":
        return "passport-tier", "cluster", "pre-existing", False, cluster
    if file_class == "shared_credentials_env":
        path = f"{cluster}/{environment}" if cluster and environment else None
        return "env-tier", "environment", "envgene", True, path
    if file_class in (
        "shared_credentials",
        "shared_credentials_repo",
        "shared_credentials_cluster",
    ):
        return "external-tier", "shared", "pre-existing", False, "external"
    if file_class == "system_credentials":
        return "external-tier", "system", "pre-existing", False, "external"
    return "unknown", "unknown", "unknown", None, None


def build_decision_record(
    cred_id: str,
    rel_path: str,
    file_class: str,
    *,
    local_type: str | None,
) -> dict[str, Any]:
    """Build a policy decision record without secret values."""
    evidence: list[str] = [f"source path class: {file_class}"]
    tier, scope, owner, prop_create, path = tier_defaults_for_class(file_class, rel_path)
    markers = heuristic_provider_markers(cred_id)
    confidence = "proposed"
    needs_review = True

    if markers:
        evidence.extend(markers)
        owner = "unknown"
        prop_create = None
        path = None
        confidence = "ambiguous"
        needs_review = True
        evidence.append("heuristic only - not proof of provider ownership")

    if tier == "unknown" or owner == "unknown" or path is None:
        if confidence != "ambiguous":
            confidence = "ambiguous" if owner == "unknown" or path is None else confidence
        needs_review = True

    if local_type == "external":
        evidence.append("already type: external")

    return {
        "credId": cred_id,
        "sourcePath": rel_path,
        "tier": tier,
        "scope": scope,
        "creationOwner": owner,
        "evidence": evidence,
        "confidence": confidence,
        "proposedCreate": prop_create,
        "proposedRemoteRefPath": path,
        "needsReview": needs_review,
        "writeToStore": None,
    }


def normalize_shared_stem(name: str) -> tuple[str, bool]:
    text = str(name).strip()
    if text.endswith(".yml"):
        return text[:-4], True
    if text.endswith(".yaml"):
        return text[:-5], True
    return text, False


def is_stub_data(data: Any) -> bool:
    if data is None:
        return True
    if isinstance(data, str):
        return data.strip() in STUB_VALUES
    if isinstance(data, dict):
        if not data:
            return True
        return all(
            (isinstance(v, str) and v.strip() in STUB_VALUES) or v is None
            for v in data.values()
        )
    return False


def discover_shared_credential_files(repo: Path) -> list[Path]:
    patterns = (
        "environments/credentials/*.yml",
        "environments/credentials/*.yaml",
        "environments/*/credentials/*.yml",
        "environments/*/credentials/*.yaml",
        "environments/*/shared-credentials/*.yml",
        "environments/*/shared-credentials/*.yaml",
        "environments/*/*/Inventory/credentials/*.yml",
        "environments/*/*/Inventory/credentials/*.yaml",
    )
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(p for p in sorted(repo.glob(pattern)) if p.is_file())
    return paths


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


def iter_yaml_files(paths: list[Path]) -> list[Path]:
    return [p for p in paths if p.is_file() and p.suffix in (".yml", ".yaml")]
