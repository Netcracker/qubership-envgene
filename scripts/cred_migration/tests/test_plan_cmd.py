"""Tests for plan_cmd: plan generation orchestration."""

from pathlib import Path

import yaml

from cred_migration.plan_cmd import compute_tier_defaults, generate_plan


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---- compute_tier_defaults ----

def test_compute_tier_defaults_passport_uses_cluster_only_path():
    """passport-tier default: remoteRefPath=/<cluster>, create=false."""
    defaults = compute_tier_defaults(
        tier="passport-tier",
        cluster="prod-cluster",
        env=None,
        namespace=None,
    )
    assert defaults == {"remote_ref_path": "/prod-cluster", "create": False}


def test_compute_tier_defaults_env_uses_cluster_env_ns_path():
    """env-tier default: /<cluster>/<env>/<ns>, create=true."""
    defaults = compute_tier_defaults(
        tier="env-tier",
        cluster="prod-cluster",
        env="env-a",
        namespace="bss",
    )
    assert defaults == {
        "remote_ref_path": "/prod-cluster/env-a/bss",
        "create": True,
    }


def test_compute_tier_defaults_external_uses_literal_external_path():
    """external-tier default: /external, create=false."""
    defaults = compute_tier_defaults(
        tier="external-tier",
        cluster=None,
        env=None,
        namespace=None,
    )
    assert defaults == {"remote_ref_path": "/external", "create": False}


# ---- generate_plan (integration) ----

def test_generate_plan_instance_repo_builds_correct_structure(tmp_path):
    """End-to-end: minimal instance repo → plan with tier-classified entries + to_delete."""
    # A Cloud Passport cred file → passport-tier
    _make(
        tmp_path,
        "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml",
        yaml.safe_dump(
            {"dbaas-cluster-dba-creds": {"type": "usernamePassword", "data": {"username": "u", "password": "p"}}}
        ),
    )
    # A repo-scoped Shared cred → external-tier
    _make(
        tmp_path,
        "environments/credentials/global.yml",
        yaml.safe_dump(
            {"webex-token-cred": {"type": "secret", "data": {"secret": "s"}}}
        ),
    )
    # A generated env-scoped file → to_delete.generated_env_credentials
    _make(
        tmp_path,
        "environments/prod-cluster/env-a/Credentials/credentials.yml",
        yaml.safe_dump({"placeholder": {"type": "secret", "data": {"secret": "x"}}}),
    )
    # A deployer creds file → to_delete.deployer_credentials
    _make(
        tmp_path,
        "environments/prod-cluster/env-a/app-deployer/deployer-creds.yml",
        yaml.safe_dump({"deployer-c": {"type": "secret", "data": {"secret": "y"}}}),
    )
    # A consumer that references the shared cred (so it stays in-scope, not orphaned)
    _make(
        tmp_path,
        "environments/parameters/global-ps.yml",
        yaml.safe_dump(
            {"deployParameters": {"WEBEX": "${creds.get('webex-token-cred').secret}"}}
        ),
    )

    plan = generate_plan(
        repo_root=tmp_path, repo_type="instance", generated_at="2026-08-05T12:00:00Z"
    )

    assert plan["repo_type"] == "instance"
    assert plan["generated_at"] == "2026-08-05T12:00:00Z"

    # Two source-file groups
    source_files = [g["sourceFile"] for g in plan["credentials"]]
    assert any("cloud-passport" in sf for sf in source_files)
    assert any("environments/credentials" in sf for sf in source_files)

    # Passport-tier: dbaas-cluster-dba-creds should have platform-pattern signal → to_review
    for group in plan["credentials"]:
        if "cloud-passport" in group["sourceFile"]:
            assert "dbaas-cluster-dba-creds" in group["to_review"]
            entry = group["to_review"]["dbaas-cluster-dba-creds"]
            assert entry["remoteRefPath"] == "/prod-cluster"
            assert entry["create"] is False
            assert entry["writeToStore"] is True
            assert "suggestions" in entry

    # External-tier: webex-token-cred has no signals → to_confirm
    for group in plan["credentials"]:
        if "environments/credentials" in group["sourceFile"]:
            assert "webex-token-cred" in group["to_confirm"]

    # to_delete: generated + deployer files listed
    assert any(
        "Credentials/credentials.yml" in p
        for p in plan["to_delete"].get("generated_env_credentials", [])
    )
    assert any(
        "app-deployer/deployer-creds.yml" in p
        for p in plan["to_delete"].get("deployer_credentials", [])
    )


def test_generate_plan_template_repo_discovers_cred_ids_from_consumers(tmp_path):
    """Template phase: descriptor + referenced templates → cred-ids grouped in a per-descriptor
    Credential Template file under `templates/external-credentials/<stem>.yml.j2`."""
    # Descriptor referencing cloud + namespace templates.
    _make(
        tmp_path,
        "templates/env_templates/bss.yaml",
        yaml.safe_dump({
            "tenant": "{{ templates_dir }}/env_templates/bss/tenant.yml.j2",
            "cloud": "{{ templates_dir }}/env_templates/bss/cloud.yml.j2",
            "namespaces": [
                {"name": "core", "template_path": "{{ templates_dir }}/env_templates/bss/namespace.yml.j2"},
            ],
        }),
    )
    _make(tmp_path, "templates/env_templates/bss/tenant.yml.j2", "name: t")
    _make(
        tmp_path,
        "templates/env_templates/bss/cloud.yml.j2",
        "deployParameters:\n  DB_USER: \"${creds.get('app-db').username}\"\n  DB_PASS: \"${creds.get('app-db').password}\"",
    )
    _make(
        tmp_path,
        "templates/env_templates/bss/namespace.yml.j2",
        "deployParameters:\n  T: \"${creds.get('token-cred').secret}\"",
    )
    plan = generate_plan(
        repo_root=tmp_path, repo_type="template", generated_at="2026-08-05T12:00:00Z"
    )
    # One group per descriptor, sourceFile in the common external-credentials dir.
    assert len(plan["credentials"]) == 1
    group = plan["credentials"][0]
    assert group["sourceFile"] == "templates/external-credentials/bss.yml.j2"
    all_creds = {**group["to_review"], **group["to_confirm"]}
    assert set(all_creds.keys()) == {"app-db", "token-cred"}
    for entry in all_creds.values():
        assert entry["remoteRefPath"] == "{{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.namespace }}"
        assert entry["create"] is True
        # writeToStore is NOT emitted for template plans (per Template-phase specifics).
        assert "writeToStore" not in entry


def test_generate_plan_flags_orphaned_shared_cred_file(tmp_path):
    """Shared cred file whose creds are never referenced ends up in to_delete.unused_shared_credentials."""
    _make(
        tmp_path,
        "environments/credentials/orphaned.yml",
        yaml.safe_dump({"unused-cred": {"type": "secret", "data": {"secret": "x"}}}),
    )
    # No consumer references unused-cred anywhere.
    plan = generate_plan(
        repo_root=tmp_path, repo_type="instance", generated_at="2026-08-05T12:00:00Z"
    )
    orphans = plan["to_delete"].get("unused_shared_credentials", [])
    assert any("orphaned.yml" in p for p in orphans)
