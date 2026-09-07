#!/usr/bin/env python3
"""Replace credential macros with $type: credRef (plan or apply)."""

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
    find_remaining_macros,
    load_yaml,
    walk_replace_macros,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.plan == args.apply:
        emit(
            {"status": "error", "error": "Specify exactly one of --plan or --apply"},
            EXIT_ERROR,
        )

    repo = args.repo.resolve()
    planned = []
    errors = []

    for rel in args.files:
        path = (repo / rel).resolve()
        if not path.is_file():
            errors.append(f"Missing file: {rel}")
            continue
        try:
            doc = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Parse failed {rel}: {exc}")
            continue

        changes: list = []
        skipped: list = []
        new_doc = walk_replace_macros(
            copy.deepcopy(doc),
            changes=changes,
            skipped_technical=skipped,
        )
        remaining = find_remaining_macros(new_doc)
        remaining_allowed = [r for r in remaining if not r.get("technical")]
        planned.append(
            {
                "file": rel,
                "replacements": changes,
                "skipped_technical": skipped,
                "remaining_after": remaining,
            }
        )
        if args.apply and changes:
            dump_yaml(new_doc, path)
        if remaining_allowed and args.apply:
            # after apply, leftover in allowed scopes is an error signal
            errors.append(
                f"{rel}: macros remain in non-technical scopes after apply"
            )

    if errors:
        emit({"status": "error", "errors": errors, "planned_changes": planned}, EXIT_ERROR)

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
