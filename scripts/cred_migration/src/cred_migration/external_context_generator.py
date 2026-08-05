#!/usr/bin/env python3
"""Standalone CLI: plan + repo → CLI-context YAML for external-cred-provision.

Called by `envgene-migrate apply` during migration; also available for operator debug runs.
The produced YAML feeds directly into `external-cred-provision`.

Repo state expected: `plan` step already run (migration-plan.yaml present), Secret Store
configured (`configuration/secret-stores.yml` present), source cred files still contain `data`
(apply Git rewrites not yet applied).

Usage (from repo root):
    envgene-external-context-generator [--out <path>]

With explicit paths:
    envgene-external-context-generator --plan <migration-plan.yaml> --repo <repo-root> [--out <path>]

Exit codes:
    0  success (context emitted; skipped creds warned on stderr, non-fatal)
    2  input malformed (plan invalid, missing files, multi-store violation)
"""

import argparse
import sys
from pathlib import Path

import yaml

from .context_from_plan import build_context_from_repo
from .plan_yaml import PlanValidationError, load_plan
from .pre_flight import PreFlightError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", default="migration-plan.yaml",
                        help="Path to migration-plan.yaml (default: migration-plan.yaml in CWD)")
    parser.add_argument("--repo", default=".",
                        help="Repository root directory (default: current working directory)")
    parser.add_argument("--out", help="Write context YAML to this file instead of stdout")
    args = parser.parse_args(argv)

    plan_path = Path(args.plan)
    repo_root = Path(args.repo)
    if not plan_path.exists():
        print(f"error: plan file not found: {plan_path}", file=sys.stderr)
        return 2
    if not repo_root.exists():
        print(f"error: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    try:
        plan = load_plan(plan_path)
    except (PlanValidationError, yaml.YAMLError) as exc:
        print(f"error: invalid plan: {exc}", file=sys.stderr)
        return 2

    try:
        context, skipped = build_context_from_repo(plan, repo_root)
    except (PreFlightError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if skipped:
        for cred_id in skipped:
            print(f"warning: skipped {cred_id!r} (envgeneNullValue placeholder in source data)",
                  file=sys.stderr)

    output = yaml.safe_dump(context, sort_keys=False, default_flow_style=False, allow_unicode=True)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
