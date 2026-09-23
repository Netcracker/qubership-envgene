"""Tests for pre_flight: dirty git tree + Store env-var validation."""

import subprocess

import pytest

from cred_migration.pre_flight import (
    PreFlightError,
    check_git_clean,
    check_store_auth_env,
    check_single_store,
)


# ---- Git dirty check ----

def _init_repo(tmp_path):
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)


def test_check_git_clean_returns_true_when_no_changes(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "f.yml").write_text("x: 1")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True)
    check_git_clean(tmp_path)  # no raise


def test_check_git_clean_raises_on_modified_tracked_file(tmp_path):
    _init_repo(tmp_path)
    f = tmp_path / "f.yml"
    f.write_text("x: 1")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True)
    f.write_text("x: 2")
    with pytest.raises(PreFlightError, match="dirty"):
        check_git_clean(tmp_path)


def test_check_git_clean_ignores_untracked_files(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "committed.yml").write_text("x: 1")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True)
    (tmp_path / "new.yml").write_text("y: 2")  # untracked
    check_git_clean(tmp_path)  # no raise per design (only tracked files matter)


# ---- Store auth env-var check ----

def test_check_store_auth_env_passes_when_all_vars_present(monkeypatch):
    monkeypatch.setenv("VAULT_ADDR", "https://vault")
    monkeypatch.setenv("VAULT_TOKEN", "t")
    check_store_auth_env(["vault"])  # no raise


def test_check_store_auth_env_raises_missing_var(monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.setenv("VAULT_ADDR", "https://vault")
    with pytest.raises(PreFlightError, match="VAULT_TOKEN"):
        check_store_auth_env(["vault"])


def test_check_store_auth_env_aws_needs_three_vars(monkeypatch):
    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(PreFlightError, match="AWS_ACCESS_KEY_ID"):
        check_store_auth_env(["aws"])


def test_check_store_auth_env_multiple_types_checked(monkeypatch):
    monkeypatch.setenv("VAULT_ADDR", "https://vault")
    monkeypatch.setenv("VAULT_TOKEN", "t")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(PreFlightError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        check_store_auth_env(["vault", "gcp"])


# ---- Single-store check (Assumption 1) ----

def test_check_single_store_passes_with_one_entry():
    check_single_store({"default_store": {"type": "vault", "mountPath": "kv"}})  # no raise


def test_check_single_store_raises_with_two_entries():
    with pytest.raises(PreFlightError, match="multiple"):
        check_single_store({"a": {"type": "vault"}, "b": {"type": "aws"}})
