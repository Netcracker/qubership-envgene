"""Tests for apply_cmd: apply orchestration."""

from pathlib import Path

import yaml

from cred_migration.apply_cmd import (
    rewrite_consumer_file,
    rewrite_source_files,
    run_apply,
)


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# collect_cred_descriptors logic moved to context_from_plan.build_context_from_repo;
# see tests/test_context_from_plan.py.


# ---- rewrite_source_files ----

def test_rewrite_source_files_updates_only_successful_creds(tmp_path):
    """Per-cred atomicity: failed creds leave their source entry untouched."""
    src = _make(
        tmp_path,
        "environments/credentials/global.yml",
        yaml.safe_dump(
            {
                "good-cred": {"type": "secret", "data": {"secret": "s"}},
                "bad-cred": {"type": "secret", "data": {"secret": "s"}},
            }
        ),
    )
    plan = {
        "credentials": [
            {
                "sourceFile": "environments/credentials/global.yml",
                "to_review": {},
                "to_confirm": {
                    "good-cred": {"remoteRefPath": "/external", "create": False, "writeToStore": True},
                    "bad-cred": {"remoteRefPath": "/external", "create": False, "writeToStore": True},
                },
            }
        ]
    }
    successful = {"good-cred"}
    rewrite_source_files(plan, tmp_path, successful)
    updated = yaml.safe_load(src.read_text())
    # good-cred rewritten
    assert updated["good-cred"]["type"] == "external"
    assert updated["good-cred"]["remoteRefPath"] == "/external"
    assert "data" not in updated["good-cred"]
    # bad-cred untouched
    assert updated["bad-cred"]["type"] == "secret"
    assert "data" in updated["bad-cred"]


# ---- rewrite_consumer_file ----

def test_rewrite_consumer_file_rewrites_deployparameters_macros(tmp_path):
    """Macros in deployParameters block become credRef structures."""
    f = _make(
        tmp_path,
        "consumer.yml",
        yaml.safe_dump(
            {
                "deployParameters": {"USER": "${creds.get('cred-a').username}"},
                "technicalConfigurationParameters": {"IGNORE": "${creds.get('cred-b').secret}"},
            }
        ),
    )
    rewrite_consumer_file(f)
    updated = yaml.safe_load(f.read_text())
    assert updated["deployParameters"]["USER"] == {
        "$type": "credRef", "credId": "cred-a", "property": "username"
    }
    # technicalConfigurationParameters untouched (Assumption 5)
    assert updated["technicalConfigurationParameters"]["IGNORE"] == "${creds.get('cred-b').secret}"


def test_rewrite_consumer_file_expands_hash_macro_in_deploy_parameters(tmp_path):
    f = _make(
        tmp_path,
        "consumer.yml",
        yaml.safe_dump({"deployParameters": {"#creds{U, P}": "app-db"}}),
    )
    rewrite_consumer_file(f)
    updated = yaml.safe_load(f.read_text())
    assert updated["deployParameters"] == {
        "U": {"$type": "credRef", "credId": "app-db", "property": "username"},
        "P": {"$type": "credRef", "credId": "app-db", "property": "password"},
    }


# ---- run_apply integration ----

def test_run_apply_template_creates_credential_template_file(tmp_path):
    """Template apply: no Credential Template exists → apply creates it under
    `templates/external-credentials/<descriptor-stem>.yml.j2` with type:external entries."""
    # Consumer template uses two cred macros with distinct fields.
    _make(
        tmp_path,
        "templates/env_templates/bss/cloud.yml.j2",
        yaml.safe_dump({
            "deployParameters": {
                "DB_USER": "${creds.get('app-db').username}",
                "DB_PASS": "${creds.get('app-db').password}",
                "TOKEN": "${creds.get('svc-token').secret}",
            }
        }),
    )
    # Template Descriptor for the solution (no external_credential_template field yet).
    _make(
        tmp_path,
        "templates/env_templates/bss.yaml",
        yaml.safe_dump({
            "tenant": "{{ templates_dir }}/env_templates/bss/tenant.yml.j2",
            "cloud": "{{ templates_dir }}/env_templates/bss/cloud.yml.j2",
        }),
    )
    _make(tmp_path, "templates/env_templates/bss/tenant.yml.j2", "name: t")
    plan_path = tmp_path / "migration-plan.yaml"
    plan_path.write_text(yaml.safe_dump({
        "repo_type": "template",
        "generated_at": "2026-08-05T12:00:00Z",
        "credentials": [
            {
                "sourceFile": "templates/external-credentials/bss.yml.j2",
                "to_review": {},
                "to_confirm": {
                    "app-db": {
                        "remoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.namespace }}",
                        "create": True,
                    },
                    "svc-token": {
                        "remoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.namespace }}",
                        "create": True,
                    },
                },
            }
        ],
        "to_delete": {},
    }))

    report = run_apply(plan_path=plan_path, repo_root=tmp_path, skip_pre_flight=True)
    assert report["store_writes"]["succeeded"] == 2

    # Credential Template created at the per-descriptor path.
    cred_template_file = tmp_path / "templates/external-credentials/bss.yml.j2"
    assert cred_template_file.exists()
    created = yaml.safe_load(cred_template_file.read_text())
    assert "app-db" in created and "svc-token" in created
    # Multi-field cred derived correctly.
    assert created["app-db"]["type"] == "external"
    assert created["app-db"]["properties"] == [{"name": "username"}, {"name": "password"}]
    # Single-value cred: no properties block.
    assert created["svc-token"]["type"] == "external"
    assert "properties" not in created["svc-token"]

    # Template Descriptor updated with external_credential_template field.
    updated_desc = yaml.safe_load((tmp_path / "templates/env_templates/bss.yaml").read_text())
    assert "external_credential_template" in updated_desc
    assert updated_desc["external_credential_template"].endswith("bss.yml.j2")


def test_run_apply_end_to_end_with_mock_cli(tmp_path, monkeypatch):
    """End-to-end: minimal apply, mocked external-cred-provision returns success for all creds."""
    # Setup: one source file + plan + secret-stores
    _make(
        tmp_path,
        "configuration/secret-stores.yml",
        yaml.safe_dump({"default_store": {"type": "vault", "mountPath": "kv"}}),
    )
    _make(
        tmp_path,
        "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml",
        yaml.safe_dump({"cred-a": {"type": "secret", "data": {"secret": "s"}}}),
    )
    _make(
        tmp_path,
        "environments/prod-cluster/env-a/Credentials/credentials.yml",
        yaml.safe_dump({"generated-placeholder": {"type": "secret", "data": {"secret": "x"}}}),
    )
    plan_path = tmp_path / "migration-plan.yaml"
    plan_path.write_text(yaml.safe_dump({
        "repo_type": "instance",
        "generated_at": "2026-08-05T12:00:00Z",
        "credentials": [
            {
                "sourceFile": "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml",
                "to_review": {},
                "to_confirm": {
                    "cred-a": {"remoteRefPath": "/prod-cluster", "create": False, "writeToStore": True}
                },
            }
        ],
        "to_delete": {
            "generated_env_credentials": ["environments/prod-cluster/env-a/Credentials/credentials.yml"]
        },
    }))

    # Mock external-cred-provision: return success marker for cred-a
    def mock_cli_runner(context_path, dry_run=False):
        return "[cred-a] overwritten\n", 0
    # No env-var/git checks in this test (bypass pre-flight)
    report = run_apply(
        plan_path=plan_path,
        repo_root=tmp_path,
        cli_runner=mock_cli_runner,
        skip_pre_flight=True,
    )
    assert report["store_writes"]["succeeded"] == 1
    assert report["store_writes"]["failed"] == 0
    # Source file rewritten
    updated_src = yaml.safe_load(
        (tmp_path / "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml").read_text()
    )
    assert updated_src["cred-a"]["type"] == "external"
    # Deleted file gone
    assert not (tmp_path / "environments/prod-cluster/env-a/Credentials/credentials.yml").exists()
