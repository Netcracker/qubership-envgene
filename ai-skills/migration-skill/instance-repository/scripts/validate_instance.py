#!/usr/bin/env python3
"""Validate Instance Repository External Credentials migration result (read-only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

from common import (
    EXIT_ERROR,
    EXIT_OK,
    classify_path,
    emit,
    find_env_definitions,
    find_remaining_macros,
    iter_credential_entries,
    load_yaml,
    path_contains_cred_id,
)


def find_schema(repo: Path, name: str) -> Path | None:
    """Locate schema relative to repo or walking up to qubership-envgene root."""
    candidates = [
        repo / "schemas" / name,
        repo.parent / "schemas" / name,
    ]
    # walk up
    for parent in [repo, *repo.parents]:
        candidate = parent / "schemas" / name
        if candidate.is_file():
            return candidate
    for c in candidates:
        if c.is_file():
            return c
    return None


def validate_secret_stores_skill_rules(doc: dict[str, Any]) -> list[str]:
    """Required fields from migration skills/how-to (not inventing url)."""
    issues = []
    required_by_type = {
        "vault": ["mountPath"],
        "gcp": ["projectId"],
        "aws": ["region"],
        "azure": ["vaultName"],
    }
    for store_id, cfg in doc.items():
        if not isinstance(cfg, dict):
            issues.append(f"secret-stores: {store_id} must be a mapping")
            continue
        stype = cfg.get("type")
        if stype not in required_by_type:
            issues.append(f"secret-stores: {store_id} has unsupported or missing type")
            continue
        for field in required_by_type[stype]:
            if field not in cfg:
                issues.append(f"secret-stores: {store_id} missing {field} for type {stype}")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        default=None,
        help="Directory containing credential.schema.json (optional)",
    )
    parser.add_argument(
        "--credential-files",
        nargs="*",
        help="Credential YAML to validate; default = discover",
    )
    parser.add_argument(
        "--macro-files",
        nargs="*",
        help="YAML files to scan for leftover macros",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()

    issues: list[dict[str, Any]] = []
    checked = []

    stores_path = repo / "configuration" / "secret-stores.yml"
    if not stores_path.is_file():
        stores_path = repo / "configuration" / "secret-stores.yaml"
    store_ids: set[str] = set()
    if stores_path.is_file():
        stores = load_yaml(stores_path) or {}
        checked.append(str(stores_path.relative_to(repo).as_posix()))
        if not isinstance(stores, dict) or not stores:
            issues.append({"severity": "error", "message": "secret-stores.yml is empty or invalid"})
        else:
            store_ids = set(stores.keys())
            for msg in validate_secret_stores_skill_rules(stores):
                issues.append({"severity": "error", "message": msg})
            schema_path = None
            if args.schemas_dir:
                schema_path = args.schemas_dir / "secret-stores.schema.json"
            else:
                schema_path = find_schema(repo, "secret-stores.schema.json")
            if schema_path and schema_path.is_file():
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                try:
                    jsonschema.validate(stores, schema)
                except jsonschema.ValidationError as exc:
                    # Sample/how-to often omit url; report as warning so skill can decide
                    issues.append(
                        {
                            "severity": "warning",
                            "message": f"secret-stores schema: {exc.message}",
                            "schema": str(schema_path),
                        }
                    )
    else:
        issues.append(
            {
                "severity": "error",
                "message": "configuration/secret-stores.yml is missing",
            }
        )

    cred_schema_path = None
    if args.schemas_dir:
        cred_schema_path = args.schemas_dir / "credential.schema.json"
    else:
        cred_schema_path = find_schema(repo, "credential.schema.json")
    cred_schema = None
    if cred_schema_path and cred_schema_path.is_file():
        cred_schema = json.loads(cred_schema_path.read_text(encoding="utf-8"))

    if args.credential_files:
        cred_paths = [(repo / p).resolve() for p in args.credential_files]
    else:
        cred_paths = []
        for pattern in (
            "environments/*/cloud-passport/*-creds.y*ml",
            "environments/*/shared-credentials/*.y*ml",
            "environments/*/app-deployer/*creds*.y*ml",
            "configuration/credentials/*.y*ml",
        ):
            cred_paths.extend(sorted(repo.glob(pattern)))

    for path in cred_paths:
        if not path.is_file():
            issues.append({"severity": "error", "message": f"Missing {path}"})
            continue
        rel = str(path.relative_to(repo).as_posix())
        checked.append(rel)
        cls = classify_path(path, repo)
        doc = load_yaml(path) or {}
        if cred_schema:
            try:
                jsonschema.validate(doc, cred_schema)
            except jsonschema.ValidationError as exc:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: schema {exc.message}",
                        "path": list(exc.path),
                    }
                )
        for cred_id, entry in iter_credential_entries(doc):
            if entry.get("type") != "external":
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: {cred_id} type is {entry.get('type')!r}, expected external",
                    }
                )
            if "data" in entry:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: {cred_id} still has data",
                    }
                )
            if "writeToStore" in entry:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: {cred_id} must not contain writeToStore in Credential YAML",
                    }
                )
            if entry.get("create") is False:
                issues.append(
                    {
                        "severity": "error",
                        "message": (
                            f"{rel}: {cred_id} has create:false - omit the field in final YAML"
                        ),
                    }
                )
            rrp = entry.get("remoteRefPath")
            if isinstance(rrp, str) and path_contains_cred_id(rrp, cred_id):
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: {cred_id} remoteRefPath must not include credId",
                    }
                )
            props = entry.get("properties")
            if props is not None:
                for p in props:
                    if not isinstance(p, dict) or "name" not in p:
                        issues.append(
                            {
                                "severity": "error",
                                "message": f"{rel}: {cred_id} properties must be - name: objects",
                            }
                        )
            ss = entry.get("secretStore", "default_store")
            if store_ids and ss not in store_ids:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: {cred_id} secretStore {ss!r} not in secret-stores.yml",
                    }
                )
            if cls == "system_credentials":
                if entry.get("create") is True:
                    issues.append(
                        {
                            "severity": "error",
                            "message": f"{rel}: {cred_id} System Credential must not set create:true",
                        }
                    )
                if not entry.get("remoteRefPath"):
                    issues.append(
                        {
                            "severity": "error",
                            "message": f"{rel}: {cred_id} System Credential needs explicit remoteRefPath",
                        }
                    )

    # sharedMasterCredentialFiles extension check
    for env_def in find_env_definitions(repo):
        rel = str(env_def.relative_to(repo).as_posix())
        doc = load_yaml(env_def) or {}
        shared = (doc.get("envTemplate") or {}).get("sharedMasterCredentialFiles") or []
        if isinstance(shared, str):
            shared = [shared]
        for item in shared:
            if isinstance(item, str) and (item.endswith(".yml") or item.endswith(".yaml")):
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: sharedMasterCredentialFiles value {item!r} must not include extension",
                    }
                )

    macro_paths: list[Path] = []
    if args.macro_files:
        macro_paths = [(repo / p).resolve() for p in args.macro_files]
    for path in macro_paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(repo).as_posix())
        checked.append(rel)
        doc = load_yaml(path)
        for hit in find_remaining_macros(doc):
            if hit.get("technical"):
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"{rel}: macro left in technical scope at {hit.get('path')}",
                    }
                )
            else:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: leftover macro at {hit.get('path')}",
                    }
                )

    errors = [i for i in issues if i["severity"] == "error"]
    status = "ok" if not errors else "error"
    emit(
        {
            "status": status,
            "mode": "analyze",
            "checked_files": checked,
            "issues": issues,
            "error_count": len(errors),
            "warning_count": len(issues) - len(errors),
        },
        EXIT_OK if status == "ok" else EXIT_ERROR,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
