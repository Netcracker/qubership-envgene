#!/usr/bin/env python3
"""Classify credential entries with policy decision records (read-only analyze)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    build_decision_record,
    classify_path,
    emit,
    iter_credential_entries,
    load_yaml,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--files",
        nargs="*",
        help="Optional relative paths; default = discover credential YAML files",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.is_dir():
        emit({"status": "error", "error": f"Not a directory: {repo}"}, EXIT_ERROR)

    paths: list[Path] = []
    if args.files:
        paths = [(repo / f).resolve() for f in args.files]
    else:
        for pattern in (
            "environments/*/cloud-passport/*-creds.y*ml",
            "environments/*/shared-credentials/*.y*ml",
            "environments/*/credentials/*.y*ml",
            "environments/credentials/*.y*ml",
            "environments/*/*/Inventory/credentials/*.y*ml",
            "environments/*/app-deployer/*creds*.y*ml",
            "configuration/credentials/*.y*ml",
            "environments/*/*/Credentials/credentials.y*ml",
        ):
            paths.extend(sorted(repo.glob(pattern)))

    credentials = []
    decisions_needed = []
    for path in paths:
        if not path.is_file():
            emit({"status": "error", "error": f"Missing file: {path}"}, EXIT_ERROR)
        cls = classify_path(path, repo)
        if cls in ("cloud_passport_main", "generated_effective_set", "parameters", "other"):
            continue
        try:
            doc = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            emit({"status": "error", "error": f"Parse failed {path}: {exc}"}, EXIT_ERROR)
        rel = str(path.relative_to(repo).as_posix())
        if cls == "generated_credentials":
            credentials.append(
                {
                    "credId": "*",
                    "sourcePath": rel,
                    "class": cls,
                    "action": "delete_only",
                    "tier": "unknown",
                    "creationOwner": "unknown",
                    "evidence": ["generated Credentials file - delete only"],
                    "confidence": "confirmed",
                    "proposedCreate": None,
                    "proposedRemoteRefPath": None,
                    "needsReview": False,
                }
            )
            continue

        for cred_id, entry in iter_credential_entries(doc or {}):
            local_type = entry.get("type")
            # Never include data / secret values
            record = build_decision_record(
                cred_id, rel, cls, local_type=local_type
            )
            record["class"] = cls
            record["local_type"] = local_type
            record["has_data"] = "data" in entry
            if local_type in ("usernamePassword", "secret"):
                record["target_shape"] = (
                    "multi_field" if local_type == "usernamePassword" else "single_value"
                )
                record["conversion"] = "local_to_external"
            elif local_type == "external":
                record["conversion"] = "already_external"
            elif local_type == "vaultAppRole":
                record["conversion"] = "unsupported_in_scripts"
                record["creationOwner"] = "unknown"
                record["confidence"] = "ambiguous"
                record["needsReview"] = True
                record["proposedCreate"] = None
                record["evidence"].append("type vaultAppRole is not auto-converted")
            else:
                record["conversion"] = "unknown"
                record["creationOwner"] = "unknown"
                record["confidence"] = "ambiguous"
                record["needsReview"] = True
                record["proposedCreate"] = None

            # Keep existing remoteRefPath as stronger path evidence when present
            existing_path = entry.get("remoteRefPath")
            if isinstance(existing_path, str) and existing_path and record["proposedRemoteRefPath"] is not None:
                record["evidence"].append("existing remoteRefPath on entry")
                record["proposedRemoteRefPath"] = existing_path
            elif isinstance(existing_path, str) and existing_path and record["confidence"] != "ambiguous":
                record["proposedRemoteRefPath"] = existing_path
                record["evidence"].append("existing remoteRefPath on entry")

            credentials.append(record)
            if record.get("needsReview") or record.get("confidence") in (
                "ambiguous",
                "proposed",
            ):
                if record.get("conversion") == "local_to_external" or record.get(
                    "conversion"
                ) in ("unsupported_in_scripts", "unknown"):
                    decisions_needed.append(
                        {
                            "id": f"decision:{rel}:{cred_id}",
                            "status": "NEEDS_INPUT",
                            "credId": cred_id,
                            "sourcePath": rel,
                            "message": (
                                "Confirm creationOwner, create, remoteRefPath, and writeToStore "
                                "before convert. Show evidence and proposals; do not apply guesses."
                            ),
                            "evidence": record["evidence"],
                            "proposedCreate": record["proposedCreate"],
                            "proposedRemoteRefPath": record["proposedRemoteRefPath"],
                            "creationOwner": record["creationOwner"],
                            "tier": record["tier"],
                            "confidence": record["confidence"],
                        }
                    )

    needs = [d for d in decisions_needed]
    status = "NEEDS_INPUT" if needs else "ok"
    code = EXIT_NEEDS_INPUT if needs else EXIT_OK
    emit(
        {
            "status": status,
            "mode": "analyze",
            "credentials": credentials,
            "decisions_needed": needs,
            "note": (
                "proposedCreate false is plan-only; final YAML omits create. "
                "writeToStore is plan-only and never written to Credential YAML. "
                "No secret values included. Status NEEDS_INPUT until confirmed."
            ),
        },
        code,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
