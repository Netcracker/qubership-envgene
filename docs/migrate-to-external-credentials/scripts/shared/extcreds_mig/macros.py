"""Credential macro detection and credRef replacement (shared)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from extcreds_mig.constants import (
    BUILTIN_FIELD_NAMES,
    CREDS_GET_RE,
    DEFAULT_SECRET_STORE,
    HASH_CREDS_RE,
    PROVIDER_MARKERS,
    TECHNICAL_KEYS,
    TECHNICAL_PARAMSET_KEY,
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


_NAME_PATTERN_CHECKS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[-_]token$", re.IGNORECASE), "ends with -token"),
    (re.compile(r"client.*(creds|secret)", re.IGNORECASE), "client + creds/secret"),
    (re.compile(r"admin[-_]user", re.IGNORECASE), "admin_user"),
    (re.compile(r"(^|[-_])idp([-_]|$)", re.IGNORECASE), "idp segment"),
    (re.compile(r"(^|[-_])ext(ernal)?([-_]|$)", re.IGNORECASE), "external/ext segment"),
    (re.compile(r"(^|[-_])(s3|storage)([-_]|$)", re.IGNORECASE), "s3/storage segment"),
    (re.compile(r"(^|[-_])git([-_]|$)", re.IGNORECASE), "git segment"),
    (re.compile(r"(^|[-_])k8s([-_]|$)", re.IGNORECASE), "k8s segment"),
)


def heuristic_provider_markers(cred_id: str) -> list[str]:
    lower = cred_id.lower()
    hits = [
        f"credId contains provider marker: {marker}"
        for marker in PROVIDER_MARKERS
        if marker in lower
    ]
    hits.extend(
        f"credId name pattern: {label}"
        for pattern, label in _NAME_PATTERN_CHECKS
        if pattern.search(cred_id)
    )
    return hits


def _parameter_set_stem(path: Path) -> str:
    name = path.name
    for suffix in (".yml.j2", ".yaml.j2", ".yml", ".yaml"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def resolve_parameter_set_paths(repo: Path, set_name: str) -> list[Path]:
    """Find ParameterSet files under templates/parameters whose stem matches set_name."""
    root = repo / "templates" / "parameters"
    if not root.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and _parameter_set_stem(path) == set_name:
            found.append(path)
    return found


def parameter_set_has_cred_macros(repo: Path, set_name: str) -> tuple[bool, list[str]]:
    """Return whether a ParameterSet still contains creds.get / #creds macros.

    Returns (has_macros, relative paths of resolved files). Empty paths means the
    set file was not found under templates/parameters.
    """
    paths = resolve_parameter_set_paths(repo, set_name)
    rels = [p.relative_to(repo).as_posix() for p in paths]
    if not paths:
        return False, []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if CREDS_GET_RE.search(text) or HASH_CREDS_RE.search(text):
            return True, rels
    return False, rels


def _technical_paramset_issues(
    *,
    location: str,
    names: list[str],
    repo: Path | None,
) -> list[dict[str, Any]]:
    """Block only when bound technical ParameterSets still contain cred macros."""
    if repo is None:
        return [
            {
                "kind": "technical_paramset_sets",
                "severity": "warning",
                "path": location,
                "sets": names,
                "message": (
                    "technicalConfigurationParameterSets is not empty: "
                    + ", ".join(names)
                    + ". Pass repo to preflight to check whether sets still contain "
                    "credential macros"
                ),
                "suggested_action": (
                    "Re-run preflight with --repo so sets are scanned for creds.get"
                ),
            }
        ]

    issues: list[dict[str, Any]] = []
    sets_with_creds: list[str] = []
    sets_clean: list[str] = []
    unresolved: list[str] = []
    set_files: dict[str, list[str]] = {}

    for name in names:
        has_macros, rels = parameter_set_has_cred_macros(repo, name)
        set_files[name] = rels
        if not rels:
            unresolved.append(name)
        elif has_macros:
            sets_with_creds.append(name)
        else:
            sets_clean.append(name)

    if sets_with_creds:
        issues.append(
            {
                "kind": "technical_paramset_sets",
                "severity": "blocker",
                "path": location,
                "sets": sets_with_creds,
                "setFiles": {n: set_files[n] for n in sets_with_creds},
                "message": (
                    "technicalConfigurationParameterSets still contain credential "
                    "macros: "
                    + ", ".join(sets_with_creds)
                    + ". External Credentials migration cannot convert these; "
                    "resolve before cutover"
                ),
                "suggested_action": (
                    "Move creds.get / #creds out of those ParameterSets into "
                    "deploy/e2e ParameterSets (or remove). Clearing macros is enough "
                    "for preflight; removing the technicalConfigurationParameterSets "
                    "binding is a separate decision"
                ),
            }
        )

    if sets_clean:
        issues.append(
            {
                "kind": "technical_paramset_sets",
                "severity": "warning",
                "path": location,
                "sets": sets_clean,
                "setFiles": {n: set_files[n] for n in sets_clean},
                "message": (
                    "technicalConfigurationParameterSets is bound but ParameterSets "
                    "have no creds.get / #creds macros: "
                    + ", ".join(sets_clean)
                    + ". Safe to continue External Credentials YAML cutover; "
                    "decide later whether to keep or drop the technical binding"
                ),
                "suggested_action": (
                    "Continue migration. Optionally move sets to deployParameterSets "
                    "or remove the binding after confirming non-secret params"
                ),
            }
        )

    if unresolved:
        issues.append(
            {
                "kind": "technical_paramset_sets",
                "severity": "warning",
                "path": location,
                "sets": unresolved,
                "message": (
                    "Could not find ParameterSet files under templates/parameters for: "
                    + ", ".join(unresolved)
                ),
                "suggested_action": (
                    "Confirm the set name matches a file stem, or treat as manual review"
                ),
            }
        )

    return issues


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
                if len(params) >= 2:
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
    repo: Path | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            if key_str == TECHNICAL_PARAMSET_KEY:
                names: list[str] = []
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            names.append(item.strip())
                if names:
                    location = ".".join(path + (key_str,)) if path else key_str
                    issues.extend(
                        _technical_paramset_issues(
                            location=location, names=names, repo=repo
                        )
                    )
                continue
            child_tech = in_technical or key_str in TECHNICAL_KEYS
            issues.extend(
                find_macro_issues(
                    value,
                    path=path + (key_str,),
                    in_technical=child_tech,
                    repo=repo,
                )
            )
    elif isinstance(node, list):
        for i, item in enumerate(node):
            issues.extend(
                find_macro_issues(
                    item,
                    path=path + (str(i),),
                    in_technical=in_technical,
                    repo=repo,
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
                    "severity": "blocker",
                    "path": location,
                    "credId": match.group(1),
                    "message": (
                        "Credential macro in technicalConfigurationParameters "
                        "blocks External Credentials cutover "
                        "($type: credRef is not supported there)"
                    ),
                    "suggested_action": (
                        "Move to deployParameters/e2eParameters, remove if unused, "
                        "handle outside EnvGene, or defer cutover"
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
