#!/usr/bin/env python3
"""Delete generated Credentials/credentials.yml|yaml for given environments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import EXIT_ERROR, EXIT_OK, emit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--environments",
        nargs="+",
        required=True,
        help="cluster/env identifiers, e.g. cluster/env",
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
    planned = []
    errors = []

    for env_key in args.environments:
        if "/" not in env_key:
            errors.append(f"Invalid environment id (expected cluster/env): {env_key}")
            continue
        cluster, env = env_key.split("/", 1)
        deleted = []
        for name in ("credentials.yml", "credentials.yaml"):
            path = repo / "environments" / cluster / env / "Credentials" / name
            rel = str(path.relative_to(repo).as_posix())
            if path.is_file():
                deleted.append(rel)
                if args.apply:
                    path.unlink()
        planned.append(
            {
                "environment": env_key,
                "delete": deleted,
                "action": "delete" if deleted else "noop",
            }
        )

    if errors:
        emit({"status": "error", "errors": errors, "planned_changes": planned}, EXIT_ERROR)

    emit(
        {
            "status": "ok",
            "mode": "plan" if args.plan else "apply",
            "planned_changes": planned,
            "written": bool(args.apply),
            "note": "Only generated Credentials/credentials.yml|yaml are deleted.",
        },
        EXIT_OK,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
