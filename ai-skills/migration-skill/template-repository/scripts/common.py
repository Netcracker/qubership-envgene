"""Shared helpers for Template Repository migration scripts."""

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
EXIT_AMBIGUOUS = 2

CREDS_GET_RE = re.compile(
    r"""\$\{(?:creds|envgen\.creds|cmdb\.creds)\.get\(['"]([^'"]+)['"]\)\.(username|password|secret)\}"""
)
HASH_CREDS_RE = re.compile(r"^#(creds|credscl|credsns)\{([^}]+)\}$")
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

DEFAULT_TEMPLATE_PATH = "{{ current_env.cloud }}/{{ current_env.name }}"


def path_contains_cred_id(remote_ref_path: str, cred_id: str) -> bool:
    if not remote_ref_path or not cred_id:
        return False
    parts = [p for p in remote_ref_path.strip("/").split("/") if p]
    # Jinja segments are OK; only flag literal credId segment
    return cred_id in parts


def heuristic_provider_markers(cred_id: str) -> list[str]:
    lower = cred_id.lower()
    return [
        f"credId contains provider marker: {marker}"
        for marker in PROVIDER_MARKERS
        if marker in lower
    ]


def emit(result: dict[str, Any], exit_code: int = EXIT_OK) -> None:
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


def find_descriptors(repo: Path) -> list[Path]:
    found = []
    for pattern in (
        "templates/env_templates/*.yml",
        "templates/env_templates/*.yaml",
        "templates/env_templates/*/*.yml",
        "templates/env_templates/*/*.yaml",
    ):
        for path in sorted(repo.glob(pattern)):
            if not path.is_file():
                continue
            # descriptors typically have cloud/tenant keys; skip j2
            if path.suffix in (".yml", ".yaml") and ".j2" not in path.name:
                try:
                    doc = load_yaml(path)
                except Exception:  # noqa: BLE001
                    continue
                if isinstance(doc, dict) and ("cloud" in doc or "tenant" in doc or "namespaces" in doc):
                    found.append(path)
    # unique
    return sorted(set(found))


def walk_replace_macros(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
    changes: list | None = None,
    skipped_technical: list | None = None,
) -> Any:
    if changes is None:
        changes = []
    if skipped_technical is None:
        skipped_technical = []

    if isinstance(node, dict):
        new_dict: dict[str, Any] = {}
        pending_hash: list[tuple[str, str, str]] = []
        for key, value in list(node.items()):
            key_str = str(key)
            m = HASH_CREDS_RE.match(key_str)
            if m and isinstance(value, str) and not in_technical:
                params = [p.strip() for p in m.group(2).split(",")]
                if len(params) == 2:
                    pending_hash.append((value, params[0], params[1]))
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
        m = CREDS_GET_RE.fullmatch(node.strip())
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


def collect_cred_evidence(node: Any, *, path: tuple[str, ...] = (), in_technical: bool = False) -> dict[str, dict]:
    """credId -> {shapes: set, locations: list, technical_only: bool}"""
    bag: dict[str, dict] = {}

    def add(cred_id: str, shape: str | None, loc: str, technical: bool) -> None:
        item = bag.setdefault(
            cred_id,
            {"shapes": set(), "locations": [], "seen_technical": False, "seen_non_technical": False},
        )
        if shape:
            item["shapes"].add(shape)
        item["locations"].append(loc)
        if technical:
            item["seen_technical"] = True
        else:
            item["seen_non_technical"] = True

    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            child_tech = in_technical or key_str in TECHNICAL_KEYS
            m = HASH_CREDS_RE.match(key_str)
            if m and isinstance(value, str) and not child_tech:
                add(value, "multi_field", ".".join(path + (key_str,)), False)
                continue
            # built-in field names
            if key_str in (
                "credentialsId",
                "defaultCredentialsId",
                "tokenSecret",
                "credential",
            ) and isinstance(value, str) and not value.startswith("{{"):
                # structure hints from parent context (see structure-from-refs.md)
                parent = path[-1] if path else ""
                shape = None
                if key_str == "defaultCredentialsId":
                    shape = None  # ambiguous alone - ask user
                elif parent == "maasConfig" or "dbaas" in parent.lower():
                    shape = "multi_field"
                elif (
                    key_str == "tokenSecret"
                    or parent in ("vaultConfig", "consulConfig")
                    or key_str in ("credentialsId", "credential")
                ):
                    # Namespace.credentialsId / Tenant.credential / vault / consul
                    shape = "single_value"
                add(value, shape, ".".join(path + (key_str,)), child_tech)
            bag_child = collect_cred_evidence(
                value, path=path + (key_str,), in_technical=child_tech
            )
            for cid, meta in bag_child.items():
                dest = bag.setdefault(
                    cid,
                    {
                        "shapes": set(),
                        "locations": [],
                        "seen_technical": False,
                        "seen_non_technical": False,
                    },
                )
                dest["shapes"] |= meta["shapes"]
                dest["locations"].extend(meta["locations"])
                dest["seen_technical"] = dest["seen_technical"] or meta["seen_technical"]
                dest["seen_non_technical"] = dest["seen_non_technical"] or meta["seen_non_technical"]
    elif isinstance(node, list):
        for i, item in enumerate(node):
            bag_child = collect_cred_evidence(
                item, path=path + (str(i),), in_technical=in_technical
            )
            for cid, meta in bag_child.items():
                dest = bag.setdefault(
                    cid,
                    {
                        "shapes": set(),
                        "locations": [],
                        "seen_technical": False,
                        "seen_non_technical": False,
                    },
                )
                dest["shapes"] |= meta["shapes"]
                dest["locations"].extend(meta["locations"])
                dest["seen_technical"] = dest["seen_technical"] or meta["seen_technical"]
                dest["seen_non_technical"] = dest["seen_non_technical"] or meta["seen_non_technical"]
    elif isinstance(node, str):
        m = CREDS_GET_RE.search(node)
        if m:
            prop = m.group(2)
            shape = "single_value" if prop == "secret" else "multi_field"
            add(m.group(1), shape, ".".join(path), in_technical)
    return bag
