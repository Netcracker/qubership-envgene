#!/usr/bin/env python3
"""Inventory Environment Instances and credential-related files (read-only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    EXIT_ERROR,
    EXIT_OK,
    classify_path,
    emit,
    find_env_definitions,
    load_yaml,
    parse_cluster_env,
)


def collect_passport_files(repo: Path, cluster: str, name: str) -> dict[str, str | None]:
    base = repo / "environments" / cluster / "cloud-passport"
    main = None
    creds = None
    for ext in (".yml", ".yaml"):
        candidate = base / f"{name}{ext}"
        if candidate.is_file():
            main = str(candidate.relative_to(repo).as_posix())
        creds_candidate = base / f"{name}-creds{ext}"
        if creds_candidate.is_file():
            creds = str(creds_candidate.relative_to(repo).as_posix())
    return {"main": main, "creds": creds}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Instance Repository root")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.is_dir():
        emit({"status": "error", "error": f"Not a directory: {repo}"}, EXIT_ERROR)

    environments = []
    passport_consumers: dict[str, list[str]] = {}
    shared_consumers: dict[str, list[str]] = {}

    for env_def in find_env_definitions(repo):
        cluster, env = parse_cluster_env(env_def, repo)
        key = f"{cluster}/{env}"
        try:
            doc = load_yaml(env_def) or {}
        except Exception as exc:  # noqa: BLE001
            emit(
                {
                    "status": "error",
                    "error": f"Failed to parse {env_def}: {exc}",
                },
                EXIT_ERROR,
            )
        inventory = doc.get("inventory") or {}
        env_template = doc.get("envTemplate") or {}
        passport = inventory.get("cloudPassport")
        shared = env_template.get("sharedMasterCredentialFiles") or []
        if isinstance(shared, str):
            shared = [shared]
        assumed = "unknown"
        lowered = f"{cluster}/{env}".lower()
        if any(x in lowered for x in ("prod", "prd", "production")):
            assumed = "likely_prod"
        elif any(x in lowered for x in ("dev", "test", "stage", "stg", "nonprod", "sandbox", "qa")):
            assumed = "likely_non_prod"

        entry = {
            "environment": key,
            "env_definition": str(env_def.relative_to(repo).as_posix()),
            "template_name": env_template.get("name"),
            "template_artifact": env_template.get("artifact"),
            "cloud_passport": passport,
            "shared_master_credential_files": shared,
            "assumed_type": assumed,
        }
        environments.append(entry)
        if passport:
            passport_consumers.setdefault(f"{cluster}:{passport}", []).append(key)
        for s in shared:
            shared_consumers.setdefault(f"{cluster}:{s}", []).append(key)

    credential_files = []
    for pattern in (
        "environments/*/cloud-passport/*",
        "environments/*/shared-credentials/*",
        "environments/*/app-deployer/*creds*",
        "configuration/credentials/*",
        "environments/*/*/Credentials/credentials.y*ml",
    ):
        for path in sorted(repo.glob(pattern)):
            if not path.is_file():
                continue
            if path.suffix not in (".yml", ".yaml"):
                continue
            credential_files.append(
                {
                    "path": str(path.relative_to(repo).as_posix()),
                    "class": classify_path(path, repo),
                }
            )

    bound_passports = set()
    bound_shared = set()
    for env in environments:
        cluster = env["environment"].split("/")[0]
        if env["cloud_passport"]:
            bound_passports.add((cluster, env["cloud_passport"]))
        for s in env["shared_master_credential_files"]:
            name = s[:-4] if str(s).endswith(".yml") else s
            if str(s).endswith(".yaml"):
                name = s[:-5]
            bound_shared.add((cluster, name))

    unbound = []
    for cf in credential_files:
        cls = cf["class"]
        path = cf["path"]
        parts = path.split("/")
        if cls == "cloud_passport_creds" and len(parts) >= 4:
            cluster = parts[1]
            fname = Path(parts[-1]).name
            passport_name = fname.replace("-creds.yml", "").replace("-creds.yaml", "")
            if (cluster, passport_name) not in bound_passports:
                unbound.append({**cf, "reason": "passport_not_referenced"})
        if cls == "shared_credentials" and len(parts) >= 4:
            cluster = parts[1]
            name = Path(parts[-1]).stem
            if (cluster, name) not in bound_shared:
                unbound.append({**cf, "reason": "shared_not_referenced"})

    non_prod_candidates = [
        e["environment"]
        for e in environments
        if e["assumed_type"] == "likely_non_prod"
    ][:3]

    emit(
        {
            "status": "ok",
            "mode": "analyze",
            "repo": str(repo),
            "environments": environments,
            "passport_consumers": passport_consumers,
            "shared_consumers": shared_consumers,
            "credential_files": credential_files,
            "unbound_resources": unbound,
            "suggested_non_prod": non_prod_candidates,
            "decisions_needed": [
                {
                    "id": "select_first_environment",
                    "message": "Select the first Environment Instance for cutover (confirm non-prod).",
                    "candidates": non_prod_candidates or [e["environment"] for e in environments[:3]],
                }
            ],
        },
        EXIT_OK,
    )


if __name__ == "__main__":
    # Allow running as script from scripts/ directory
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
