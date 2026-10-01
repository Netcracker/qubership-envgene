"""Template repository — plan (descriptor-closure algorithm)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .classify import classify_cred, entry_fields
from .constants import TEMPLATE_ENV_TIER_PATH
from .macros import (
    BUILTIN_CRED_FIELDS,
    collect_cred_refs_excluding_runtime,
    collect_runtime_macro_hits,
    extract_cred_ids_from_mapping,
)
from .plan_schema import (
    add_source_group,
    empty_plan,
    merge_prior_plan_overrides,
    try_load_prior_plan,
)
from .yaml_io import open_yaml


def _try_open_yaml(path: Path) -> Any:
    """Load YAML; Jinja templates often fail the parser — treat as unreadable."""
    try:
        return open_yaml(path)
    except Exception:  # noqa: BLE001 — ruyaml ScannerError on {% %}
        return None


_PARAMSET_LIST_KEYS = (
    ("technicalConfigurationParameterSets", "technical"),
    ("deployParameterSets", "deploy_e2e"),
    ("e2eParameterSets", "deploy_e2e"),
)

_LIST_ITEM_NAME_RE = re.compile(
    r"""^\s*-\s*["']?([A-Za-z0-9_.-]+)["']?\s*$"""
)
_BUILTIN_CRED_LINE_RE = re.compile(
    r"""^\s*("""
    + "|".join(re.escape(k) for k in sorted(BUILTIN_CRED_FIELDS))
    + r""")\s*:\s*["']([^"']+)["']\s*$"""
)


def _descriptor_paths(repo: Path) -> list[Path]:
    base = repo / "templates" / "env_templates"
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.glob("*.yaml")) + sorted(base.glob("*.yml")):
        if p.parent != base:
            continue
        out.append(p)
    return out


def _resolve_descriptor_rel(repo: Path, rel: str) -> Path | None:
    """Map descriptor path string to a file under the template repo.

    EnvGene descriptors often use ``{{ templates_dir }}/...``; that placeholder
    resolves to the repo ``templates/`` directory.
    """
    cleaned = rel.strip().replace("\\", "/")
    cleaned = re.sub(r"\{\{\s*templates_dir\s*\}\}", "templates", cleaned)
    cleaned = cleaned.lstrip("/")
    if "{{" in cleaned or "}}" in cleaned:
        return None
    path = repo / cleaned
    return path if path.is_file() else None


def _follow_descriptor_refs(repo: Path, descriptor: dict[str, Any]) -> list[Path]:
    """Object files reachable from one Template Descriptor only."""
    paths: list[Path] = []
    for key in ("tenant", "cloud"):
        rel = descriptor.get(key)
        if isinstance(rel, str):
            resolved = _resolve_descriptor_rel(repo, rel)
            if resolved is not None:
                paths.append(resolved)
    cs = descriptor.get("composite_structure")
    if isinstance(cs, str):
        resolved = _resolve_descriptor_rel(repo, cs)
        if resolved is not None:
            paths.append(resolved)
    for ns in descriptor.get("namespaces") or []:
        if isinstance(ns, dict):
            tp = ns.get("template_path")
            if isinstance(tp, str):
                resolved = _resolve_descriptor_rel(repo, tp)
                if resolved is not None:
                    paths.append(resolved)
    # Preserve order, drop dupes
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _paramset_bindings_from_template(data: Any) -> tuple[set[str], set[str]]:
    """Return (deploy_or_e2e_names, technical_names) from object / template YAML."""
    deploy_e2e: set[str] = set()
    technical: set[str] = set()

    def add(target: set[str], val: Any) -> None:
        if isinstance(val, list):
            target.update(str(x) for x in val)
        elif isinstance(val, str):
            target.add(val)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, val in node.items():
                if key in ("deployParameterSets", "e2eParameterSets"):
                    add(deploy_e2e, val)
                elif key == "technicalConfigurationParameterSets":
                    add(technical, val)
                else:
                    walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return deploy_e2e, technical


def _paramset_names_from_template(data: Any) -> set[str]:
    """All bound paramset names (deploy + e2e + technical) for discovery."""
    deploy_e2e, technical = _paramset_bindings_from_template(data)
    return deploy_e2e | technical


def _paramset_names_for_macro_rewrite(data: Any) -> set[str]:
    """Paramsets whose macros may be rewritten (not technical-only bindings)."""
    deploy_e2e, _technical = _paramset_bindings_from_template(data)
    return deploy_e2e


def _text_bindings_from_file(path: Path) -> tuple[set[str], set[str], set[str]]:
    """Text pass for Jinja templates: paramset names + Built-in cred ids.

    Does not render Jinja. Collects list items from all ``{% if %}`` branches
    (union). Built-in fields: credentialsId / defaultCredentialsId / etc.
    """
    deploy_e2e: set[str] = set()
    technical: set[str] = set()
    builtins: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deploy_e2e, technical, builtins

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        bm = _BUILTIN_CRED_LINE_RE.match(line)
        if bm:
            builtins.add(bm.group(2))
            i += 1
            continue

        matched_target: set[str] | None = None
        for key, kind in _PARAMSET_LIST_KEYS:
            if key in line and ":" in line:
                matched_target = technical if kind == "technical" else deploy_e2e
                break
        if matched_target is None:
            i += 1
            continue
        i += 1
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            if (
                not stripped.startswith("-")
                and not stripped.startswith("{%")
                and not stripped.startswith("{{")
                and ":" in stripped
                and not stripped.startswith("'")
                and not stripped.startswith('"')
            ):
                break
            m = _LIST_ITEM_NAME_RE.match(raw)
            if m:
                matched_target.add(m.group(1))
            i += 1
    return deploy_e2e, technical, builtins


def _bindings_for_template_file(
    path: Path,
) -> tuple[set[str], set[str], dict[str, str]]:
    """YAML + text union for one template/object file in the descriptor closure."""
    deploy_e2e: set[str] = set()
    technical: set[str] = set()
    reachable: dict[str, str] = {}

    data = _try_open_yaml(path)
    if data is not None:
        de, tech = _paramset_bindings_from_template(data)
        deploy_e2e |= de
        technical |= tech
        reachable.update(collect_cred_refs_excluding_runtime(data))

    de_t, tech_t, builtins = _text_bindings_from_file(path)
    deploy_e2e |= de_t
    technical |= tech_t
    for cid in builtins:
        reachable.setdefault(cid, "secret")
    return deploy_e2e, technical, reachable


def _resolve_paramsets(repo: Path, names: set[str]) -> list[Path]:
    if not names:
        return []
    root = repo / "templates" / "parameters"
    if not root.is_dir():
        return []
    found: list[Path] = []
    seen: set[Path] = set()
    for path in list(root.rglob("*.yml")) + list(root.rglob("*.yaml")):
        if path in seen:
            continue
        data = open_yaml(path)
        if isinstance(data, dict) and str(data.get("name") or "") in names:
            found.append(path)
            seen.add(path)
    return found


def _iter_all_paramset_files(repo: Path) -> list[Path]:
    root = repo / "templates" / "parameters"
    if not root.is_dir():
        return []
    return sorted(set(list(root.rglob("*.yml")) + list(root.rglob("*.yaml"))))


def _ct_cred_ids(repo: Path, source_file: str) -> set[str]:
    path = repo / source_file
    if not path.is_file():
        return set()
    existing = open_yaml(path) or {}
    if not isinstance(existing, dict):
        return set()
    body = existing.get("credentials", existing)
    if not isinstance(body, dict):
        return set()
    out: set[str] = set()
    for cid, entry in body.items():
        if isinstance(entry, dict) and (
            "type" in entry or "remoteRefPath" in entry or "data" in entry
        ):
            out.add(str(cid))
    return out


def _repo_bound_paramset_names(repo: Path) -> set[str]:
    """All paramset names referenced from any Template Descriptor closure."""
    bound: set[str] = set()
    for desc_path in _descriptor_paths(repo):
        descriptor = open_yaml(desc_path) or {}
        for tf in _follow_descriptor_refs(repo, descriptor):
            de, tech, _ = _bindings_for_template_file(tf)
            bound |= de | tech
    return bound


def _find_unbound_paramsets(repo: Path) -> list[dict[str, Any]]:
    """ParameterSets never named from any descriptor closure (YAML + text).

    Informational only — apply does not rewrite, delete, or add these to CT.
    """
    bound = _repo_bound_paramset_names(repo)
    unbound: list[dict[str, Any]] = []
    for path in _iter_all_paramset_files(repo):
        data = open_yaml(path)
        if not isinstance(data, dict):
            continue
        name = str(data.get("name") or "").strip()
        if not name or name in bound:
            continue
        creds = extract_cred_ids_from_mapping(data)
        if not creds:
            continue
        unbound.append(
            {
                "path": str(path.relative_to(repo)).replace("\\", "/"),
                "name": name,
                "credIds": sorted(creds),
            }
        )
    return unbound


