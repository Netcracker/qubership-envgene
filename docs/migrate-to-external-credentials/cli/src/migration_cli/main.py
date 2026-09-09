"""Click entrypoint for migration-cli."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from migration_cli.collect import CollectCredentialValues
from migration_cli.errors import MigrationCliError
from migration_cli.export_credentials import ExportCredentials
from migration_cli.fill import FillExternalCredentialContext, FillRepositoryContexts


def _setup_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(levelname)-5s] %(message)s",
        stream=sys.stdout,
    )


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
)
@click.pass_context
def cli(ctx: click.Context, log_level: str) -> None:
    """Collect, export, and fill credential values for External Credentials migration."""
    _setup_logging(log_level)
    ctx.ensure_object(dict)


@cli.command("collect")
@click.option("--instance-root", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--out", required=True, type=click.Path(path_type=Path))
@click.option("--env-filter", default=None, help="Comma-separated cluster/env keys.")
@click.option(
    "--secret-key",
    default=None,
    envvar="SECRET_KEY",
    help="Fernet SECRET_KEY for field-level encrypted credentials.",
)
def collect_cmd(
    instance_root: Path, out: Path, env_filter: str | None, secret_key: str | None
) -> None:
    """Collect local Credential plaintext into a tiered values YAML file."""
    try:
        CollectCredentialValues(
            instance_root=instance_root,
            out=out,
            env_filter=env_filter,
            secret_key=secret_key,
        ).run()
    except MigrationCliError as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


@cli.command("fill")
@click.option("--context", default=None, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--repo-root", default=None, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--values", default=None, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--values-dir", default=None, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--values-format",
    required=True,
    type=click.Choice(["instance_scoped", "jenkins_export"], case_sensitive=False),
)
@click.option("--out", required=True, type=click.Path(path_type=Path))
@click.option("--tenant", default=None, help="Jenkins tenant prefix (optional with --values-dir).")
@click.option("--cloud", default=None, help="Jenkins cloud prefix (optional with --values-dir).")
@click.option("--env-filter", default=None, help="Repo mode: comma-separated cluster/env keys.")
@click.option("--continue-on-error", is_flag=True, help="Repo mode: keep processing after env errors.")
@click.option(
    "--partial",
    is_flag=True,
    help=(
        "Write matched credentials even when some fail_if_absent entries miss. "
        "Also writes an unmatched report (see --report). Exit code is still non-zero."
    ),
)
@click.option(
    "--report",
    default=None,
    type=click.Path(path_type=Path),
    help="Unmatched report path when using --partial (default: <out>-unmatched.yaml).",
)
@click.option(
    "--seed-strategy",
    default="create_if_absent",
    show_default=True,
    type=click.Choice(["create_if_absent", "overwrite"], case_sensitive=False),
)
def fill_cmd(
    context: Path | None,
    repo_root: Path | None,
    values: Path | None,
    values_dir: Path | None,
    values_format: str,
    out: Path,
    tenant: str | None,
    cloud: str | None,
    env_filter: str | None,
    continue_on_error: bool,
    partial: bool,
    report: Path | None,
    seed_strategy: str,
) -> None:
    """Fill fail_if_absent Context entries from local values or Jenkins exports."""
    if context is None and repo_root is None:
        raise click.UsageError("Provide --context for one env or --repo-root for the whole repository")
    if context is not None and repo_root is not None:
        raise click.UsageError("Use either --context or --repo-root, not both")
    if values is None and values_dir is None:
        raise click.UsageError("Provide --values or --values-dir")

    try:
        if repo_root is not None:
            FillRepositoryContexts(
                repo_root=repo_root,
                values=values,
                values_dir=values_dir,
                values_format=values_format.lower(),
                out=out,
                tenant=tenant,
                cloud=cloud,
                seed_strategy=seed_strategy,
                env_filter=env_filter,
                continue_on_error=continue_on_error,
                partial=partial,
                report=report,
            ).run()
        else:
            FillExternalCredentialContext(
                context=context,
                values=values,
                values_dir=values_dir,
                values_format=values_format.lower(),
                out=out,
                tenant=tenant,
                cloud=cloud,
                seed_strategy=seed_strategy,
                partial=partial,
                report=report,
            ).run()
    except MigrationCliError as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


@cli.command("export-credentials")
@click.option(
    "--tenant",
    "tenants",
    multiple=True,
    help="CMDB tenant name. Repeat the flag or comma-separate: --tenant DEMO,ACME.",
)
@click.option(
    "--jenkins-url",
    default=None,
    help="Jenkins base URL. Default: https://jenkins.example.com",
)
@click.option(
    "--out-dir",
    default="cmdb-export-credentials",
    show_default=True,
    type=click.Path(path_type=Path),
)
@click.option(
    "--out-file",
    default="shared-credentials.yml",
    show_default=True,
    help="Output filename inside --out-dir (single --tenant only).",
)
@click.option("--config", default=None, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--username", default=None, help="Jenkins username override.")
@click.option(
    "--token",
    default=None,
    envvar="JENKINS_TOKEN",
    help="Jenkins API token override (prefer env vars).",
)
@click.option("--username-env", default=None, help="Env var name for username (config jobs).")
@click.option("--token-env", default=None, help="Env var name for token (config jobs).")
@click.option("--insecure", is_flag=True, help="Skip TLS certificate verification.")
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Accepted for pipeline compatibility; export still exits 1 when any credential fails.",
)
@click.option("--dry-run", is_flag=True, help="List credentials from CM API without Script Console.")
@click.option("--limit", default=None, type=int, help="Process at most N credentials (debug).")
def export_credentials_cmd(
    tenants: tuple[str, ...],
    jenkins_url: str | None,
    out_dir: Path,
    out_file: str,
    config: Path | None,
    username: str | None,
    token: str | None,
    username_env: str | None,
    token_env: str | None,
    insecure: bool,
    continue_on_error: bool,
    dry_run: bool,
    limit: int | None,
) -> None:
    """Export Jenkins credential plaintext into YAML for fill --values-format jenkins_export."""
    from migration_cli.export_credentials.tenants import parse_tenant_values

    if continue_on_error:
        logging.getLogger(__name__).warning(
            "--continue-on-error is accepted for pipeline compatibility; export still exits 1 on failures."
        )
    try:
        ExportCredentials(
            tenants=parse_tenant_values(tenants) or None,
            jenkins_url=jenkins_url,
            out_dir=out_dir,
            out_file=out_file,
            config=config,
            username=username,
            token=token,
            username_env=username_env,
            token_env=token_env,
            insecure=insecure,
            continue_on_error=continue_on_error,
            dry_run=dry_run,
            limit=limit,
        ).run()
    except MigrationCliError as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc
