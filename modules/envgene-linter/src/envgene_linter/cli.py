from __future__ import annotations

from pathlib import Path

import click

from .discovery import DiscoveryError
from .engine import run_check
from .html_report import ensure_report_ignored, report_path, render_html
from .report import render
from .rule_config import RuleConfigError


@click.group()
def main() -> None:
    pass


@main.command("check")
@click.argument("repo", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--console",
    is_flag=True,
    help="Also print findings in the console.",
)
def check_cmd(repo: Path, console: bool) -> None:
    """Check REPO (the current directory by default) and save an HTML report."""
    repo = repo.resolve()
    try:
        result = run_check(repo)
    except (DiscoveryError, RuleConfigError) as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2) from exc
    if console:
        click.echo(render(result.findings, disabled_rules=result.disabled_rules), nl=False)
    for note in result.skipped:
        click.echo(note, err=True)
    path = report_path(repo)
    try:
        path.write_text(
            render_html(result.findings, repo, disabled_rules=result.disabled_rules),
            encoding="utf-8",
        )
    except OSError as exc:
        click.echo(f"cannot write HTML report {path}: {exc}", err=True)
        raise SystemExit(2) from exc
    try:
        ensure_report_ignored(repo)
    except (OSError, UnicodeDecodeError) as exc:
        click.echo(f"cannot update .gitignore {repo / '.gitignore'}: {exc}", err=True)
    click.echo(f"Report saved to: {path}", err=True)