def build_template_plan(repo_root: Path) -> dict[str, Any]:
    """Build plan using descriptor-closure only; unbound ParameterSets and stale CT aside."""
    prior = try_load_prior_plan(cwd=repo_root)
    plan = empty_plan("template")
    stale_ct: list[dict[str, Any]] = []
    all_runtime_hits: list[dict[str, Any]] = []
    runtime_seen: set[tuple[str, str]] = set()
    plan_errors: list[str] = []
    all_technical_bound: set[str] = set()

    for desc_path in _descriptor_paths(repo_root):
        descriptor = open_yaml(desc_path) or {}
        stem = desc_path.stem
        source_file = f"templates/external-credentials/{stem}.yml.j2"

        reachable: dict[str, str] = {}
        template_files = _follow_descriptor_refs(repo_root, descriptor)
        if not template_files:
            plan_errors.append(
                f"descriptor {stem!r}: 0 reachable template files "
                "(check tenant/cloud/namespaces paths; "
                "{{ templates_dir }} should map to templates/)"
            )
        deploy_e2e_names: set[str] = set()
        technical_names: set[str] = set()

        for tf in template_files:
            de, tech, file_creds = _bindings_for_template_file(tf)
            deploy_e2e_names |= de
            technical_names |= tech
            reachable.update(file_creds)
            rel = str(tf.relative_to(repo_root)).replace("\\", "/")
            data = _try_open_yaml(tf)
            if data is not None:
                for row in collect_runtime_macro_hits(data, file_path=rel):
                    key = (row["file"], row["credId"])
                    if key not in runtime_seen:
                        runtime_seen.add(key)
                        all_runtime_hits.append(row)

        all_technical_bound |= technical_names

        for pf in _resolve_paramsets(repo_root, deploy_e2e_names):
            data = open_yaml(pf)
            if data is not None:
                reachable.update(collect_cred_refs_excluding_runtime(data))

        for pf in _resolve_paramsets(repo_root, technical_names):
            data = open_yaml(pf)
            if data is None:
                continue
            rel = str(pf.relative_to(repo_root)).replace("\\", "/")
            # Paramset files are flat (parameters:/params:) — no wrapper key;
            # binding via technicalConfigurationParameterSets makes the body runtime.
            body = data
            if isinstance(data, dict):
                body = data.get("parameters") or data.get("params") or data
            for row in collect_runtime_macro_hits(
                body,
                file_path=rel,
                source="technicalConfigurationParameterSets",
                assume_runtime=True,
            ):
                key = (row["file"], row["credId"])
                if key not in runtime_seen:
                    runtime_seen.add(key)
                    all_runtime_hits.append(row)

        # Existing CT must not inflate reachable — report stale ids instead
        for cid in sorted(_ct_cred_ids(repo_root, source_file) - set(reachable)):
            stale_ct.append(
                {
                    "sourceFile": source_file,
                    "credId": cid,
                    "note": (
                        "present in Credential Template but not reachable from "
                        "this descriptor closure — will be dropped on apply unless "
                        "you add it to the plan with includeInCredentialTemplate: true"
                    ),
                }
            )

        to_review: dict[str, Any] = {}
        to_confirm: dict[str, Any] = {}
        for cred_id in sorted(reachable):
            clf = classify_cred(
                cred_id,
                tier_from_location="env",
                default_path=TEMPLATE_ENV_TIER_PATH,
                default_create=True,
                template_mode=True,
            )
            fields = entry_fields(clf, instance=False)
            # Always include reachable creds in the Credential Template by default.
            # Operator may still set includeInCredentialTemplate: false in the plan
            # to exclude a specific id; apply honors that.
            fields["includeInCredentialTemplate"] = True
            if clf.to_review:
                to_review[cred_id] = fields
            else:
                to_confirm[cred_id] = fields

        add_source_group(
            plan, source_file, to_review=to_review, to_confirm=to_confirm
        )

    plan["unbound_parameter_sets"] = _find_unbound_paramsets(repo_root)
    plan["stale_credential_template_entries"] = stale_ct
    plan["runtime_credential_macros"] = all_runtime_hits
    plan["technical_bound_parameter_sets"] = sorted(all_technical_bound)
    if plan_errors:
        plan["plan_errors"] = plan_errors
    merge_prior_plan_overrides(plan, prior)
    return plan
