"""Tests for file_scanner: discovers source/consumer/to-delete files by glob."""

from pathlib import Path

from cred_migration.file_scanner import (
    find_source_cred_files_instance,
    find_source_cred_files_template,
    find_consumer_files_instance,
    find_consumer_files_template,
    find_generated_env_credentials,
    find_deployer_cred_files,
)


def _make(tmp_path, relpath, content=""):
    """Create a file under tmp_path at relpath (nested dirs auto-created)."""
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---- Instance-repo source file discovery ----

def test_find_source_cred_files_instance_collects_cloud_passport_creds(tmp_path):
    _make(tmp_path, "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml")
    _make(tmp_path, "environments/prod-cluster/cloud-passport/prod-cluster.yml")  # not -creds
    found = find_source_cred_files_instance(tmp_path)
    rels = {str(p.relative_to(tmp_path)) for p in found}
    assert "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml" in rels
    assert "environments/prod-cluster/cloud-passport/prod-cluster.yml" not in rels


def test_find_source_cred_files_instance_collects_shared_creds_all_scopes(tmp_path):
    _make(tmp_path, "environments/credentials/global.yml")
    _make(tmp_path, "environments/prod-cluster/credentials/cluster.yml")
    _make(tmp_path, "environments/prod-cluster/env-a/Inventory/credentials/env.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_source_cred_files_instance(tmp_path)}
    assert "environments/credentials/global.yml" in found
    assert "environments/prod-cluster/credentials/cluster.yml" in found
    assert "environments/prod-cluster/env-a/Inventory/credentials/env.yml" in found


def test_find_source_cred_files_instance_collects_system_credentials(tmp_path):
    _make(tmp_path, "configuration/credentials/credentials.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_source_cred_files_instance(tmp_path)}
    assert "configuration/credentials/credentials.yml" in found


def test_find_source_cred_files_instance_excludes_generated_env_credentials(tmp_path):
    """Generated env-scoped `Credentials/credentials.yml` is a to-delete target, not a source."""
    _make(tmp_path, "environments/prod-cluster/env-a/Credentials/credentials.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_source_cred_files_instance(tmp_path)}
    assert not any("Credentials/credentials.yml" in p for p in found)


# ---- Template-repo source file discovery ----

def test_find_source_cred_files_template_collects_credential_template(tmp_path):
    _make(tmp_path, "templates/env_templates/bss/external-credentials.yml.j2")
    _make(tmp_path, "templates/env_templates/bss/cloud.yml.j2")  # not a cred template
    found = {str(p.relative_to(tmp_path)) for p in find_source_cred_files_template(tmp_path)}
    assert "templates/env_templates/bss/external-credentials.yml.j2" in found
    assert "templates/env_templates/bss/cloud.yml.j2" not in found


# ---- To-delete file discovery ----

def test_find_generated_env_credentials_collects_all_env_scoped_files(tmp_path):
    _make(tmp_path, "environments/prod-cluster/env-a/Credentials/credentials.yml")
    _make(tmp_path, "environments/prod-cluster/env-b/Credentials/credentials.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_generated_env_credentials(tmp_path)}
    assert "environments/prod-cluster/env-a/Credentials/credentials.yml" in found
    assert "environments/prod-cluster/env-b/Credentials/credentials.yml" in found


def test_find_deployer_cred_files_collects_all_env_scoped_files(tmp_path):
    _make(tmp_path, "environments/prod-cluster/env-a/app-deployer/deployer-creds.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_deployer_cred_files(tmp_path)}
    assert "environments/prod-cluster/env-a/app-deployer/deployer-creds.yml" in found


# ---- Consumer file discovery ----

def test_find_consumer_files_instance_collects_cloud_passport_main(tmp_path):
    _make(tmp_path, "environments/prod-cluster/cloud-passport/prod-cluster.yml")
    _make(tmp_path, "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml")  # excluded
    found = {str(p.relative_to(tmp_path)) for p in find_consumer_files_instance(tmp_path)}
    assert "environments/prod-cluster/cloud-passport/prod-cluster.yml" in found
    assert "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml" not in found


def test_find_consumer_files_instance_collects_parametersets_all_scopes(tmp_path):
    _make(tmp_path, "environments/parameters/global.yml")
    _make(tmp_path, "environments/prod-cluster/parameters/cluster.yml")
    _make(tmp_path, "environments/prod-cluster/env-a/Inventory/parameters/env.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_consumer_files_instance(tmp_path)}
    for expected in [
        "environments/parameters/global.yml",
        "environments/prod-cluster/parameters/cluster.yml",
        "environments/prod-cluster/env-a/Inventory/parameters/env.yml",
    ]:
        assert expected in found


def test_find_consumer_files_template_collects_templates(tmp_path):
    _make(tmp_path, "templates/env_templates/bss/cloud.yml.j2")
    _make(tmp_path, "templates/env_templates/bss/namespace.yml.j2")
    _make(tmp_path, "templates/env_templates/bss/tenant.yml.j2")
    _make(tmp_path, "templates/parameters/area/paramset.yml")
    found = {str(p.relative_to(tmp_path)) for p in find_consumer_files_template(tmp_path)}
    for expected in [
        "templates/env_templates/bss/cloud.yml.j2",
        "templates/env_templates/bss/namespace.yml.j2",
        "templates/env_templates/bss/tenant.yml.j2",
        "templates/parameters/area/paramset.yml",
    ]:
        assert expected in found
