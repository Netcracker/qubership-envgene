#!/usr/bin/env python3
"""Migration CLI dispatcher.

Usage:
    python migrate.py plan --repo=<instance|template>
    python migrate.py apply --repo=<instance|template> [--dry-run]

Reads the current working directory as the repository root; writes migration-plan.yaml to CWD.

Exit codes:
    0  success
    1  apply failed (Store write / Git rewrite / verification)
    2  plan invalid / unknown repo type / unsupported cred type
    3  pre-flight failed (missing env vars / SOPS key / dirty tree / multi-store)
    130 user interrupt (SIGINT)
"""

import argparse
import datetime
import sys
from pathlib import Path

import yaml

from .apply_cmd import run_apply
from .plan_cmd import generate_plan
from .plan_yaml import dump_plan, PlanValidationError
from .pre_flight import PreFlightError
from .source_rewriter import PartialMigrationError, UnsupportedCredTypeError


def _now_iso():
    """UTC timestamp as ISO-8601 string."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cmd_plan(args):
    repo_root = Path.cwd()
    plan = generate_plan(
        repo_root=repo_root,
        repo_type=args.repo,
        generated_at=_now_iso(),
    )
    plan_path = repo_root / "migration-plan.yaml"
    dump_plan(plan, plan_path)
    n_creds = sum(
        len(g.get("to_review") or {}) + len(g.get("to_confirm") or {})
        for g in plan["credentials"]
    )
    n_review = sum(len(g.get("to_review") or {}) for g in plan["credentials"])
    print(f"[PLAN] {args.repo} repo scan complete")
    print(f"Wrote plan -> {plan_path.name}")
    print(f"Summary: {n_creds} credentials, {n_review} flagged for review")
    return 0


def _cmd_apply(args):
    repo_root = Path.cwd()
    plan_path = repo_root / "migration-plan.yaml"
    if not plan_path.exists():
        print(f"error: {plan_path.name} not found in {repo_root}", file=sys.stderr)
        return 2

    try:
        report = run_apply(
            plan_path=plan_path,
            repo_root=repo_root,
            dry_run=args.dry_run,
        )
    except PreFlightError as exc:
        print(f"error: pre-flight failed: {exc}", file=sys.stderr)
        return 3
    except (PartialMigrationError, UnsupportedCredTypeError, PlanValidationError) as exc:
        print(f"error: plan invalid: {exc}", file=sys.stderr)
        return 2

    print(f"[APPLY] {args.repo} repo migration {'(dry-run)' if args.dry_run else ''}")
    writes = report["store_writes"]
    print(f"Store writes: {writes['succeeded']} succeeded, {writes['failed']} failed")
    if writes.get("skipped_envgene_null_value"):
        print(f"Skipped (envgeneNullValue): {writes['skipped_envgene_null_value']}")
    if report["failed_creds"]:
        for cid, reason in report["failed_creds"].items():
            print(f"  [{cid}] FAILED: {reason}", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="migrate", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    parser_plan = sub.add_parser("plan", help="Scan repo, write migration-plan.yaml")
    parser_plan.add_argument("--repo", required=True, choices=["instance", "template"])

    parser_apply = sub.add_parser("apply", help="Read migration-plan.yaml, apply migration")
    parser_apply.add_argument("--repo", required=True, choices=["instance", "template"])
    parser_apply.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "plan":
            return _cmd_plan(args)
        if args.cmd == "apply":
            return _cmd_apply(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
