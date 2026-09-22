from __future__ import annotations

import sys
from pathlib import Path

import click

from .discovery import DiscoveryError
from .engine import run_check
from .html_report import ensure_report_ignored, report_path, render_html
from .report import render


@click.group()
def main() -> None:
    pass


@main.command("check")
@click.argument("repo", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--html",
    "write_html",
    is_flag=True,
    help="Write envgene-linter-report.html in the repository root and ignore it.",
)
def check_cmd(repo: Path, write_html: bool) -> None:
    try:
        result = run_check(repo)
    except DiscoveryError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2) from exc
    click.echo(render(result.findings), nl=False)
    for note in result.skipped:
        click.echo(note, err=True)
    if not write_html:
        return
    path = report_path(repo)
    try:
        path.write_text(render_html(result.findings, repo), encoding="utf-8")
    except OSError as exc:
        click.echo(f"cannot write HTML report {path}: {exc}", err=True)
        raise SystemExit(2) from exc
    try:
        ensure_report_ignored(repo)
    except (OSError, UnicodeDecodeError) as exc:
        click.echo(f"cannot update .gitignore {repo / '.gitignore'}: {exc}", err=True)
    click.echo("Wrote HTML report to envgene-linter-report.html", err=True)
