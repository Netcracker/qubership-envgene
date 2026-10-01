"""Orchestrate Jenkins credential export to YAML."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.export_credentials.auth import resolve_jenkins_auth
from migration_cli.export_credentials.cm_api import list_credentials
from migration_cli.export_credentials.config import ExportJob, load_export_config
from migration_cli.export_credentials.http_client import JenkinsHttpClient
from migration_cli.export_credentials.script_console import (
    credential_entry_payload,
    fetch_credential_value,
)
from migration_cli.yaml_io import dump_yaml

log = logging.getLogger(__name__)


@dataclass
class ExportResult:
    written: int = 0
    skipped: int = 0
    failed: list[str] = field(default_factory=list)


@dataclass
class ExportCredentials:
    out_dir: Path
    tenants: list[str] | None = None
    jenkins_url: str | None = None
    out_file: str = "shared-credentials.yml"
    config: Path | None = None
    username: str | None = None
    token: str | None = None
    username_env: str | None = None
    token_env: str | None = None
    insecure: bool = False
    continue_on_error: bool = False
    dry_run: bool = False
    limit: int | None = None

    def run(self) -> None:
        jobs = self._resolve_jobs()
        total_failed: list[str] = []

        for job in jobs:
            result = self._export_job(job)
            total_failed.extend(result.failed)

        if total_failed:
            log.error("The following credential(s) could not be fetched and were skipped:")
            for cred_id in total_failed:
                log.error("  - %s", cred_id)
            raise MigrationCliError(
                f"Export finished with {len(total_failed)} failed credential(s)."
            )

    def _resolve_jobs(self) -> list[ExportJob]:
        if self.config is not None:
            if self.tenants:
                raise ValidationError("Use either --config or --tenant, not both.")
            return load_export_config(self.config)

        if not self.tenants:
            raise ValidationError("Provide --tenant or --config.")

        from migration_cli.export_credentials.auth import DEFAULT_JENKINS_URL

        jenkins_url = self.jenkins_url or DEFAULT_JENKINS_URL
        multi_tenant = len(self.tenants) > 1
        if multi_tenant and self.out_file != "shared-credentials.yml":
            raise ValidationError(
                "With multiple --tenant values, omit --out-file "
                "(each tenant writes {tenant}-shared-credentials.yml)."
            )

        jobs: list[ExportJob] = []
        for tenant in self.tenants:
            out_file = self.out_file if not multi_tenant else f"{tenant}-shared-credentials.yml"
            jobs.append(
                ExportJob(
                    tenant=tenant,
                    jenkins_url=jenkins_url,
                    out_file=out_file,
                    username=self.username,
                    token=self.token,
                    username_env=self.username_env,
                    token_env=self.token_env,
                )
            )
        return jobs

    def _export_job(self, job: ExportJob) -> ExportResult:
        log.info("Fetching credential list for tenant %r ...", job.tenant)
        auth = resolve_jenkins_auth(
            jenkins_url=job.jenkins_url,
            username=job.username or self.username,
            token=job.token or self.token,
            username_env=job.username_env or self.username_env,
            token_env=job.token_env or self.token_env,
        )
        client = JenkinsHttpClient(jenkins_url=job.jenkins_url, auth=auth, insecure=self.insecure)

        refs = list_credentials(client=client, tenant=job.tenant)
        if not refs:
            log.warning("No credentials returned from CM API for tenant %r.", job.tenant)
            out_path = self.out_dir / job.out_file
            dump_yaml(out_path, {})
            log.info("Wrote empty export to %s", out_path)
            return ExportResult()

        if self.limit is not None:
            refs = refs[: self.limit]

        log.info("Found %d credential(s) to process for tenant %r.", len(refs), job.tenant)

        if self.dry_run:
            for ref in refs:
                log.info("  [dry-run] %s (type: %s)", ref.cred_id, ref.cred_type)
            return ExportResult(skipped=len(refs))

        credentials: dict[str, dict[str, object]] = {}
        result = ExportResult()

        for ref in refs:
            log.info("Processing %r (type: %s) ...", ref.cred_id, ref.cred_type)
            try:
                value = fetch_credential_value(
                    client=client,
                    cred_id=ref.cred_id,
                    cred_type=ref.cred_type,  # type: ignore[arg-type]
                )
                credentials[ref.cred_id] = credential_entry_payload(
                    ref.cred_type,  # type: ignore[arg-type]
                    value,
                )
                result.written += 1
                log.info("Written: %s", ref.cred_id)
            except MigrationCliError as exc:
                log.error("%s", exc)
                result.failed.append(ref.cred_id)

        out_path = self.out_dir / job.out_file
        dump_yaml(out_path, credentials)
        log.info("Wrote %d credential(s) to %s", result.written, out_path)
        return result
