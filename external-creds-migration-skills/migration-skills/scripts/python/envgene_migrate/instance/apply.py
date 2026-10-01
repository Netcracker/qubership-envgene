"""Instance repository — apply."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .external_creds import (
    build_normalized_secret_name,
    build_vals_uri,
    provision_data_payload,
)
from .macros import (
    ANY_VALUE_MACRO_RE,
    HASH_KEY_RE,
    CompositeMacroError,
    surgical_rewrite_consumer_file,
    strip_inventory_deployer_in_env_definitions,
    strip_shared_master_extensions_in_env_definitions,
)
from .plan_schema import iter_plan_entries
from ..preflight import PreflightError
from .store_preflight import (
    load_default_store,
    require_sops_key_if_needed,
    require_store_env,
)
from .reports import progress
from .rewrite_creds import (
    UnsupportedCredTypeError,
    extract_plaintext_for_store,
    is_null_placeholder,
    to_external_entry,
)
from .validate_plan import validate_plan_entries
from .verify_post import VerifyError, run_verification
from .yaml_io import open_yaml, try_decrypt_cred_file, write_yaml
from .plan import check_mixed_types_in_file
from .store_invoke import run_provision, success_status


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


def _file_looks_sops(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(line.startswith("sops:") for line in reversed(text.splitlines()[-30:]))


def _load_source_entry(repo: Path, source_file: str, cred_id: str) -> dict[str, Any]:
    path = repo / source_file
    data = try_decrypt_cred_file(path) or open_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"[{cred_id}] FAILED: cannot read source {source_file}")
    body = data.get("credentials", data)
    if not isinstance(body, dict) or cred_id not in body:
        raise ValueError(
            f"[{cred_id}] FAILED: cred-id not present in source file at apply time ({source_file})"
        )
    entry = body[cred_id]
    if not isinstance(entry, dict):
        raise ValueError(f"[{cred_id}] FAILED: invalid entry in {source_file}")
    return entry


def _write_source_entry(
    repo: Path, source_file: str, cred_id: str, new_entry: dict[str, Any]
) -> None:
    path = repo / source_file
    data = open_yaml(path) or {}
    if not isinstance(data, dict):
        data = {}
    if "credentials" in data and isinstance(data["credentials"], dict):
        data["credentials"][cred_id] = new_entry
    else:
        data[cred_id] = new_entry
    write_yaml(path, data)


def _consumer_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in (
        "environments/**/cloud-passport/*.yml",
        "environments/**/cloud-passport/*.yaml",
        "environments/**/Inventory/parameters/*.yml",
        "environments/**/parameters/*.yml",
        "environments/parameters/*.yml",
        "configuration/integration.yml",
        "configuration/registry.yml",
        "configuration/deployer.yml",
        "environments/**/app-deployer/deployer.yml",
        "environments/**/cloud.yml",
        "environments/**/Applications/*.yml",
    ):
        files.extend(p for p in repo.glob(pattern) if p.is_file())
    # skip *-creds
    return [
        p
        for p in files
        if not p.name.endswith("-creds.yml") and not p.name.endswith("-creds.yaml")
    ]


def _consumer_rewrite_mode(path: Path) -> str:
    """unrestricted = whole file except technicalConfigurationParameters."""
    norm = str(path).replace("\\", "/")
    name = path.name
    if "/cloud-passport/" in norm:
        return "unrestricted"
    if name in ("integration.yml", "registry.yml", "deployer.yml"):
        return "unrestricted"
    return "restricted"


def require_instance_apply_gate(plan: dict[str, Any]) -> None:
    """Refuse apply when runtime macros remain (unless waived) or delete flags unset."""
    runtime = plan.get("runtime_credential_macros") or []
    decisions = plan.get("operator_decisions") or {}
    if runtime and not decisions.get("technical_macros_waive"):
        raise PreflightError(
            f"runtime_credential_macros still present ({len(runtime)} hit(s)). "
            "Reply A (set operator_decisions.technical_macros_waive: true) if the "
            "Template is already updated, or Reply B: remove the macros yourself "
            "and re-plan. Apply is blocked until then (GATE)."
        )
    deletes = plan.get("to_delete") or {}
    deployer = deletes.get("deployer_credentials") or []
    if deployer and "deployer_delete" not in decisions:
        raise PreflightError(
            f"{len(deployer)} app-deployer/*-creds.yml listed under to_delete. "
            "Set operator_decisions.deployer_delete: true (delete on apply) or "
            "false (keep files; pipeline may fail) in migration-plan.yaml, then re-run apply."
        )
    if deployer and decisions.get("deployer_delete") is False:
        deletes = dict(deletes)
        deletes["deployer_credentials"] = []
        plan["to_delete"] = deletes
    unused = deletes.get("unused_shared_credentials") or []
    if unused and "unused_shared_delete" not in decisions:
        raise PreflightError(
            f"{len(unused)} unused shared credential file(s) listed under "
            "to_delete. Set operator_decisions.unused_shared_delete: true "
            "(delete on apply) or false (keep files) in migration-plan.yaml, "
            "then re-run apply."
        )
    if unused and decisions.get("unused_shared_delete") is False:
        deletes = dict(deletes)
        deletes["unused_shared_credentials"] = []
        plan["to_delete"] = deletes


def _flatten_to_delete(plan: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for _group, items in (plan.get("to_delete") or {}).items():
        if isinstance(items, list):
            out.extend(str(x) for x in items)
    return out


def apply_instance_plan(
    repo_root: Path,
    plan: dict[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    warnings, errors = validate_plan_entries(plan)
    for w in warnings:
        progress(f"[warn] {w}", force=True)
    if errors:
        raise ValueError("; ".join(errors))

    require_instance_apply_gate(plan)

    # Re-check source files for mixed local+external before Store/Git writes
    seen_src: set[str] = set()
    for src, _b, _cid, _f in iter_plan_entries(plan):
        if src in seen_src:
            continue
        seen_src.add(src)
        mixed = check_mixed_types_in_file(repo_root / src, src)
        if mixed:
            raise ValueError("; ".join(mixed))

    store = load_default_store(repo_root)
    store_type = (store.get("type") or "vault").lower()
    if store_type == "openbao":
        store_type = "vault"

    # Product provision context: credentials.<id>.{vals,strategy,data}
    provision_map: dict[str, Any] = {}
    pending_git: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = []
    # (source, cred_id, fields, source_entry)
    sops_seen = False

    for src, _b, cred_id, fields in iter_plan_entries(plan):
        src_path = repo_root / src
        if _file_looks_sops(src_path):
            sops_seen = True
        source_entry = _load_source_entry(repo_root, src, cred_id)
        if source_entry.get("type") == "external":
            raise ValueError(
                f"[{cred_id}] FAILED: source already type: external (partial migration)"
            )
        pending_git.append((src, cred_id, fields, source_entry))
        write_store = fields.get("writeToStore", True) is True
        data = extract_plaintext_for_store(source_entry)
        if write_store and is_null_placeholder(data):
            progress(
                f"[{cred_id}] warn: envgeneNullValue — skip Store write",
                force=True,
            )
            write_store = False
        if write_store:
            rrp = str(fields["remoteRefPath"])
            try:
                norm = build_normalized_secret_name(rrp, cred_id, store_type)
                vals = build_vals_uri(store, norm)
            except ValueError as exc:
                raise ValueError(f"[{cred_id}] FAILED: {exc}") from exc
            provision_map[cred_id] = {
                "vals": vals,
                "strategy": "overwrite",
                "data": provision_data_payload(data),
            }

    require_sops_key_if_needed(sops_seen)
    if provision_map:
        require_store_env(store)

    statuses: dict[str, str] = {}
    if provision_map:
        context = {"credentials": provision_map}
        statuses = run_provision(context=context, dry_run=dry_run)

    store_ok = store_fail = 0
    git_ok = git_fail = 0
    touched_creds: list[Path] = []
    warnings_out: list[str] = []

    # Cross-source same cred-id different values warning
    by_id: dict[str, list[str]] = defaultdict(list)
    for src, cred_id, _f, _e in pending_git:
        by_id[cred_id].append(src)
    for cred_id, srcs in by_id.items():
        if len(srcs) > 1:
            warnings_out.append(
                f"{cred_id}: same cred-id in multiple sources ({', '.join(srcs)}); "
                "each written to its own path"
            )

    for src, cred_id, fields, source_entry in pending_git:
        write_store = fields.get("writeToStore", True) is True
        if write_store and is_null_placeholder(source_entry.get("data")):
            write_store = False
        if write_store and cred_id in provision_map:
            st = statuses.get(cred_id, "")
            if dry_run and not st:
                st = "dry_run_ok"
            if not success_status(st) and st != "":
                store_fail += 1
                progress(
                    f"[{cred_id}] FAILED: store outcome={st}",
                    force=True,
                )
                git_fail += 1
                continue
            if st == "" and not dry_run:
                # CLI ran but no per-cred line — treat as fail
                store_fail += 1
                progress(
                    f"[{cred_id}] FAILED: no provision outcome line for cred",
                    force=True,
                )
                git_fail += 1
                continue
            store_ok += 1
        if dry_run:
            progress(f"[{cred_id}] dry-run: skip Git rewrite")
            continue
        try:
            new_entry = to_external_entry(
                cred_id,
                source_entry,
                remote_ref_path=str(fields["remoteRefPath"]),
                create=fields.get("create"),
            )
            _write_source_entry(repo_root, src, cred_id, new_entry)
            touched_creds.append(repo_root / src)
            git_ok += 1
            progress(f"git: {src} [{cred_id}]")
        except (UnsupportedCredTypeError, ValueError) as exc:
            progress(str(exc), force=True)
            git_fail += 1

    macro_ok = macro_fail = 0
    touched_consumers: list[Path] = []
    if not dry_run:
        for cf in _consumer_files(repo_root):
            try:
                mode = _consumer_rewrite_mode(cf)
                c = surgical_rewrite_consumer_file(cf, mode=mode)
            except CompositeMacroError as exc:
                progress(str(exc), force=True)
                macro_fail += 1
                raise ValueError(str(exc)) from exc
            if (
                c == 0
                and mode == "restricted"
                and _file_has_cred_macros(cf)
            ):
                progress(
                    f"[warn] macros found but not inside a recognized root key "
                    f"(parameters / deployParameters / e2eParameters) — check spelling: {cf}",
                    force=True,
                )
            if c:
                touched_consumers.append(cf)
                macro_ok += c
                progress(f"macros: {cf} ({c})")

        sm = strip_shared_master_extensions_in_env_definitions(repo_root)
        if sm:
            progress(f"sharedMasterCredentialFiles: stripped .yml extension ({sm})")

        decisions = plan.get("operator_decisions") or {}
        deployer_rels = list(
            (plan.get("to_delete") or {}).get("deployer_credentials") or []
        )
        if deployer_rels and decisions.get("deployer_delete") is True:
            dep_stripped = strip_inventory_deployer_in_env_definitions(
                repo_root, deployer_rels
            )
            if dep_stripped:
                progress(
                    f"inventory.deployer: removed from env_definition ({dep_stripped})"
                )

        for rel in _flatten_to_delete(plan):
            path = repo_root / rel
            if path.is_file():
                path.unlink()
                progress(f"delete: {rel}")

        try:
            run_verification(
                repo_root=repo_root,
                touched_cred_files=list(dict.fromkeys(touched_creds)),
                touched_consumer_files=touched_consumers,
                to_delete=_flatten_to_delete(plan),
            )
        except VerifyError as exc:
            raise ValueError("verification failed: " + "; ".join(exc.issues)) from exc

    return {
        "store_ok": store_ok,
        "store_fail": store_fail,
        "git_ok": git_ok,
        "git_fail": git_fail,
        "macro_ok": macro_ok,
        "macro_fail": macro_fail,
        "warnings": warnings_out,
    }
