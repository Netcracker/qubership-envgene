"""Tests for the migrate.py CLI dispatcher."""

import subprocess
import sys

import yaml


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "cred_migration.migrate"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_cli_requires_repo_flag(tmp_path):
    """Missing --repo → exit code non-zero."""
    result = _run(["plan"], cwd=tmp_path)
    assert result.returncode != 0
    assert "--repo" in result.stderr.lower() or "required" in result.stderr.lower()


def test_cli_plan_writes_migration_plan_yaml(tmp_path):
    """plan subcommand walks repo, writes migration-plan.yaml in CWD."""
    _make(
        tmp_path,
        "environments/credentials/global.yml",
        yaml.safe_dump({"webex-token-cred": {"type": "secret", "data": {"secret": "s"}}}),
    )
    result = _run(["plan", "--repo=instance"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    plan_file = tmp_path / "migration-plan.yaml"
    assert plan_file.exists()
    plan = yaml.safe_load(plan_file.read_text())
    assert plan["repo_type"] == "instance"
    assert plan["credentials"]


def test_cli_plan_template_repo(tmp_path):
    """plan --repo=template scans templates/ tree."""
    _make(
        tmp_path,
        "templates/env_templates/bss/external-credentials.yml.j2",
        yaml.safe_dump({"app-db-cred": {"type": "usernamePassword", "data": {"username": "u", "password": "p"}}}),
    )
    result = _run(["plan", "--repo=template"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    plan = yaml.safe_load((tmp_path / "migration-plan.yaml").read_text())
    assert plan["repo_type"] == "template"


def test_cli_plan_rejects_unknown_repo_type(tmp_path):
    result = _run(["plan", "--repo=bogus"], cwd=tmp_path)
    assert result.returncode != 0
