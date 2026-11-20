from __future__ import annotations

from pathlib import Path

import click

from .discovery import DiscoveryError
from .engine import run_check
from .html_report import ensure_report_ignored, render_html, report_path
from .report import JSON_REPORT_FILENAME, render, render_json
from .rule_config import RuleConfigError


@click.group()
def main() -> None:
    pass


@main.command("check")
@click.argument(
    "repo",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "-i",
    "--instance-repo",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Instance repository to check. Use instead of REPO.",
)
@click.option(
    "--console",
    is_flag=True,
    help="Also print findings in the console.",
)
@click.option(
    "-t",
    "--template-repo",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Compare PLACE-12 candidates with local template sources (repository root or templates directory).",
)
def check_cmd(
    repo: Path | None,
    instance_repo: Path | None,
    console: bool,
    template_repo: Path | None,
) -> None:
    """Check REPO or --instance-repo (the current directory by default) and save HTML and JSON reports."""
    if repo is not None and instance_repo is not None:
        raise click.UsageError("Use either REPO or --instance-repo/-i, not both.")
    repo = (instance_repo or repo or Path(".")).resolve()
    try:
        result = run_check(repo, template_repo=template_repo)
    except (DiscoveryError, RuleConfigError) as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2) from exc
    if console:
        click.echo(
            render(
                result.findings,
                disabled_rules=result.disabled_rules,
                not_applicable_rules=result.not_applicable_rules,
            ),
            nl=False,
        )
    for note in result.skipped:
        click.echo(note, err=True)
    reports = (
        ("HTML", report_path(repo), render_html, {"skipped": result.skipped}),
        (
            "JSON",
            repo / JSON_REPORT_FILENAME,
            render_json,
            {"skipped_checks": result.skipped_checks},
        ),
    )
    for label, path, renderer, extra in reports:
        try:
            path.write_text(
                renderer(
                    result.findings,
                    repo,
                    disabled_rules=result.disabled_rules,
                    not_applicable_rules=result.not_applicable_rules,
                    **extra,
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            click.echo(f"cannot write {label} report {path}: {exc}", err=True)
            raise SystemExit(2) from exc
    try:
        ensure_report_ignored(repo, JSON_REPORT_FILENAME)
    except (OSError, UnicodeDecodeError) as exc:
        click.echo(f"cannot update .gitignore {repo / '.gitignore'}: {exc}", err=True)
    for label, path, _, _ in reports:
        click.echo(f"{label} report saved here: {path}", err=True)
