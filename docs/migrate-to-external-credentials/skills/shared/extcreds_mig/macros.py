"""Credential macro detection and credRef replacement (shared)."""

from __future__ import annotations

from typing import Any

from extcreds_mig.constants import (
    BUILTIN_FIELD_NAMES,
    CREDS_GET_RE,
    DEFAULT_SECRET_STORE,
    HASH_CREDS_RE,
    PROVIDER_MARKERS,
    TECHNICAL_KEYS,
)


def base_external_entry(*, remote_ref_path: str, secret_store: str) -> dict[str, Any]:
    """Build external Credential fields.

    Always write ``secretStore``. JSON Schema defaults ``default_store``, but the
    Effective Set calculator reads ``Credential.secretStore`` as-is with no
    runtime fallback (see ``ExternalCredUtils``).
    """
    return {
        "type": "external",
        "secretStore": secret_store or DEFAULT_SECRET_STORE,
        "remoteRefPath": remote_ref_path,
    }


def path_contains_cred_id(remote_ref_path: str, cred_id: str) -> bool:
    if not remote_ref_path or not cred_id:
        return False
    parts = [p for p in remote_ref_path.strip("/").split("/") if p]
    return cred_id in parts


def heuristic_provider_markers(cred_id: str) -> list[str]:
    lower = cred_id.lower()
    return [
        f"credId contains provider marker: {marker}"
        for marker in PROVIDER_MARKERS
        if marker in lower
    ]


def walk_replace_macros(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
    changes: list | None = None,
    skipped_technical: list | None = None,
) -> Any:
    """Replace credential macros with ``$type: credRef`` mappings."""
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
                find_remaining_macros(
                    item, path=path + (str(i),), in_technical=in_technical
                )
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


def find_macro_issues(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            child_tech = in_technical or key_str in TECHNICAL_KEYS
            issues.extend(
                find_macro_issues(
                    value, path=path + (key_str,), in_technical=child_tech
                )
            )
    elif isinstance(node, list):
        for i, item in enumerate(node):
            issues.extend(
                find_macro_issues(
                    item, path=path + (str(i),), in_technical=in_technical
                )
            )
    elif isinstance(node, str):
        stripped = node.strip()
        match = CREDS_GET_RE.search(stripped)
        if not match:
            return issues
        location = ".".join(path)
        if in_technical:
            issues.append(
                {
                    "kind": "technical_macro",
                    "severity": "warning",
                    "path": location,
                    "credId": match.group(1),
                    "message": (
                        "Credential macro in technicalConfigurationParameters "
                        "is out of migration scope"
                    ),
                }
            )
            return issues
        if CREDS_GET_RE.fullmatch(stripped):
            return issues
        issues.append(
            {
                "kind": "composite_macro",
                "severity": "blocker",
                "path": location,
                "credId": match.group(1),
                "snippet": stripped[:120],
                "message": (
                    "Composite credential macro cannot become $type: credRef; "
                    "split into separate parameters"
                ),
            }
        )
    return issues


def collect_referenced_cred_ids(
    node: Any,
    *,
    path: tuple[str, ...] = (),
    in_technical: bool = False,
) -> set[str]:
    """Collect credIds from macros, hash-macros, built-ins, or credRef."""
    found: set[str] = set()
    if isinstance(node, dict):
        if node.get("$type") == "credRef" and isinstance(node.get("credId"), str):
            found.add(node["credId"])
        for key, value in node.items():
            key_str = str(key)
            child_tech = in_technical or key_str in TECHNICAL_KEYS
            hash_match = HASH_CREDS_RE.match(key_str)
            if hash_match and isinstance(value, str) and not child_tech:
                found.add(value)
                continue
            if key_str in BUILTIN_FIELD_NAMES and isinstance(value, str):
                if value and not value.startswith("{{") and not value.startswith("${"):
                    found.add(value)
            found |= collect_referenced_cred_ids(
                value, path=path + (key_str,), in_technical=child_tech
            )
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found |= collect_referenced_cred_ids(
                item, path=path + (str(i),), in_technical=in_technical
            )
    elif isinstance(node, str):
        for match in CREDS_GET_RE.finditer(node):
            found.add(match.group(1))
    return found
