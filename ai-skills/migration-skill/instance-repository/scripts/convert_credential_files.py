#!/usr/bin/env python3
"""Convert local Credential YAML to type external using confirmed decisions only."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from common import (
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    classify_path,
    dump_yaml,
    emit,
    iter_credential_entries,
    load_yaml,
    path_contains_cred_id,
)


def load_decisions(path: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    """Map (sourcePath, credId) -> confirmed decision record."""
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "credentials" in raw:
        items = raw["credentials"]
    elif isinstance(raw, list):
        items = raw
    else:
        raise ValueError("decisions JSON must be a list or {credentials: [...]}")
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        key = (item["sourcePath"], item["credId"])
        out[key] = item
    return out


def yaml_create_field(proposed_create: bool | None) -> bool | None:
    """Return True to set create:true; None to omit field. Never emit false."""
    if proposed_create is True:
        return True
    return None


def convert_with_decision(
    cred_id: str,
    entry: dict[str, Any],
    decision: dict[str, Any],
    *,
    secret_store: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if entry.get("type") == "external":
        return None, None
    if entry.get("type") not in ("usernamePassword", "secret"):
        return None, {
            "id": f"unsupported:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: type {entry.get('type')!r} is not auto-converted.",
        }

    if decision.get("needsReview") is True:
        return None, {
            "id": f"needsReview:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: needsReview true - refuse convert.",
            "evidence": decision.get("evidence"),
        }
    if decision.get("confidence") == "ambiguous":
        return None, {
            "id": f"ambiguous:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: confidence ambiguous - refuse convert.",
        }
    if decision.get("creationOwner") in (None, "unknown"):
        return None, {
            "id": f"owner:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: creationOwner unknown - refuse convert.",
        }

    path = decision.get("proposedRemoteRefPath") or entry.get("remoteRefPath")
    if not path:
        return None, {
            "id": f"path:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: remoteRefPath required and missing.",
        }
    if path_contains_cred_id(str(path), cred_id):
        return None, {
            "id": f"path_credId:{cred_id}",
            "status": "error",
            "message": f"{cred_id}: remoteRefPath must not include credId.",
        }

    owner = decision.get("creationOwner")
    prop_create = decision.get("proposedCreate")
    scope = decision.get("scope")

    if scope == "system" or owner == "pre-existing" and scope == "system":
        pass
    if scope == "system" and prop_create is True:
        return None, {
            "id": f"system_create:{cred_id}",
            "status": "error",
            "message": f"{cred_id}: System Credentials must not use create:true.",
        }
    if owner in ("pre-existing", "provider") and prop_create is True:
        return None, {
            "id": f"create_conflict:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: {owner} must not use create:true.",
        }
    if prop_create is None:
        return None, {
            "id": f"create:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: proposedCreate null - refuse convert.",
        }

    # Final YAML: true stays; false is omitted
    create_yaml = yaml_create_field(prop_create if owner == "envgene" else False)
    if owner == "envgene" and prop_create is not True:
        return None, {
            "id": f"envgene_create:{cred_id}",
            "status": "NEEDS_INPUT",
            "message": f"{cred_id}: envgene owner requires proposedCreate true.",
        }
    if scope == "system":
        create_yaml = None

    new_entry: dict[str, Any] = {
        "type": "external",
        "secretStore": entry.get("secretStore") or secret_store,
        "remoteRefPath": path,
    }
    if create_yaml is True:
        new_entry["create"] = True
    if entry.get("type") == "usernamePassword":
        new_entry["properties"] = [{"name": "username"}, {"name": "password"}]
    return new_entry, None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--secret-store", default="default_store")
    parser.add_argument(
        "--decisions-json",
        type=Path,
        required=True,
        help=(
            "JSON list of confirmed decision records "
            "(confidence=confirmed, needsReview=false, known owner+path)."
        ),
    )
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
        decisions = load_decisions(args.decisions_json.resolve())
    except Exception as exc:  # noqa: BLE001
        emit({"status": "error", "error": f"Invalid decisions JSON: {exc}"}, EXIT_ERROR)

    planned = []
    blocked = []
    errors = []

    for rel in args.files:
        path = (repo / rel).resolve()
        if not path.is_file():
            errors.append(f"Missing file: {rel}")
            continue
        cls = classify_path(path, repo)
        try:
            doc = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Parse failed {rel}: {exc}")
            continue
        if not isinstance(doc, dict):
            errors.append(f"{rel}: expected mapping root")
            continue

        new_doc = copy.deepcopy(doc)
        file_changes = []
        for cred_id, entry in iter_credential_entries(doc):
            key = (rel, cred_id)
            decision = decisions.get(key)
            if decision is None:
                blocked.append(
                    {
                        "id": f"missing_decision:{rel}:{cred_id}",
                        "status": "NEEDS_INPUT",
                        "credId": cred_id,
                        "sourcePath": rel,
                        "message": "No confirmed decision record for this Credential.",
                    }
                )
                continue
            new_entry, problem = convert_with_decision(
                cred_id,
                entry,
                decision,
                secret_store=args.secret_store,
            )
            if problem:
                if problem.get("status") == "error":
                    errors.append(problem["message"])
                else:
                    blocked.append({**problem, "file": rel, "credId": cred_id})
                continue
            if new_entry is None:
                file_changes.append(
                    {"credId": cred_id, "action": "skip_already_external"}
                )
                continue
            plan_create = decision.get("proposedCreate")
            file_changes.append(
                {
                    "credId": cred_id,
                    "action": "convert",
                    "from_type": entry.get("type"),
                    "to": new_entry,
                    "plan": {
                        "create": plan_create,
                        "writeToStore": decision.get("writeToStore"),
                        "creationOwner": decision.get("creationOwner"),
                        "tier": decision.get("tier"),
                        "note": (
                            "create:false in plan -> omit create in YAML; "
                            "writeToStore never written to YAML"
                        ),
                    },
                }
            )
            new_doc[cred_id] = new_entry

        planned.append({"file": rel, "class": cls, "changes": file_changes})
        if (
            args.apply
            and not blocked
            and not errors
            and any(c["action"] == "convert" for c in file_changes)
        ):
            dump_yaml(new_doc, path)

    if errors:
        emit(
            {"status": "error", "errors": errors, "planned_changes": planned, "blocked": blocked},
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

    emit(
        {
            "status": "ok",
            "mode": "plan" if args.plan else "apply",
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
