"""Instance repository — plan."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constants import GLOBAL_PATH
from .plan_schema import (
    add_source_group,
    empty_plan,
    iter_plan_entries,
    merge_prior_plan_overrides,
    try_load_prior_plan,
)
from .rewrite_creds import is_null_placeholder
from .runtime_scan import scan_instance_runtime_macros
from .yaml_io import open_yaml, try_decrypt_cred_file
from .orphans import _iter_shared_files, find_orphaned_shared_files

# Cyrillic (and other letters in Cyrillic block) in credential paths → hard fail.
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

SourceKind = str  # passport | system | env | shared


def _passport_cred_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    env_root = repo / "environments"
    if not env_root.is_dir():
        return out
    for cluster in sorted(p for p in env_root.iterdir() if p.is_dir()):
        cp = cluster / "cloud-passport"
        if not cp.is_dir():
            continue
        out.extend(sorted(cp.glob("*-creds.yml")))
        out.extend(sorted(cp.glob("*-creds.yaml")))
    return out


def _system_cred_files(repo: Path) -> list[Path]:
    conf = repo / "configuration" / "credentials"
    out: list[Path] = []
    if conf.is_dir():
        out.extend(sorted(conf.glob("*.yml")))
        out.extend(sorted(conf.glob("*.yaml")))
    return out


def _parse_cluster_env(rel: str) -> tuple[str, str | None]:
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "environments":
        cluster = parts[1]
        # Repo-level shared: environments/shared-credentials/<file> — no env segment
        if cluster == "shared-credentials":
            return "shared-credentials", None
        env = None
        if len(parts) >= 3 and parts[2] not in (
            "credentials",
            "shared-credentials",
            "cloud-passport",
            "parameters",
            "app-deployer",
        ):
            env = parts[2]
        return cluster, env
    return "unknown", None


def _source_kind(rel: str) -> SourceKind:
    norm = rel.replace("\\", "/")
    if "/cloud-passport/" in norm and norm.endswith(("-creds.yml", "-creds.yaml")):
        return "passport"
    if norm.startswith("configuration/credentials/"):
        return "system"
    if "/Inventory/credentials/" in norm:
        return "env"
    return "shared"


def _path_and_create(
    kind: SourceKind, cluster: str, env: str | None
) -> tuple[str, bool | None]:
    """Suggested remoteRefPath and create (no leading slash)."""
    if kind == "passport":
        return f"{cluster}", False
    if kind == "system":
        return GLOBAL_PATH, False
    if kind == "env":
        return (f"{cluster}/{env}" if env else f"{cluster}"), True
    # shared: env-scoped → {cluster}/{env}, create true;
    # cluster-level (environments/{cluster}/shared-credentials) → {cluster}, create false;
    # repo-level (environments/shared-credentials) → global, create false
    if env:
        return f"{cluster}/{env}", True
    if cluster in ("shared-credentials", "unknown"):
        return GLOBAL_PATH, False
    return f"{cluster}", False


def _entries_from_cred_file(path: Path) -> dict[str, dict[str, Any]]:
    data = try_decrypt_cred_file(path) or open_yaml(path) or {}
    if not isinstance(data, dict):
        return {}
    body = data.get("credentials", data)
    if not isinstance(body, dict):
        return {}
    out = {}
    for cid, entry in body.items():
        if isinstance(entry, dict) and ("type" in entry or "data" in entry):
            out[str(cid)] = entry
    return out


def _generated_and_deployer_deletes(repo: Path) -> dict[str, list[str]]:
    generated: list[str] = []
    deployer: list[str] = []
    env_root = repo / "environments"
    if not env_root.is_dir():
        return {
            "generated_env_credentials": generated,
            "deployer_credentials": deployer,
        }

    def _add_deployer_creds(app_dep: Path) -> None:
        if not app_dep.is_dir():
            return
        for p in sorted(app_dep.glob("*-creds.yml")) + sorted(
            app_dep.glob("*-creds.yaml")
        ):
            if p.is_file():
                deployer.append(str(p.relative_to(repo)).replace("\\", "/"))

    for cluster in sorted(p for p in env_root.iterdir() if p.is_dir()):
        if cluster.name in ("credentials", "shared-credentials"):
            continue
        # Cluster-level: environments/<cluster>/app-deployer/*-creds.yml
        _add_deployer_creds(cluster / "app-deployer")
        for env_dir in sorted(p for p in cluster.iterdir() if p.is_dir()):
            gen = env_dir / "Credentials" / "credentials.yml"
            if gen.is_file():
                generated.append(str(gen.relative_to(repo)).replace("\\", "/"))
            # Legacy env-level app-deployer
            _add_deployer_creds(env_dir / "app-deployer")
    # Deduplicate while preserving order
    deployer = list(dict.fromkeys(deployer))
    return {
        "generated_env_credentials": generated,
        "deployer_credentials": deployer,
    }


def _parse_env_filter(env_filter: str | None) -> tuple[str, str] | None:
    if not env_filter:
        return None
    parts = env_filter.replace("\\", "/").strip().split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"--env must be CLUSTER/ENV (got {env_filter!r})"
        )
    return parts[0], parts[1]


def _path_in_scope(rel: str, kind: SourceKind, scope: tuple[str, str] | None) -> bool:
    """Whole repo when scope is None. With --env: that env + its cluster passport + system + repo shared."""
    if scope is None:
        return True
    cluster, env = scope
    if kind == "system":
        return True
    if kind == "passport":
        return _parse_cluster_env(rel)[0] == cluster
    if kind == "shared":
        c, e = _parse_cluster_env(rel)
        if rel.replace("\\", "/").startswith("environments/credentials/") or rel.replace(
            "\\", "/"
        ).startswith("environments/shared-credentials/"):
            return True  # repo-wide shared
        if e is None and c == cluster:
            return True  # cluster-level shared
        return c == cluster and e == env
    # env inventory
    c, e = _parse_cluster_env(rel)
    return c == cluster and e == env


def check_cyrillic_paths(rels: list[str]) -> list[str]:
    """Return errors for credential-related paths containing Cyrillic."""
    errors: list[str] = []
    for rel in rels:
        if _CYRILLIC_RE.search(rel):
            errors.append(
                f"Cyrillic in credential path is not supported: {rel}"
            )
    return errors


def check_mixed_types_in_file(path: Path, rel: str) -> list[str]:
    """Hard fail if one source file mixes type: external and local cred types."""
    entries = _entries_from_cred_file(path)
    if not entries:
        return []
    has_external = False
    has_local = False
    for entry in entries.values():
        t = entry.get("type")
        if t == "external":
            has_external = True
        elif t in ("usernamePassword", "secret") or (
            isinstance(entry.get("data"), dict) and t != "external"
        ):
            has_local = True
    if has_external and has_local:
        return [
            f"mixed local and external credentials in the same file: {rel} "
            "(migrate fully or split before plan)"
        ]
    return []


def _flag_passport_shared_duplicates(plan: dict[str, Any]) -> None:
    """Same cred-id in passport and shared → both to_review; ask who is authoritative."""
    by_id: dict[str, list[tuple[str, dict[str, Any], str]]] = {}
    for src, _bucket, cred_id, fields in iter_plan_entries(plan):
        kind = _source_kind(src)
        by_id.setdefault(cred_id, []).append((src, fields, kind))

    for cred_id, rows in by_id.items():
        kinds = {r[2] for r in rows}
        if "passport" not in kinds or "shared" not in kinds:
            continue
        for src, fields, kind in rows:
            if kind not in ("passport", "shared"):
                continue
            for group in plan.get("credentials") or []:
                if group.get("sourceFile") != src:
                    continue
                confirm = group.setdefault("to_confirm", {})
                review = group.setdefault("to_review", {})
                entry = confirm.pop(cred_id, None) or review.get(cred_id) or dict(fields)
                if not isinstance(entry, dict):
                    entry = dict(fields)
                else:
                    entry = dict(entry)
                sugg = list(entry.get("suggestions") or [])
                msg = (
                    "cred-id also in passport and shared — pick authoritative source; "
                    f"seen in: {', '.join(sorted({r[0] for r in rows}))}"
                )
                if msg not in sugg:
                    sugg.append(msg)
                entry["suggestions"] = sugg
                review[cred_id] = entry
                confirm.pop(cred_id, None)


def build_instance_plan(
    repo_root: Path, *, env_filter: str | None = None
) -> dict[str, Any]:
    prior = try_load_prior_plan(cwd=repo_root)
    scope = _parse_env_filter(env_filter)
    plan = empty_plan("instance")
    if scope:
        plan["env_filter"] = f"{scope[0]}/{scope[1]}"

    # Welcome answer (git|jenkins|store|apply_store). Default Store-write on apply
    # only for explicit apply_store; Transfer / Git / Jenkins paths stay false.
    prior_od = (prior or {}).get("operator_decisions") or {}
    values_source = prior_od.get("values_source") if isinstance(prior_od, dict) else None
    default_write_to_store = values_source == "apply_store"

    sources: list[Path] = []
    sources.extend(_passport_cred_files(repo_root))
    repo_cluster, env_scoped = _iter_shared_files(repo_root)
    sources.extend(repo_cluster)
    sources.extend(env_scoped)
    sources.extend(_system_cred_files(repo_root))

    path_errors: list[str] = []
    mixed_errors: list[str] = []
    rels_for_cyrillic: list[str] = []

    for path in sources:
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        kind = _source_kind(rel)
        if not _path_in_scope(rel, kind, scope):
            continue
        rels_for_cyrillic.append(rel)
        mixed_errors.extend(check_mixed_types_in_file(path, rel))

        cluster, env = _parse_cluster_env(rel)
        default_path, default_create = _path_and_create(kind, cluster, env)
        entries = _entries_from_cred_file(path)
        to_review: dict[str, Any] = {}
        to_confirm: dict[str, Any] = {}
        for cred_id, entry in sorted(entries.items()):
            if entry.get("type") == "external":
                continue
            # Instance policy (no classify): passport/system auto; else always ask
            fields: dict[str, Any] = {
                "remoteRefPath": default_path,
                "writeToStore": default_write_to_store,
                "suggestions": [],
            }
            if default_create is not None:
                fields["create"] = default_create
            if kind in ("passport", "system"):
                fields["create"] = False
                if kind == "system":
                    fields["remoteRefPath"] = GLOBAL_PATH
                    fields["writeToStore"] = False
                    fields["suggestions"].append(
                        "system cred: create=false; Store should already be filled by "
                        "`migration-cli collect-system` → external-cred-provision "
                        "(set writeToStore:true only if you skipped that step)"
                    )
            else:
                fields["suggestions"].append(
                    f"suggested create={default_create!s}, "
                    f"remoteRefPath={default_path} — confirm or override"
                )

            if is_null_placeholder(entry.get("data")):
                fields["_hasNullPlaceholder"] = True
                fields["writeToStore"] = False
                fields["suggestions"].append(
                    "envgeneNullValue — Store write skipped; seed out-of-band"
                )

            if kind in ("passport", "system"):
                to_confirm[cred_id] = fields
            else:
                to_review[cred_id] = fields
        add_source_group(plan, rel, to_review=to_review, to_confirm=to_confirm)

    path_errors.extend(check_cyrillic_paths(rels_for_cyrillic))
    # Also flag generated Credentials paths with Cyrillic
    deletes = _generated_and_deployer_deletes(repo_root)
    path_errors.extend(
        check_cyrillic_paths(deletes.get("generated_env_credentials") or [])
    )
    if path_errors or mixed_errors:
        plan["plan_errors"] = path_errors + mixed_errors

    _flag_passport_shared_duplicates(plan)

    if scope is None:
        deletes["unused_shared_credentials"] = find_orphaned_shared_files(repo_root)
    else:
        # Narrow deletes to scoped env when filtering
        cluster, env = scope
        gen = [
            p
            for p in deletes.get("generated_env_credentials") or []
            if f"/{cluster}/{env}/" in f"/{p}"
        ]
        dep = [
            p
            for p in deletes.get("deployer_credentials") or []
            if f"/{cluster}/{env}/" in f"/{p}"
        ]
        deletes["generated_env_credentials"] = gen
        deletes["deployer_credentials"] = dep
        deletes["unused_shared_credentials"] = []
    plan["to_delete"] = deletes
    plan["runtime_credential_macros"] = scan_instance_runtime_macros(
        repo_root, env_filter=env_filter
    )
    merge_prior_plan_overrides(plan, prior)
    return plan
