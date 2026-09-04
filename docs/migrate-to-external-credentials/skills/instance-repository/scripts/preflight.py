#!/usr/bin/env python3
"""Preflight checks for Instance Repository External Credentials migration.

Read-only. Starts from env_definition.yml and builds the used credential graph.
Exit 0 when safe to continue; exit 2 when blockers need user action; exit 1 on errors.
Never prints secret values from data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    SUPPORTED_LOCAL_TYPES,
    UNSUPPORTED_LOCAL_TYPES,
    classify_path,
    collect_referenced_cred_ids,
    discover_shared_credential_files,
    emit,
    find_env_definitions,
    find_macro_issues,
    heuristic_provider_markers,
    is_stub_data,
    iter_credential_entries,
    load_yaml,
    normalize_shared_stem,
    parse_cluster_env,
    resolve_passport_creds,
    resolve_shared_file,
)


def _rel(repo: Path, path: Path) -> str:
    return str(path.relative_to(repo).as_posix())


def _issue(
    *,
    kind: str,
    severity: str,
    message: str,
    path: str | None = None,
    cred_id: str | None = None,
    suggested_action: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if path is not None:
        item["path"] = path
    if cred_id is not None:
        item["credId"] = cred_id
    if suggested_action is not None:
        item["suggested_action"] = suggested_action
    item.update(extra)
    return item


def _load_doc(path: Path) -> Any:
    try:
        return load_yaml(path)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to parse {path}: {exc}") from exc


def check_secret_stores(repo: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    path = repo / "configuration" / "secret-stores.yml"
    if not path.is_file():
        path = repo / "configuration" / "secret-stores.yaml"
    if not path.is_file():
        blockers.append(
            _issue(
                kind="missing_secret_stores",
                severity="blocker",
                path="configuration/secret-stores.yml",
                message="configuration/secret-stores.yml is missing",
                suggested_action="Create default_store before migration",
            )
        )
        return blockers, warnings

    doc = _load_doc(path) or {}
    if not isinstance(doc, dict) or "default_store" not in doc:
        blockers.append(
            _issue(
                kind="missing_default_store",
                severity="blocker",
                path=_rel(repo, path),
                message="default_store is missing in secret-stores.yml",
                suggested_action="Define a single default_store",
            )
        )
        return blockers, warnings

    extra = [k for k in doc if k != "default_store"]
    if extra:
        warnings.append(
            _issue(
                kind="multiple_secret_stores",
                severity="warning",
                path=_rel(repo, path),
                message=(
                    "Migration assumes one default_store; extra store ids found: "
                    + ", ".join(extra)
                ),
                suggested_action="Confirm migration uses only default_store",
            )
        )
    return blockers, warnings


def collect_env_scope(repo: Path, env_def: Path) -> dict[str, Any]:
    cluster, env = parse_cluster_env(env_def, repo)
    doc = _load_doc(env_def) or {}
    inventory = doc.get("inventory") or {}
    env_template = doc.get("envTemplate") or {}
    passport = inventory.get("cloudPassport")
    shared_raw = env_template.get("sharedMasterCredentialFiles") or []
    if isinstance(shared_raw, str):
        shared_raw = [shared_raw]

    source_files: list[str] = []
    consumer_files: list[str] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    declared: dict[str, str] = {}
    referenced: set[str] = set()

    # Passport
    if passport:
        creds_path = resolve_passport_creds(repo, cluster, str(passport))
        if creds_path is None:
            blockers.append(
                _issue(
                    kind="missing_passport_creds",
                    severity="blocker",
                    path=f"environments/{cluster}/cloud-passport/{passport}-creds.yml",
                    message=f"Cloud Passport '{passport}' is referenced but creds file is missing",
                    suggested_action="Restore the *-creds.yml file or fix env_definition",
                )
            )
        else:
            source_files.append(_rel(repo, creds_path))
        main_candidates = [
            repo / "environments" / cluster / "cloud-passport" / f"{passport}.yml",
            repo / "environments" / cluster / "cloud-passport" / f"{passport}.yaml",
        ]
        for main in main_candidates:
            if main.is_file():
                consumer_files.append(_rel(repo, main))
                break

    # Shared
    bound_shared_stems: list[str] = []
    for raw in shared_raw:
        stem, has_ext = normalize_shared_stem(str(raw))
        bound_shared_stems.append(stem)
        if has_ext:
            blockers.append(
                _issue(
                    kind="shared_ref_has_extension",
                    severity="blocker",
                    path=_rel(repo, env_def),
                    message=(
                        f"sharedMasterCredentialFiles entry '{raw}' includes a .yml extension; "
                        "EnvGene skips such references"
                    ),
                    suggested_action=f"Change to '{stem}' (no extension)",
                )
            )
        resolved = resolve_shared_file(repo, cluster, env, stem)
        if resolved is None:
            blockers.append(
                _issue(
                    kind="missing_shared_file",
                    severity="blocker",
                    path=_rel(repo, env_def),
                    message=f"Shared Credential file '{stem}' is referenced but not found",
                    suggested_action="Restore the file or remove the env_definition binding",
                )
            )
        else:
            source_files.append(_rel(repo, resolved))

    # Environment / cluster / global ParameterSets (consumers)
    param_globs = [
        repo / "environments" / cluster / env / "Inventory" / "parameters",
        repo / "environments" / cluster / "parameters",
        repo / "environments" / "parameters",
    ]
    for base in param_globs:
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.yml")) + sorted(base.glob("*.yaml")):
            consumer_files.append(_rel(repo, path))

    # System config consumers
    for rel in (
        "configuration/integration.yml",
        "configuration/integration.yaml",
        "configuration/registry.yml",
        "configuration/registry.yaml",
    ):
        path = repo / rel
        if path.is_file():
            consumer_files.append(rel)

    # System credential sources
    for rel in (
        "configuration/credentials/credentials.yml",
        "configuration/credentials/credentials.yaml",
    ):
        path = repo / rel
        if path.is_file():
            source_files.append(rel)

    # Scan sources for declared credIds
    for rel in list(dict.fromkeys(source_files)):
        path = repo / rel
        cls = classify_path(path, repo)
        if cls == "generated_credentials":
            continue
        doc = _load_doc(path) or {}
        for cred_id, entry in iter_credential_entries(doc):
            declared[cred_id] = rel
            local_type = entry.get("type")
            if local_type in UNSUPPORTED_LOCAL_TYPES:
                blockers.append(
                    _issue(
                        kind="unsupported_cred_type",
                        severity="blocker",
                        path=rel,
                        cred_id=cred_id,
                        message=f"Unsupported credential type '{local_type}'",
                        suggested_action="Migrate this credential out-of-band",
                    )
                )
            elif local_type == "external" and not entry.get("secretStore"):
                blockers.append(
                    _issue(
                        kind="missing_secret_store",
                        severity="blocker",
                        path=rel,
                        cred_id=cred_id,
                        message=(
                            "secretStore is required on type: external; "
                            "EnvGene does not fill schema defaults"
                        ),
                        suggested_action=(
                            "Set secretStore to an id from configuration/secret-stores.yml "
                            "(usually default_store)"
                        ),
                    )
                )
            elif local_type not in SUPPORTED_LOCAL_TYPES and local_type != "external":
                if local_type is not None:
                    warnings.append(
                        _issue(
                            kind="unknown_cred_type",
                            severity="warning",
                            path=rel,
                            cred_id=cred_id,
                            message=f"Unknown credential type '{local_type}'",
                        )
                    )
            if local_type in SUPPORTED_LOCAL_TYPES and is_stub_data(entry.get("data")):
                warnings.append(
                    _issue(
                        kind="stub_value",
                        severity="warning",
                        path=rel,
                        cred_id=cred_id,
                        message="Credential data looks like a stub (empty or envgeneNullValue)",
                        suggested_action="Transfer a real value before Store write",
                    )
                )
            for marker in heuristic_provider_markers(cred_id):
                warnings.append(
                    _issue(
                        kind="heuristic_review",
                        severity="warning",
                        path=rel,
                        cred_id=cred_id,
                        message=marker,
                        suggested_action="Confirm creation owner and remoteRefPath before convert",
                    )
                )

    # Scan consumers for refs + macro issues
    for rel in list(dict.fromkeys(consumer_files)):
        path = repo / rel
        doc = _load_doc(path)
        referenced |= collect_referenced_cred_ids(doc)
        for issue in find_macro_issues(doc):
            issue = {**issue, "file": rel}
            if issue.get("severity") == "blocker":
                blockers.append(issue)
            else:
                warnings.append(issue)

    return {
        "environment": f"{cluster}/{env}",
        "env_definition": _rel(repo, env_def),
        "cloud_passport": passport,
        "shared_stems": bound_shared_stems,
        "source_files": list(dict.fromkeys(source_files)),
        "consumer_files": list(dict.fromkeys(consumer_files)),
        "declared_cred_ids": sorted(declared),
        "referenced_cred_ids": sorted(referenced),
        "blockers": blockers,
        "warnings": warnings,
        "_declared_map": declared,
        "_referenced": referenced,
        "_cluster": cluster,
        "_bound_shared": set(bound_shared_stems),
        "_passport": str(passport) if passport else None,
    }


def find_orphans(
    repo: Path,
    scopes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    bound_passports = {
        (s["_cluster"], s["_passport"]) for s in scopes if s.get("_passport")
    }
    bound_shared = {(s["_cluster"], stem) for s in scopes for stem in s["_bound_shared"]}
    # Repo-level shared is cluster-agnostic: also allow match by stem alone for repo scope
    bound_shared_stems = {stem for s in scopes for stem in s["_bound_shared"]}

    # Unbound passport creds
    for path in sorted((repo / "environments").glob("*/cloud-passport/*-creds.y*ml")):
        if not path.is_file():
            continue
        rel = _rel(repo, path)
        parts = rel.split("/")
        cluster = parts[1]
        stem = path.name.replace("-creds.yml", "").replace("-creds.yaml", "")
        if (cluster, stem) not in bound_passports:
            blockers.append(
                _issue(
                    kind="orphan_passport_creds",
                    severity="blocker",
                    path=rel,
                    message="Cloud Passport creds file is not referenced by any env_definition",
                    suggested_action="Delete manually or bind it from an environment, then re-run",
                )
            )

    # Unbound shared files
    for path in discover_shared_credential_files(repo):
        rel = _rel(repo, path)
        cls = classify_path(path, repo)
        stem = path.stem
        parts = rel.split("/")
        cluster = parts[1] if len(parts) > 1 else ""

        if cls == "shared_credentials_env":
            # Env-scoped shared is in scope for that environment by location
            continue
        if cls == "shared_credentials_repo":
            if stem not in bound_shared_stems:
                blockers.append(
                    _issue(
                        kind="orphan_shared_file",
                        severity="blocker",
                        path=rel,
                        message="Shared Credential file is not referenced by any env_definition",
                        suggested_action="Delete manually or add to sharedMasterCredentialFiles",
                    )
                )
            continue
        if (cluster, stem) not in bound_shared and stem not in bound_shared_stems:
            blockers.append(
                _issue(
                    kind="orphan_shared_file",
                    severity="blocker",
                    path=rel,
                    message="Shared Credential file is not referenced by any env_definition",
                    suggested_action="Delete manually or add to sharedMasterCredentialFiles",
                )
            )

    # Declared but never referenced credIds (within bound sources)
    all_referenced: set[str] = set()
    all_declared: dict[str, str] = {}
    for scope in scopes:
        all_referenced |= scope["_referenced"]
        all_declared.update(scope["_declared_map"])

    for cred_id, source in sorted(all_declared.items()):
        if cred_id not in all_referenced:
            warnings.append(
                _issue(
                    kind="unreferenced_cred_id",
                    severity="warning",
                    path=source,
                    cred_id=cred_id,
                    message="credId is declared in a source file but not referenced by scanned consumers",
                    suggested_action="Confirm unused, or fix missing references before convert",
                )
            )

    for cred_id in sorted(all_referenced - set(all_declared)):
        blockers.append(
            _issue(
                kind="undeclared_cred_id",
                severity="blocker",
                cred_id=cred_id,
                message=(
                    f"credId '{cred_id}' is referenced by consumers but not declared "
                    "in any in-scope source Credential file"
                ),
                suggested_action="Add the Credential definition or remove the reference",
            )
        )

    return blockers, warnings


def find_out_of_scope(repo: Path) -> dict[str, list[str]]:
    deployer: list[str] = []
    generated: list[str] = []
    for path in sorted(repo.glob("environments/*/app-deployer/*creds*")):
        if path.is_file() and path.suffix in (".yml", ".yaml"):
            deployer.append(_rel(repo, path))
    for path in sorted(repo.glob("environments/*/*/Credentials/credentials.y*ml")):
        if path.is_file():
            generated.append(_rel(repo, path))
    return {"deployer_credentials": deployer, "generated_credentials": generated}


def run_preflight(repo: Path) -> dict[str, Any]:
    env_defs = find_env_definitions(repo)
    if not env_defs:
        return {
            "status": "error",
            "error": "No env_definition.yml files found under environments/",
        }

    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    store_blockers, store_warnings = check_secret_stores(repo)
    blockers.extend(store_blockers)
    warnings.extend(store_warnings)

    scopes: list[dict[str, Any]] = []
    for env_def in env_defs:
        scope = collect_env_scope(repo, env_def)
        blockers.extend(scope.pop("blockers"))
        warnings.extend(scope.pop("warnings"))
        scopes.append(scope)

    orphan_blockers, orphan_warnings = find_orphans(repo, scopes)
    blockers.extend(orphan_blockers)
    warnings.extend(orphan_warnings)

    out_of_scope = find_out_of_scope(repo)
    if out_of_scope["deployer_credentials"]:
        warnings.append(
            _issue(
                kind="deployer_out_of_scope",
                severity="warning",
                message="Deployer credential files are out of scope for No-CMDB (delete, do not convert)",
                paths=out_of_scope["deployer_credentials"],
                suggested_action="Delete during cleanup after YAML cutover",
            )
        )
    if out_of_scope["generated_credentials"]:
        warnings.append(
            _issue(
                kind="generated_credentials_present",
                severity="warning",
                message="Generated Credentials/credentials.yml files present (delete-only)",
                paths=out_of_scope["generated_credentials"],
                suggested_action="Delete during cleanup; EnvGene regenerates after cutover",
            )
        )

    # Strip private keys from scopes for output
    public_scopes = []
    for scope in scopes:
        public_scopes.append(
            {
                "environment": scope["environment"],
                "env_definition": scope["env_definition"],
                "cloud_passport": scope["cloud_passport"],
                "shared_stems": scope["shared_stems"],
                "source_files": scope["source_files"],
                "consumer_files": scope["consumer_files"],
                "declared_cred_ids": scope["declared_cred_ids"],
                "referenced_cred_ids": scope["referenced_cred_ids"],
            }
        )

    status = "ok" if not blockers else "NEEDS_INPUT"
    return {
        "status": status,
        "mode": "preflight",
        "repo": str(repo),
        "environments": public_scopes,
        "out_of_scope": out_of_scope,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "environments": len(public_scopes),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "deployer_files": len(out_of_scope["deployer_credentials"]),
            "generated_files": len(out_of_scope["generated_credentials"]),
        },
        "note": (
            "Read-only preflight. Fix blockers (or clean orphans manually), then re-run. "
            "Do not convert until status is ok. Secret values are never printed."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Instance Repository root")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.is_dir():
        emit({"status": "error", "error": f"Not a directory: {repo}"}, EXIT_ERROR)

    try:
        result = run_preflight(repo)
    except ValueError as exc:
        emit({"status": "error", "error": str(exc)}, EXIT_ERROR)

    if result.get("status") == "error":
        emit(result, EXIT_ERROR)
    if result.get("status") == "NEEDS_INPUT":
        emit(result, EXIT_NEEDS_INPUT)
    emit(result, EXIT_OK)


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
