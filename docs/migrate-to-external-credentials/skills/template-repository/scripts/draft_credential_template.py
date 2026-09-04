#!/usr/bin/env python3
"""Draft external-credentials.yml.j2 from confirmed credential decisions only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_SECRET_STORE,
    DEFAULT_TEMPLATE_PATH,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    base_external_entry,
    dump_yaml,
    emit,
    path_contains_cred_id,
)


def build_entry(
    structure: str,
    *,
    secret_store: str,
    proposed_create: bool,
    remote_ref_path: str,
) -> dict[str, Any]:
    entry = base_external_entry(remote_ref_path=remote_ref_path, secret_store=secret_store)
    # false -> omit field in final YAML
    if proposed_create is True:
        entry["create"] = True
    if structure == "multi_field":
        entry["properties"] = [{"name": "username"}, {"name": "password"}]
    elif structure == "single_value":
        pass
    else:
        raise ValueError(f"Cannot draft entry with structure={structure}")
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--credentials-json",
        required=True,
        help=(
            "JSON list of confirmed records: credId, structure, creationOwner, "
            "proposedCreate (bool), proposedRemoteRefPath, needsReview=false, "
            "confidence=confirmed"
        ),
    )
    parser.add_argument("--secret-store", default=DEFAULT_SECRET_STORE)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.plan == args.apply:
        emit(
            {"status": "error", "error": "Specify exactly one of --plan or --apply"},
            EXIT_ERROR,
        )

    repo = args.repo.resolve()
    try:
        creds = json.loads(args.credentials_json)
    except json.JSONDecodeError as exc:
        emit({"status": "error", "error": f"Invalid JSON: {exc}"}, EXIT_ERROR)

    if not isinstance(creds, list):
        emit({"status": "error", "error": "credentials-json must be a list"}, EXIT_ERROR)

    doc: dict[str, Any] = {}
    blocked = []
    planned = []
    for item in creds:
        cred_id = item.get("credId")
        structure = item.get("structure")
        owner = item.get("creationOwner")
        prop_create = item.get("proposedCreate")
        path = item.get("proposedRemoteRefPath") or DEFAULT_TEMPLATE_PATH
        needs_review = item.get("needsReview", True)
        confidence = item.get("confidence", "proposed")

        if needs_review is True or confidence == "ambiguous":
            blocked.append(
                {
                    "id": f"review:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: needsReview/ambiguous - refuse draft.",
                    "evidence": item.get("evidence"),
                }
            )
            continue
        if owner in (None, "unknown"):
            blocked.append(
                {
                    "id": f"owner:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: creationOwner unknown - refuse draft.",
                }
            )
            continue
        if structure not in ("multi_field", "single_value"):
            blocked.append(
                {
                    "id": f"structure:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: structure must be multi_field or single_value",
                }
            )
            continue
        if prop_create is None:
            blocked.append(
                {
                    "id": f"create:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: proposedCreate null - refuse draft.",
                }
            )
            continue
        if owner in ("pre-existing", "provider") and prop_create is True:
            blocked.append(
                {
                    "id": f"create_conflict:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: {owner} must not use create:true.",
                }
            )
            continue
        if owner == "envgene" and prop_create is not True:
            blocked.append(
                {
                    "id": f"envgene_create:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": f"{cred_id}: envgene requires proposedCreate true.",
                }
            )
            continue
        if "{{ current_env.namespace }}" in str(path):
            blocked.append(
                {
                    "id": f"namespace:{cred_id}",
                    "status": "NEEDS_INPUT",
                    "message": (
                        f"{cred_id}: {{ current_env.namespace }} is not allowed "
                        "without implementation proof."
                    ),
                }
            )
            continue
        if path_contains_cred_id(str(path), str(cred_id)):
            blocked.append(
                {
                    "id": f"path_credId:{cred_id}",
                    "status": "error",
                    "message": f"{cred_id}: remoteRefPath must not include credId.",
                }
            )
            continue

        entry = build_entry(
            structure,
            secret_store=args.secret_store,
            proposed_create=bool(prop_create),
            remote_ref_path=str(path),
        )
        doc[cred_id] = entry
        planned.append(
            {
                "credId": cred_id,
                "entry": entry,
                "plan": {
                    "create": prop_create,
                    "creationOwner": owner,
                    "note": "create:false in plan -> omit in YAML",
                },
            }
        )

    if any(b.get("status") == "error" for b in blocked):
        emit(
            {"status": "error", "decisions_needed": blocked, "planned_changes": planned},
            EXIT_ERROR,
        )
    if blocked:
        emit(
            {
                "status": "NEEDS_INPUT",
                "mode": "plan" if args.plan else "apply",
                "planned_changes": planned,
                "decisions_needed": blocked,
            },
            EXIT_NEEDS_INPUT,
        )

    out_path = repo / args.output
    if args.apply:
        dump_yaml(doc, out_path)

    emit(
        {
            "status": "ok",
            "mode": "plan" if args.plan else "apply",
            "output": args.output,
            "planned_changes": planned,
            "written": bool(args.apply),
        },
        EXIT_OK,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
