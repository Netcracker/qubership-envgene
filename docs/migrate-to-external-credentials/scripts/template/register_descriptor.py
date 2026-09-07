#!/usr/bin/env python3
"""Set external_credential_template on Template Descriptors (plan or apply)."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

from common import EXIT_ERROR, EXIT_OK, dump_yaml, emit, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--descriptor", required=True, help="Relative descriptor path")
    parser.add_argument(
        "--template-path",
        required=True,
        help='Value to set, e.g. "{{ templates_dir }}/external-credentials/<descriptor-stem>.yml.j2"',
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
    path = (repo / args.descriptor).resolve()
    if not path.is_file():
        emit({"status": "error", "error": f"Missing descriptor: {args.descriptor}"}, EXIT_ERROR)

    # Credential template file must exist
    # Map {{ templates_dir }}/... -> templates/...
    fs_rel = args.template_path.replace("{{ templates_dir }}", "templates")
    cred_file = repo / fs_rel
    if not cred_file.is_file():
        emit(
            {
                "status": "error",
                "error": (
                    f"Credential Template missing at {fs_rel}. "
                    "Run draft_credential_template.py first."
                ),
            },
            EXIT_ERROR,
        )

    doc = load_yaml(path) or {}
    old = doc.get("external_credential_template")
    planned = {
        "file": args.descriptor,
        "from": old,
        "to": args.template_path,
        "action": "noop" if old == args.template_path else "set",
    }
    if args.apply and planned["action"] == "set":
        new_doc = copy.deepcopy(doc)
        new_doc["external_credential_template"] = args.template_path
        dump_yaml(new_doc, path)

    emit(
        {
            "status": "ok",
            "mode": "plan" if args.plan else "apply",
            "planned_changes": [planned],
            "written": bool(args.apply) and planned["action"] == "set",
        },
        EXIT_OK,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
