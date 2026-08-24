"""Shared helpers for Instance Repository migration scripts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NEEDS_INPUT = 2
EXIT_AMBIGUOUS = 2  # alias for NEEDS_INPUT

CREDS_GET_RE = re.compile(
    r"""\$\{(?:creds|envgen\.creds|cmdb\.creds)\.get\(['"]([^'"]+)['"]\)\.(username|password|secret)\}"""
)
HASH_CREDS_RE = re.compile(r"^#(creds|credscl|credsns)\{([^}]+)\}$")

BUILTIN_FIELD_NAMES = frozenset(
    {
        "credentialsId",
        "defaultCredentialsId",
        "tokenSecret",
        "credential",
    }
)

TECHNICAL_KEYS = frozenset({"technicalConfigurationParameters"})

PROVIDER_MARKERS = (
    "consul",
    "dbaas",
    "argocd",
    "webex",
    "operator",
    "service-account",
    "service_account",
    "serviceaccount",
)


def path_contains_cred_id(remote_ref_path: str, cred_id: str) -> bool:
    """True if path ends with or contains credId as a path segment."""
    if not remote_ref_path or not cred_id:
        return False
    parts = [p for p in remote_ref_path.strip("/").split("/") if p]
    return cred_id in parts or remote_ref_path.rstrip("/").endswith("/" + cred_id)


def heuristic_provider_markers(cred_id: str) -> list[str]:
    lower = cred_id.lower()
    hits = []
    for marker in PROVIDER_MARKERS:
        if marker in lower:
            hits.append(f"credId contains provider marker: {marker}")
    return hits


def tier_defaults_for_class(
    file_class: str, rel_path: str
) -> tuple[str, str, str, bool | None, str | None]:
    """Return tier, scope, creationOwner proposal, proposedCreate, path hint template.

    Path hint may use placeholders: {cluster}, {environment}.
    """
    parts = rel_path.split("/")
    cluster = parts[1] if len(parts) > 1 and parts[0] == "environments" else None
    environment = None
    if len(parts) > 2 and parts[0] == "environments":
        # environments/<cluster>/<env>/Inventory/credentials/...
        if "Inventory" in parts and parts[2] != "cloud-passport" and parts[2] != "shared-credentials":
            environment = parts[2]

    if file_class == "cloud_passport_creds":
        path = cluster
        return "passport-tier", "cluster", "pre-existing", False, path
    if file_class == "shared_credentials_env":
        path = f"{cluster}/{environment}" if cluster and environment else None
        return "env-tier", "environment", "envgene", True, path
    if file_class in ("shared_credentials", "shared_credentials_repo", "shared_credentials_cluster"):
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


class LiteralStr(str):
    """Marker for YAML literal-ish string preservation (unused; reserved)."""


def emit(result: dict[str, Any], exit_code: int = EXIT_OK) -> None:
    """Print structured JSON to stdout and exit."""
    payload = json.dumps(result, indent=2, ensure_ascii=True)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()
    sys.exit(exit_code)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


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
    if "/app-deployer/" in rel and (
        "creds" in Path(rel).name.lower()
    ):
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


def walk_replace_macros(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
    changes: list[dict[str, Any]] | None = None,
    skipped_technical: list[dict[str, Any]] | None = None,
) -> Any:
    """Replace credential macros with credRef mappings. Deterministic."""
    if changes is None:
        changes = []
    if skipped_technical is None:
        skipped_technical = []

    if isinstance(node, dict):
        # Legacy hash-macro keys
        new_dict: dict[str, Any] = {}
        pending_hash: list[tuple[str, str, list[str]]] = []
        for key, value in list(node.items()):
            key_str = str(key)
            m = HASH_CREDS_RE.match(key_str)
            if m and isinstance(value, str) and not in_technical:
                params = [p.strip() for p in m.group(2).split(",")]
                if len(params) == 2:
                    pending_hash.append((value, params[0], params[1] if False else ""))
                    # fix: store properly
                    pending_hash[-1] = (value, params[0], params[1])
                    changes.append(
                        {
                            "kind": "hash_macro",
                            "path": ".".join(path + (key_str,)),
                            "credId": value,
                            "params": params,
                        }
                    )
                    continue
            child_technical = in_technical or key_str in TECHNICAL_KEYS
            new_dict[key] = walk_replace_macros(
                value,
                path=path + (key_str,),
                in_technical=child_technical,
                changes=changes,
                skipped_technical=skipped_technical,
            )
        for cred_id, login_key, password_key in pending_hash:
            new_dict[login_key] = {
                "$type": "credRef",
                "credId": cred_id,
                "property": "username",
            }
            new_dict[password_key] = {
                "$type": "credRef",
                "credId": cred_id,
                "property": "password",
            }
        return new_dict

    if isinstance(node, list):
        return [
            walk_replace_macros(
                item,
                path=path + (str(i),),
                in_technical=in_technical,
                changes=changes,
                skipped_technical=skipped_technical,
            )
            for i, item in enumerate(node)
        ]

    if isinstance(node, str):
        stripped = node.strip()
        m = CREDS_GET_RE.fullmatch(stripped)
        if m:
            cred_id, prop = m.group(1), m.group(2)
            if in_technical:
                skipped_technical.append(
                    {
                        "path": ".".join(path),
                        "macro": node,
                        "reason": "technicalConfigurationParameters",
                    }
                )
                return node
            ref: dict[str, Any] = {"$type": "credRef", "credId": cred_id}
            if prop != "secret":
                ref["property"] = prop
            changes.append(
                {
                    "kind": "creds_get",
                    "path": ".".join(path),
                    "credId": cred_id,
                    "property": prop if prop != "secret" else None,
                }
            )
            return ref
    return node


def find_remaining_macros(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            if HASH_CREDS_RE.match(key_str):
                found.append(
                    {
                        "path": ".".join(path + (key_str,)),
                        "kind": "hash_macro",
                        "technical": in_technical or key_str in TECHNICAL_KEYS,
                    }
                )
            child_tech = in_technical or key_str in TECHNICAL_KEYS
            found.extend(
                find_remaining_macros(
                    value, path=path + (key_str,), in_technical=child_tech
                )
            )
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found.extend(
                find_remaining_macros(item, path=path + (str(i),), in_technical=in_technical)
            )
    elif isinstance(node, str):
        if CREDS_GET_RE.search(node):
            found.append(
                {
                    "path": ".".join(path),
                    "kind": "creds_get",
                    "technical": in_technical,
                    "snippet": node[:120],
                }
            )
    return found
