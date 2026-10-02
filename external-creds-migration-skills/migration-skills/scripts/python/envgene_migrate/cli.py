"""CLI entry: plan | apply | strip-technical-macros | check-template-version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exit_codes import (
    EXIT_APPLY_FAILED,
    EXIT_INTERRUPT,
    EXIT_OK,
    EXIT_PLAN_INVALID,
    REPO_INSTANCE,
    REPO_TEMPLATE,
)
from .preflight import PreflightError, check_dirty_git, exit_preflight


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envgene_migrate",
        description="EnvGene External Credentials migration (plan / apply)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Scan repo; write migration-plan.yaml")
    plan.add_argument(
        "--repo",
        required=True,
        choices=(REPO_TEMPLATE, REPO_INSTANCE),
        help="Repository type (required)",
    )
    plan.add_argument(
        "--root",
        default=".",
        help="Repository root (default: cwd)",
    )
    plan.add_argument(
        "--env",
        default=None,
        metavar="CLUSTER/ENV",
        help=(
            "Instance only: limit scan to one environment (debug). "
            "Default is the whole repository."
        ),
    )
    plan.add_argument(
        "--verbose",
        action="store_true",
        help="List auto entries and extra detail (default: summary only)",
    )
    plan.add_argument(
        "--manual",
        action="store_true",
        help=(
            "Human CLI run: do not print reply prompts. "
            "Omit when an agent runs this command."
        ),
    )

    apply = sub.add_parser("apply", help="Apply migration-plan.yaml")
    apply.add_argument(
        "--repo",
        required=True,
        choices=(REPO_TEMPLATE, REPO_INSTANCE),
        help="Repository type (required)",
    )
    apply.add_argument(
        "--root",
        default=".",
        help="Repository root (default: cwd)",
    )
    apply.add_argument(
        "--dry-run",
        action="store_true",
        help="Propagate dry-run to Store CLI; no Git writes",
    )
    apply.add_argument(
        "--verbose",
        action="store_true",
        help="Per-cred progress on stderr (default: summary only)",
    )
    apply.add_argument(
        "--manual",
        action="store_true",
        help=(
            "Human CLI run: do not print reply prompts. "
            "Omit when an agent runs this command."
        ),
    )

    check_tv = sub.add_parser(
        "check-template-version",
        help="Verify envTemplate.artifact matches --expect in all env_definition files",
    )
    check_tv.add_argument(
        "--repo",
        required=True,
        choices=(REPO_INSTANCE,),
        help="Repository type (instance only)",
    )
    check_tv.add_argument(
        "--root",
        default=".",
        help="Repository root (default: cwd)",
    )
    check_tv.add_argument(
        "--expect",
        required=True,
        help="Expected envTemplate.artifact value (published Template version)",
    )

    strip = sub.add_parser(
        "strip-technical-macros",
        help=(
            "Template only: remove credential macros under "
            "technicalConfigurationParameters (from migration-plan.yaml hits)"
        ),
    )
    strip.add_argument(
        "--repo",
        required=True,
        choices=(REPO_TEMPLATE,),
        help="Repository type (template only)",
    )
    strip.add_argument(
        "--root",
        default=".",
        help="Repository root (default: cwd)",
    )
    strip.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed; do not write files",
    )
    return p


def _cmd_check_template_version(root: Path, expect: str) -> int:
    from .instance.check_template_version import check_template_versions

    ok, lines = check_template_versions(root, expect)
    for line in lines:
        print(line, flush=True)
    if ok:
        print("[CHECK] template version OK", flush=True)
        return EXIT_OK
    print("[CHECK] FAILED: envTemplate.artifact mismatch or missing", flush=True)
    return EXIT_PLAN_INVALID


def _cmd_strip_technical_macros(root: Path, dry_run: bool) -> int:
    from .template.strip_technical import strip_technical_macros

    try:
        files_touched, macros_removed, errors = strip_technical_macros(
            root, cwd=root, dry_run=dry_run
        )
    except FileNotFoundError as exc:
        print(f"[STRIP] FAILED: {exc}", flush=True)
        return EXIT_PLAN_INVALID
    except ValueError as exc:
        print(f"[STRIP] FAILED: {exc}", flush=True)
        return EXIT_PLAN_INVALID

    for err in errors:
        print(f"[STRIP] FAILED: {err}", flush=True)
    if errors:
        return EXIT_APPLY_FAILED

    mode = "dry-run" if dry_run else "done"
    print(
        f"[STRIP] {mode}: files={files_touched} macros_removed={macros_removed}",
        flush=True,
    )
    if macros_removed == 0 and files_touched == 0:
        print(
            "[STRIP] No runtime_credential_macros in plan "
            "(or nothing removable). Re-run plan if unsure.",
            flush=True,
        )
    return EXIT_OK


def _cmd_plan(
    repo: str, root: Path, env_filter: str | None, verbose: bool, manual: bool
) -> int:
    if repo == REPO_TEMPLATE:
        from .template.plan_schema import write_plan
        from .template.reports import emit_plan_report, set_manual, set_verbose

        set_verbose(verbose)
        set_manual(manual)
        if env_filter:
            print("[PLAN] FAILED: --env is only valid with --repo=instance", flush=True)
            return EXIT_PLAN_INVALID
        from .template.plan import build_template_plan

        plan = build_template_plan(root)
    else:
        from .instance.plan_schema import write_plan
        from .instance.reports import emit_plan_report, set_manual, set_verbose

        set_verbose(verbose)
        set_manual(manual)
        from .instance.plan import build_instance_plan

        try:
            plan = build_instance_plan(root, env_filter=env_filter)
        except ValueError as exc:
            print(f"[PLAN] FAILED: {exc}", flush=True)
            return EXIT_PLAN_INVALID

    path = write_plan(plan, cwd=root)
    emit_plan_report(plan, repo_label=f"{repo} repo {root.name}")
    print(f"(plan file: {path})", flush=True)
    if plan.get("plan_errors"):
        return EXIT_PLAN_INVALID
    return EXIT_OK


def _cmd_apply(
    repo: str, root: Path, dry_run: bool, verbose: bool, manual: bool
) -> int:
    try:
        check_dirty_git(root)
    except PreflightError as exc:
        return exit_preflight(exc)

    if repo == REPO_TEMPLATE:
        from .template.plan_schema import read_plan
        from .template.reports import emit_migration_report, set_manual, set_verbose

        set_verbose(verbose)
        set_manual(manual)
    else:
        from .instance.plan_schema import read_plan
        from .instance.reports import emit_migration_report, set_manual, set_verbose

        set_verbose(verbose)
        set_manual(manual)

    try:
        plan = read_plan(cwd=root)
    except FileNotFoundError as exc:
        print(f"[APPLY] FAILED: {exc}", flush=True)
        return EXIT_PLAN_INVALID

    if plan.get("repo_type") and plan.get("repo_type") != repo:
        print(
            f"[APPLY] FAILED: plan repo_type={plan.get('repo_type')!r} "
            f"does not match --repo={repo}",
            flush=True,
        )
        return EXIT_PLAN_INVALID

    try:
        if repo == REPO_TEMPLATE:
            from .template.apply import apply_template_plan

            stats = apply_template_plan(root, plan)
            emit_migration_report(
                repo_label=f"template repo {root.name}",
                store_ok=0,
                store_fail=0,
                git_ok=stats.get("git_ok", 0),
                git_fail=0,
                macro_ok=stats.get("macro_ok", 0),
                macro_fail=0,
            )
        else:
            from .instance.apply import apply_instance_plan

            try:
                stats = apply_instance_plan(root, plan, dry_run=dry_run)
            except PreflightError as exc:
                return exit_preflight(exc)
            emit_migration_report(
                repo_label=f"instance repo {root.name}",
                store_ok=stats.get("store_ok", 0),
                store_fail=stats.get("store_fail", 0),
                git_ok=stats.get("git_ok", 0),
                git_fail=stats.get("git_fail", 0),
                macro_ok=stats.get("macro_ok", 0),
                macro_fail=stats.get("macro_fail", 0),
                warnings=stats.get("warnings"),
            )
            if stats.get("store_fail") or stats.get("git_fail") or stats.get("macro_fail"):
                return EXIT_APPLY_FAILED
    except ValueError as exc:
        print(f"[APPLY] FAILED: {exc}", flush=True)
        msg = str(exc)
        if (
            "unsupported cred type" in msg
            or "already type: external" in msg
            or "mixed local and external" in msg
            or "Cyrillic" in msg
        ):
            return EXIT_PLAN_INVALID
        return EXIT_APPLY_FAILED
    except RuntimeError as exc:
        print(f"[APPLY] FAILED: {exc}", flush=True)
        return EXIT_APPLY_FAILED

    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    verbose = bool(getattr(args, "verbose", False))
    manual = bool(getattr(args, "manual", False))
    root = Path(args.root).resolve()
    try:
        if args.command == "plan":
            return _cmd_plan(
                args.repo, root, getattr(args, "env", None), verbose, manual
            )
        if args.command == "apply":
            return _cmd_apply(
                args.repo, root, getattr(args, "dry_run", False), verbose, manual
            )
        if args.command == "check-template-version":
            return _cmd_check_template_version(root, args.expect)
        if args.command == "strip-technical-macros":
            return _cmd_strip_technical_macros(
                root, bool(getattr(args, "dry_run", False))
            )
        parser.error("unknown command")
        return EXIT_PLAN_INVALID
    except KeyboardInterrupt:
        print("Interrupted.", flush=True)
        return EXIT_INTERRUPT


if __name__ == "__main__":
    sys.exit(main())
