"""Template Repository helpers. Shared macro/YAML logic lives in extcreds_mig."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_SHARED = Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from extcreds_mig.constants import (  # noqa: E402
    CREDS_GET_RE,
    DEFAULT_SECRET_STORE,
    DEFAULT_TEMPLATE_PATH,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    HASH_CREDS_RE,
    NAMESPACE_JINJA,
    PROVIDER_MARKERS,
    TECHNICAL_KEYS,
)
from extcreds_mig.emit import emit  # noqa: E402
from extcreds_mig.macros import (  # noqa: E402
    base_external_entry,
    find_macro_issues,
    find_remaining_macros,
    heuristic_provider_markers,
    path_contains_cred_id,
    walk_replace_macros,
)
from extcreds_mig.yaml_io import dump_yaml, load_yaml, strip_jinja2_for_yaml  # noqa: E402

# Back-compat alias used by smoke tests
_strip_jinja2_for_yaml = strip_jinja2_for_yaml

EXIT_AMBIGUOUS = EXIT_NEEDS_INPUT
PARAMSET_KEYS = ("deployParameterSets", "e2eParameterSets")
SKIP_PARAMSET_KEYS = frozenset({"technicalConfigurationParameterSets"})

__all__ = [
    "CREDS_GET_RE",
    "DEFAULT_SECRET_STORE",
    "DEFAULT_TEMPLATE_PATH",
    "EXIT_AMBIGUOUS",
    "EXIT_ERROR",
    "EXIT_NEEDS_INPUT",
    "EXIT_OK",
    "HASH_CREDS_RE",
    "NAMESPACE_JINJA",
    "PARAMSET_KEYS",
    "PROVIDER_MARKERS",
    "SKIP_PARAMSET_KEYS",
    "TECHNICAL_KEYS",
    "base_external_entry",
    "collect_cred_evidence",
    "collect_paramset_names",
    "collect_paramset_names_from_text",
    "dump_yaml",
    "emit",
    "find_descriptors",
    "find_macro_issues",
    "find_remaining_macros",
    "heuristic_provider_markers",
    "list_credential_scan_files",
    "list_parameter_files",
    "load_yaml",
    "path_contains_cred_id",
    "resolve_descriptor_paths",
    "templates_dir_to_path",
    "walk_replace_macros",
]


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
            if path.suffix in (".yml", ".yaml") and ".j2" not in path.name:
                try:
                    doc = load_yaml(path)
                except Exception:  # noqa: BLE001
                    continue
                if isinstance(doc, dict) and (
                    "cloud" in doc or "tenant" in doc or "namespaces" in doc
                ):
                    found.append(path)
    return sorted(set(found))


def templates_dir_to_path(repo: Path, value: str) -> Path | None:
    """Resolve a ``{{ templates_dir }}/...`` descriptor path to a repo Path."""
    if not isinstance(value, str) or "{{ templates_dir }}" not in value:
        return None
    rel = value.replace("{{ templates_dir }}", "templates").replace("\\", "/")
    return repo / rel


def collect_paramset_names(node: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            if key_str in SKIP_PARAMSET_KEYS:
                continue
            if key_str in PARAMSET_KEYS and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        names.add(item)
            names |= collect_paramset_names(value)
    elif isinstance(node, list):
        for item in node:
            names |= collect_paramset_names(item)
    return names


def collect_paramset_names_from_text(content: str, *, strip_jinja: bool = False) -> set[str]:
    """Collect ParameterSet names from raw YAML/Jinja text.

    After Jinja block lines are stripped, if/elif branches often leave duplicate
    deployParameterSets keys; YAML loaders keep only the last one. Scanning the
    stripped text unions names from every branch.
    """
    if strip_jinja:
        content = strip_jinja2_for_yaml(content)
    names: set[str] = set()
    active_key: str | None = None
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.endswith(":") and stripped[:-1] in PARAMSET_KEYS:
            active_key = stripped[:-1]
            continue
        if active_key is not None:
            item_match = re.match(r"^-\s+(.+)$", stripped)
            if item_match:
                item = item_match.group(1).strip().strip('"').strip("'")
                if item:
                    names.add(item)
                continue
            if stripped == "":
                continue
            if not line[:1].isspace():
                active_key = None
    return names


def list_parameter_files(repo: Path) -> list[Path]:
    params_root = repo / "templates" / "parameters"
    if not params_root.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(params_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in (".yml", ".yaml") or path.name.endswith(".j2"):
            files.append(path)
    return files


def resolve_descriptor_paths(repo: Path, descriptor: Path) -> dict[str, Any]:
    doc = load_yaml(descriptor) or {}
    missing: list[str] = []
    template_files: list[Path] = []
    credential_template: Path | None = None

    for key in ("tenant", "cloud"):
        val = doc.get(key)
        if isinstance(val, str) and "{{ templates_dir }}" in val:
            path = templates_dir_to_path(repo, val)
            if path is None or not path.is_file():
                missing.append(val)
            else:
                template_files.append(path)

    for ns in doc.get("namespaces") or []:
        if not isinstance(ns, dict):
            continue
        val = ns.get("template_path")
        if isinstance(val, str) and "{{ templates_dir }}" in val:
            path = templates_dir_to_path(repo, val)
            if path is None or not path.is_file():
                missing.append(val)
            else:
                template_files.append(path)

    ect = doc.get("external_credential_template")
    if isinstance(ect, str) and "{{ templates_dir }}" in ect:
        path = templates_dir_to_path(repo, ect)
        if path is None or not path.is_file():
            missing.append(ect)
        else:
            credential_template = path

    return {
        "descriptor_doc": doc,
        "template_files": template_files,
        "credential_template": credential_template,
        "missing": missing,
        "has_external_credential_template_field": isinstance(ect, str) and bool(ect),
    }


def list_credential_scan_files(
    repo: Path,
    descriptor: Path,
    *,
    include_credential_template: bool = False,
) -> list[Path]:
    """Cloud/Tenant/Namespace templates plus every ParameterSet file."""
    resolved = resolve_descriptor_paths(repo, descriptor)
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in resolved["template_files"]:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    for path in list_parameter_files(repo):
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    if include_credential_template and resolved["credential_template"] is not None:
        ct = resolved["credential_template"]
        if ct not in seen:
            ordered.append(ct)
    return ordered


def collect_cred_evidence(
    node: Any, *, path: tuple[str, ...] = (), in_technical: bool = False
) -> dict[str, dict]:
    """credId -> shapes/locations/technical flags."""
    bag: dict[str, dict] = {}

    def add(cred_id: str, shape: str | None, loc: str, technical: bool) -> None:
        item = bag.setdefault(
            cred_id,
            {
                "shapes": set(),
                "locations": [],
                "seen_technical": False,
                "seen_non_technical": False,
            },
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
            if key_str in (
                "credentialsId",
                "defaultCredentialsId",
                "tokenSecret",
                "credential",
            ) and isinstance(value, str) and not value.startswith("{{"):
                parent = path[-1] if path else ""
                shape = None
                if key_str == "defaultCredentialsId":
                    shape = None
                elif parent == "maasConfig" or "dbaas" in parent.lower():
                    shape = "multi_field"
                elif (
                    key_str == "tokenSecret"
                    or parent in ("vaultConfig", "consulConfig")
                    or key_str in ("credentialsId", "credential")
                ):
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
                dest["seen_non_technical"] = (
                    dest["seen_non_technical"] or meta["seen_non_technical"]
                )
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
                dest["seen_non_technical"] = (
                    dest["seen_non_technical"] or meta["seen_non_technical"]
                )
    elif isinstance(node, str):
        m = CREDS_GET_RE.search(node)
        if m:
            prop = m.group(2)
            shape = "single_value" if prop == "secret" else "multi_field"
            add(m.group(1), shape, ".".join(path), in_technical)
    return bag
