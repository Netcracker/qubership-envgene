"""Template repository — apply (descriptor-closure; no Store)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .macros import (
    ANY_VALUE_MACRO_RE,
    HASH_KEY_RE,
    CompositeMacroError,
    collect_cred_refs_excluding_runtime,
    surgical_rewrite_consumer_file,
)
from .plan_schema import iter_plan_entries
from .reports import progress
from .rewrite_creds import to_external_entry
from .validate_plan import validate_plan_entries
from .verify_post import VerifyError, run_verification
from .yaml_io import open_yaml, write_yaml
from .plan import (
    _bindings_for_template_file,
    _descriptor_paths,
    _follow_descriptor_refs,
    _resolve_paramsets,
    _try_open_yaml,
)

_UP_PROPS = [{"name": "username"}, {"name": "password"}]

_DESCRIPTOR_ECT_RE = re.compile(
    r"(?m)^\s*external_credential_template\s*:",
)


def _merge_inferred_type(into: dict[str, str], cid: str, cred_type: str) -> None:
    """Prefer usernamePassword over secret; never downgrade."""
    if cred_type == "usernamePassword":
        into[cid] = "usernamePassword"
    else:
        into.setdefault(cid, cred_type or "secret")


def _collect_consumer_inferred_types(repo: Path) -> dict[str, str]:
    """Scan descriptor closure (same paths as macro rewrite) for field usage.

    Returns credId → usernamePassword | secret. Used only to decide whether CT
    entries need ``properties``; does not rewrite consumers.
    """
    inferred: dict[str, str] = {}
    for desc_path in _descriptor_paths(repo):
        descriptor = open_yaml(desc_path) or {}
        rewrite_names: set[str] = set()
        for tf in _follow_descriptor_refs(repo, descriptor):
            de, _tech, file_creds = _bindings_for_template_file(tf)
            rewrite_names |= de
            for cid, t in file_creds.items():
                _merge_inferred_type(inferred, cid, t)
        for pf in _resolve_paramsets(repo, rewrite_names):
            data = open_yaml(pf)
            if data is None:
                continue
            for cid, t in collect_cred_refs_excluding_runtime(data).items():
                _merge_inferred_type(inferred, cid, t)
    return inferred


def _resolve_inferred_type(
    prior: dict[str, Any],
    consumer_type: str | None,
) -> str:
    """Prior/data first; consumer may upgrade secret → usernamePassword only."""
    inferred = "secret"
    if prior.get("type") in ("usernamePassword", "secret"):
        inferred = str(prior.get("type"))
    elif prior.get("data"):
        data = prior.get("data")
        inferred = (
            "usernamePassword"
            if isinstance(data, dict)
            and ("username" in data or "password" in data)
            else "secret"
        )
    if consumer_type == "usernamePassword":
        return "usernamePassword"
    return inferred


def _ensure_cred_template(
    repo: Path,
    source_file: str,
    entries: dict[str, dict[str, Any]],
    *,
    consumer_inferred: dict[str, str] | None = None,
) -> Path:
    """Rewrite Credential Template to exactly the included plan entries (no leftovers)."""
    path = repo / source_file
    existing = open_yaml(path) if path.is_file() else {}
    wrapped = (
        isinstance(existing, dict)
        and "credentials" in existing
        and isinstance(existing.get("credentials"), dict)
    )
    by_consumer = consumer_inferred or {}

    new_body: dict[str, Any] = {}
    for cred_id, fields in entries.items():
        if fields.get("includeInCredentialTemplate", True) is False:
            progress(
                f"[{cred_id}] skip CT write (includeInCredentialTemplate: false)"
            )
            continue
        prior: dict[str, Any] = {}
        if isinstance(existing, dict):
            root = existing["credentials"] if wrapped else existing
            if isinstance(root, dict) and isinstance(root.get(cred_id), dict):
                prior = root[cred_id]
        inferred = _resolve_inferred_type(prior, by_consumer.get(cred_id))
        create = fields.get("create")
        if prior.get("type") == "external":
            kept = dict(prior)
            kept["remoteRefPath"] = str(fields["remoteRefPath"])
            if create is not None:
                kept["create"] = create
            # Re-apply: fill missing properties only; never strip existing ones.
            if "properties" not in kept and inferred == "usernamePassword":
                kept["properties"] = [dict(p) for p in _UP_PROPS]
            new_body[cred_id] = kept
            continue
        new_body[cred_id] = to_external_entry(
            cred_id,
            prior if prior else {"type": inferred},
            remote_ref_path=str(fields["remoteRefPath"]),
            create=create if create is not None else True,
            inferred_type=inferred,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    if wrapped:
        out = dict(existing)
        out["credentials"] = new_body
        write_yaml(path, out)
    else:
        write_yaml(path, new_body)
    return path


def _descriptor_ct_path(ct_rel: str) -> str:
    """Repo-relative CT path → descriptor value with {{ templates_dir }}.

    On disk: templates/external-credentials/<stem>.yml.j2
    In descriptor (env-build resolves templates_dir): 
    {{ templates_dir }}/external-credentials/<stem>.yml.j2
    """
    rel = ct_rel.replace("\\", "/").strip()
    prefix = "templates/"
    if rel.startswith(prefix):
        rel = rel[len(prefix) :]
    return "{{ templates_dir }}/" + rel.lstrip("/")


def _update_descriptor(repo: Path, stem: str, ct_rel: str) -> Path | None:
    """Set external_credential_template by text append — do not dump the descriptor."""
    ect_value = _descriptor_ct_path(ct_rel)
    for ext in (".yaml", ".yml"):
        dpath = repo / "templates" / "env_templates" / f"{stem}{ext}"
        if not dpath.is_file():
            continue
        text = dpath.read_text(encoding="utf-8")
        if _DESCRIPTOR_ECT_RE.search(text):
            return dpath
        if text and not text.endswith(("\n", "\r")):
            text += "\n"
        # Quote path so values with spaces stay valid YAML.
        text += f'external_credential_template: "{ect_value}"\n'
        dpath.write_text(text, encoding="utf-8", newline="")
        progress(f"descriptor: {dpath} +external_credential_template")
        return dpath
    return None


def _file_has_cred_macros(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if ANY_VALUE_MACRO_RE.search(text):
        return True
    for line in text.splitlines():
        key = line.split(":", 1)[0].strip()
        if HASH_KEY_RE.match(key):
            return True
    return False


def _surgical_macros_parseable(path: Path) -> int:
    """A2: surgical rewrite only if YAML parse succeeds; else warn and skip."""
    data = _try_open_yaml(path)
    if data is None:
        if path.is_file() and _file_has_cred_macros(path):
            progress(
                f"[warn] skip macros (unparseable YAML/Jinja; fix by hand): {path}",
                force=True,
            )
        return 0
    try:
        count = surgical_rewrite_consumer_file(path, mode="restricted")
    except CompositeMacroError as exc:
        raise ValueError(str(exc)) from exc
    if count == 0 and _file_has_cred_macros(path):
        progress(
            f"[warn] macros found but not inside a recognized root key "
            f"(parameters / deployParameters / e2eParameters) — check spelling: {path}",
            force=True,
        )
    return count


def apply_template_plan(repo_root: Path, plan: dict[str, Any]) -> dict[str, int]:
    warnings, errors = validate_plan_entries(plan)
    for w in warnings:
        progress(f"[warn] {w}")
    if errors:
        raise ValueError("; ".join(errors))

    by_source: dict[str, dict[str, Any]] = {}
    for src, _b, cred_id, fields in iter_plan_entries(plan):
        by_source.setdefault(src, {})[cred_id] = fields

    # Unbound ParameterSets: informational only — never rewrite / delete / CT.

    touched_creds: list[Path] = []
    touched_consumers: list[Path] = []
    macro_ok = 0
    git_ok = 0
    deleted_rels: list[str] = []

    # Before CT write: infer usernamePassword from consumer macros / credRef.
    consumer_inferred = _collect_consumer_inferred_types(repo_root)

    for src, entries in by_source.items():
        progress(f"credential template: {src}")
        ct = _ensure_cred_template(
            repo_root, src, entries, consumer_inferred=consumer_inferred
        )
        touched_creds.append(ct)
        git_ok += 1
        name = Path(src).name
        if name.endswith(".yml.j2"):
            desc_stem = name[: -len(".yml.j2")]
        else:
            desc_stem = Path(src).stem
        _update_descriptor(repo_root, desc_stem, src)

    # Macros: descriptor closure; technicalConfigurationParameters not rewritten;
    # paramsets bound only via technicalConfigurationParameterSets not rewritten.
    # A2: surgical text rewrite when YAML parses; unparseable Jinja → warn, no write.
    for desc_path in _descriptor_paths(repo_root):
        descriptor = open_yaml(desc_path) or {}
        files = _follow_descriptor_refs(repo_root, descriptor)
        rewrite_names: set[str] = set()
        for tf in files:
            de, _tech, _creds = _bindings_for_template_file(tf)
            rewrite_names |= de
            c = _surgical_macros_parseable(tf)
            if c:
                touched_consumers.append(tf)
                macro_ok += c
                progress(f"macros: {tf} ({c})")
        for pf in _resolve_paramsets(repo_root, rewrite_names):
            c = _surgical_macros_parseable(pf)
            if c:
                touched_consumers.append(pf)
                macro_ok += c
                progress(f"macros: {pf} ({c})")

    try:
        run_verification(
            repo_root=repo_root,
            touched_cred_files=touched_creds,
            touched_consumer_files=touched_consumers,
            to_delete=deleted_rels,
        )
    except VerifyError as exc:
        raise ValueError("verification failed: " + "; ".join(exc.issues)) from exc

    return {"git_ok": git_ok, "macro_ok": macro_ok, "store_ok": 0}
