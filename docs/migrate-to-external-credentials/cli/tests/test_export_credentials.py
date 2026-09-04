"""Tests for export-credentials command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.export_credentials import ExportCredentials
from migration_cli.export_credentials.auth import resolve_jenkins_auth
from migration_cli.export_credentials.script_console import (
    SecretValue,
    UsernamePasswordValue,
    fetch_credential_value,
)

DEFAULT_URL = "https://jenkins.example.com"


def test_resolve_auth_default_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_USERNAME", "cloud-user")
    monkeypatch.setenv("CLOUD_TOKEN", "cloud-token")
    auth = resolve_jenkins_auth(jenkins_url=DEFAULT_URL)
    assert auth.username == "cloud-user"
    assert auth.token == "cloud-token"


def test_resolve_auth_custom_url_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JENKINS_USERNAME", raising=False)
    monkeypatch.delenv("JENKINS_TOKEN", raising=False)
    with pytest.raises(ValidationError, match="JENKINS_USERNAME"):
        resolve_jenkins_auth(jenkins_url="https://other-jenkins.example.com")


def test_fetch_username_password_parses_script_output() -> None:
    client = MagicMock()
    client.post_form.return_value = "USERNAME:demo-user\nPASSWORD:demo-pass\n"
    value = fetch_credential_value(
        client=client,
        cred_id="demo-id",
        cred_type="usernamePassword",
    )
    assert isinstance(value, UsernamePasswordValue)
    assert value.username == "demo-user"
    assert value.password == "demo-pass"


def test_fetch_secret_reports_not_found() -> None:
    client = MagicMock()
    client.post_form.return_value = "ERROR:not_found\n"
    with pytest.raises(MigrationCliError, match="not_found"):
        fetch_credential_value(client=client, cred_id="missing", cred_type="secret")


@patch("migration_cli.export_credentials.runner.fetch_credential_value")
@patch("migration_cli.export_credentials.runner.list_credentials")
@patch("migration_cli.export_credentials.runner.JenkinsHttpClient")
@patch("migration_cli.export_credentials.runner.resolve_jenkins_auth")
def test_export_writes_yaml(
    mock_auth: MagicMock,
    mock_client_cls: MagicMock,
    mock_list: MagicMock,
    mock_fetch: MagicMock,
    tmp_path: Path,
) -> None:
    from migration_cli.export_credentials.cm_api import CredentialRef

    mock_auth.return_value = MagicMock(username="u", token="t")
    mock_list.return_value = [
        CredentialRef(cred_id="DEMO-CLOUD-env-ID_A", cred_type="usernamePassword"),
        CredentialRef(cred_id="DEMO-CLOUD-env-token", cred_type="secret"),
    ]
    mock_fetch.side_effect = [
        UsernamePasswordValue(username="user-a", password='pass"quote'),
        SecretValue(secret="secret-value"),
    ]

    out_dir = tmp_path / "cmdb-export-credentials"
    ExportCredentials(
        tenants=["DEMO"],
        jenkins_url=DEFAULT_URL,
        out_dir=out_dir,
        username="u",
        token="t",
    ).run()

    out_file = out_dir / "shared-credentials.yml"
    data = yaml.safe_load(out_file.read_text(encoding="utf-8"))
    assert data["DEMO-CLOUD-env-ID_A"]["type"] == "usernamePassword"
    assert data["DEMO-CLOUD-env-ID_A"]["data"]["username"] == "user-a"
    assert data["DEMO-CLOUD-env-ID_A"]["data"]["password"] == 'pass"quote'
    assert data["DEMO-CLOUD-env-token"]["data"]["secret"] == "secret-value"


@patch("migration_cli.export_credentials.runner.list_credentials")
@patch("migration_cli.export_credentials.runner.JenkinsHttpClient")
@patch("migration_cli.export_credentials.runner.resolve_jenkins_auth")
def test_export_dry_run_skips_script_console(
    mock_auth: MagicMock,
    mock_client_cls: MagicMock,
    mock_list: MagicMock,
    tmp_path: Path,
) -> None:
    from migration_cli.export_credentials.cm_api import CredentialRef

    mock_auth.return_value = MagicMock(username="u", token="t")
    mock_list.return_value = [CredentialRef(cred_id="id-1", cred_type="secret")]

    out_dir = tmp_path / "out"
    ExportCredentials(
        tenants=["DEMO"],
        out_dir=out_dir,
        username="u",
        token="t",
        dry_run=True,
    ).run()

    assert not (out_dir / "shared-credentials.yml").exists()


@patch("migration_cli.export_credentials.runner.fetch_credential_value")
@patch("migration_cli.export_credentials.runner.list_credentials")
@patch("migration_cli.export_credentials.runner.JenkinsHttpClient")
@patch("migration_cli.export_credentials.runner.resolve_jenkins_auth")
def test_export_partial_failure_exits_with_error(
    mock_auth: MagicMock,
    mock_client_cls: MagicMock,
    mock_list: MagicMock,
    mock_fetch: MagicMock,
    tmp_path: Path,
) -> None:
    from migration_cli.export_credentials.cm_api import CredentialRef

    mock_auth.return_value = MagicMock(username="u", token="t")
    mock_list.return_value = [
        CredentialRef(cred_id="good", cred_type="secret"),
        CredentialRef(cred_id="bad", cred_type="secret"),
    ]
    mock_fetch.side_effect = [
        SecretValue(secret="ok"),
        MigrationCliError("Failed to fetch 'bad': ERROR:not_found"),
    ]

    with pytest.raises(MigrationCliError, match="1 failed"):
        ExportCredentials(
            tenants=["DEMO"],
            out_dir=tmp_path / "out",
            username="u",
            token="t",
        ).run()

    data = yaml.safe_load((tmp_path / "out" / "shared-credentials.yml").read_text(encoding="utf-8"))
    assert "good" in data
    assert "bad" not in data


def test_export_config_multi_tenant(tmp_path: Path) -> None:
    config = tmp_path / "export-config.yml"
    config.write_text(
        "exports:\n"
        "  - tenant: DEMO\n"
        "    out_file: demo.yml\n"
        "  - tenant: ACME\n"
        "    out_file: acme.yml\n"
        "    jenkins_url: https://jenkins.example.com\n"
        "    username: acme-user\n"
        "    token: acme-token\n",
        encoding="utf-8",
    )

    with (
        patch("migration_cli.export_credentials.runner.fetch_credential_value") as mock_fetch,
        patch("migration_cli.export_credentials.runner.list_credentials") as mock_list,
        patch("migration_cli.export_credentials.runner.JenkinsHttpClient"),
        patch("migration_cli.export_credentials.runner.resolve_jenkins_auth") as mock_auth,
    ):
        mock_auth.return_value = MagicMock(username="u", token="t")
        mock_list.return_value = []
        out_dir = tmp_path / "exports"
        ExportCredentials(config=config, out_dir=out_dir).run()
        assert mock_list.call_count == 2
        assert (out_dir / "demo.yml").exists()
        assert (out_dir / "acme.yml").exists()
        mock_fetch.assert_not_called()


def test_export_multiple_tenants_writes_separate_files(tmp_path: Path) -> None:
    with (
        patch("migration_cli.export_credentials.runner.fetch_credential_value") as mock_fetch,
        patch("migration_cli.export_credentials.runner.list_credentials") as mock_list,
        patch("migration_cli.export_credentials.runner.JenkinsHttpClient"),
        patch("migration_cli.export_credentials.runner.resolve_jenkins_auth") as mock_auth,
    ):
        mock_auth.return_value = MagicMock(username="u", token="t")
        mock_list.return_value = []
        out_dir = tmp_path / "exports"
        ExportCredentials(
            tenants=["DEMO", "ACME"],
            out_dir=out_dir,
            username="u",
            token="t",
        ).run()
        assert mock_list.call_count == 2
        assert (out_dir / "DEMO-shared-credentials.yml").exists()
        assert (out_dir / "ACME-shared-credentials.yml").exists()
        mock_fetch.assert_not_called()


def test_parse_tenant_values_comma_and_repeat() -> None:
    from migration_cli.export_credentials.tenants import parse_tenant_values

    assert parse_tenant_values(("DEMO,ACME", "ACME", "FOO")) == ["DEMO", "ACME", "FOO"]
