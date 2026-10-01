"""Multi-tenant export configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.export_credentials.auth import DEFAULT_JENKINS_URL
from migration_cli.yaml_io import load_yaml


@dataclass(frozen=True)
class ExportJob:
    tenant: str
    jenkins_url: str = DEFAULT_JENKINS_URL
    out_file: str = "shared-credentials.yml"
    username: str | None = None
    token: str | None = None
    username_env: str | None = None
    token_env: str | None = None


def _job_from_mapping(raw: dict[str, Any]) -> ExportJob:
    tenant = raw.get("tenant")
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValidationError("Each export job requires a non-empty 'tenant' field.")

    jenkins_url = raw.get("jenkins_url", DEFAULT_JENKINS_URL)
    if not isinstance(jenkins_url, str) or not jenkins_url.strip():
        raise ValidationError(f"Invalid jenkins_url for tenant {tenant!r}.")

    out_file = raw.get("out_file", "shared-credentials.yml")
    if not isinstance(out_file, str) or not out_file.strip():
        raise ValidationError(f"Invalid out_file for tenant {tenant!r}.")

    username = raw.get("username")
    token = raw.get("token")
    username_env = raw.get("username_env")
    token_env = raw.get("token_env")

    for field_name, value in (
        ("username", username),
        ("token", token),
        ("username_env", username_env),
        ("token_env", token_env),
    ):
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"Invalid {field_name} for tenant {tenant!r}.")

    return ExportJob(
        tenant=tenant.strip(),
        jenkins_url=jenkins_url.strip(),
        out_file=out_file.strip(),
        username=username,
        token=token,
        username_env=username_env,
        token_env=token_env,
    )


def load_export_config(path: Path) -> list[ExportJob]:
    try:
        doc = load_yaml(path)
    except (OSError, yaml.YAMLError) as exc:
        raise MigrationCliError(f"Failed to load export config {path}: {exc}") from exc

    if not isinstance(doc, dict):
        raise MigrationCliError(f"Export config must be a YAML mapping: {path}")

    exports = doc.get("exports")
    if not isinstance(exports, list) or not exports:
        raise ValidationError(f"Export config must contain a non-empty 'exports' list: {path}")

    return [_job_from_mapping(item) for item in exports if isinstance(item, dict)]
