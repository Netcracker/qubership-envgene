#!/usr/bin/env python3
"""Strip .yml/.yaml from sharedMasterCredentialFiles values (plan or apply)."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

from common import (
    EXIT_ERROR,
    EXIT_OK,
    dump_yaml,
    emit,
    find_env_definitions,
    load_yaml,
)


def normalize_name(value: str) -> tuple[str, bool]:
    if value.endswith(".yml"):
        return value[:-4], True
    if value.endswith(".yaml"):
        return value[:-5], True
    return value, False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--env-definitions",
        nargs="*",
        help="Optional relative env_definition paths; default = all",
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
    if args.env_definitions:
        paths = [(repo / p).resolve() for p in args.env_definitions]
    else:
        paths = find_env_definitions(repo)

    planned = []
    for path in paths:
        if not path.is_file():
            emit({"status": "error", "error": f"Missing: {path}"}, EXIT_ERROR)
        rel = str(path.relative_to(repo).as_posix())
        doc = load_yaml(path) or {}
        env_template = doc.get("envTemplate") or {}
        shared = env_template.get("sharedMasterCredentialFiles")
        if shared is None:
            continue
        changed = False
        new_shared: list[str] | str
        file_changes = []
        if isinstance(shared, str):
            new_val, did = normalize_name(shared)
            new_shared = new_val
            if did:
                changed = True
                file_changes.append({"from": shared, "to": new_val})
        elif isinstance(shared, list):
            new_list = []
            for item in shared:
                if not isinstance(item, str):
                    new_list.append(item)
                    continue
                new_val, did = normalize_name(item)
                new_list.append(new_val)
                if did:
                    changed = True
                    file_changes.append({"from": item, "to": new_val})
            new_shared = new_list
        else:
            continue

        if not changed:
            planned.append({"file": rel, "changes": [], "action": "noop"})
            continue

        planned.append({"file": rel, "changes": file_changes, "action": "fix"})
        if args.apply:
            new_doc = copy.deepcopy(doc)
            new_doc.setdefault("envTemplate", {})["sharedMasterCredentialFiles"] = new_shared
            dump_yaml(new_doc, path)

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
