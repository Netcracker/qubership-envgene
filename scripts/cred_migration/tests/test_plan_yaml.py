"""Tests for plan_yaml: build + validate + I/O."""

import pytest

from cred_migration.plan_yaml import (
    PlanValidationError,
    build_cred_entry,
    build_source_group,
    build_plan,
    dump_plan,
    load_plan,
    validate_plan,
)


# ---- build_cred_entry ----

def test_build_cred_entry_instance_repo_includes_write_to_store():
    entry = build_cred_entry(
        remote_ref_path="/prod-cluster/env-a/bss",
        create=True,
        write_to_store=True,
        suggestions=None,
    )
    assert entry == {
        "remoteRefPath": "/prod-cluster/env-a/bss",
        "create": True,
        "writeToStore": True,
    }


def test_build_cred_entry_template_repo_omits_write_to_store():
    entry = build_cred_entry(
        remote_ref_path="{{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.namespace }}",
        create=True,
        write_to_store=None,
        suggestions=None,
    )
    assert "writeToStore" not in entry


def test_build_cred_entry_includes_suggestions_when_present():
    entry = build_cred_entry(
        remote_ref_path="/prod-cluster",
        create=False,
        write_to_store=True,
        suggestions=["if platform-shared: set remoteRefPath to /prod-cluster"],
    )
    assert entry["suggestions"] == ["if platform-shared: set remoteRefPath to /prod-cluster"]


def test_build_cred_entry_omits_empty_suggestions():
    entry = build_cred_entry(
        remote_ref_path="/external", create=False, write_to_store=True, suggestions=[]
    )
    assert "suggestions" not in entry


# ---- build_source_group + build_plan ----

def test_build_source_group_partitions_by_review_and_confirm():
    to_review = {"arango-db-creds": {"remoteRefPath": "/p/e/b", "create": True, "writeToStore": True}}
    to_confirm = {"dbaas": {"remoteRefPath": "/p", "create": False, "writeToStore": True}}
    group = build_source_group(
        source_file="environments/prod/env-a/Inventory/credentials/arango.yml",
        to_review=to_review,
        to_confirm=to_confirm,
    )
    assert group == {
        "sourceFile": "environments/prod/env-a/Inventory/credentials/arango.yml",
        "to_review": to_review,
        "to_confirm": to_confirm,
    }


def test_build_plan_composes_top_level_structure():
    plan = build_plan(
        repo_type="instance",
        generated_at="2026-08-05T12:00:00Z",
        credentials=[
            {"sourceFile": "f", "to_review": {}, "to_confirm": {"c": {"remoteRefPath": "/x", "create": False, "writeToStore": True}}},
        ],
        to_delete={"generated_env_credentials": ["a", "b"]},
    )
    assert plan == {
        "repo_type": "instance",
        "generated_at": "2026-08-05T12:00:00Z",
        "credentials": [
            {"sourceFile": "f", "to_review": {}, "to_confirm": {"c": {"remoteRefPath": "/x", "create": False, "writeToStore": True}}},
        ],
        "to_delete": {"generated_env_credentials": ["a", "b"]},
    }


# ---- validate_plan ----

def test_validate_plan_accepts_minimal_valid_instance_plan():
    plan = {
        "repo_type": "instance",
        "generated_at": "2026-08-05T12:00:00Z",
        "credentials": [],
        "to_delete": {},
    }
    validate_plan(plan)  # no raise


def test_validate_plan_rejects_missing_repo_type():
    with pytest.raises(PlanValidationError, match="repo_type"):
        validate_plan({"credentials": [], "to_delete": {}})


def test_validate_plan_rejects_unknown_repo_type():
    with pytest.raises(PlanValidationError, match="repo_type"):
        validate_plan({"repo_type": "bogus", "credentials": [], "to_delete": {}})


def test_validate_plan_rejects_group_missing_source_file():
    plan = {
        "repo_type": "instance",
        "credentials": [{"to_review": {}, "to_confirm": {}}],
        "to_delete": {},
    }
    with pytest.raises(PlanValidationError, match="sourceFile"):
        validate_plan(plan)


def test_validate_plan_rejects_entry_missing_remote_ref_path():
    plan = {
        "repo_type": "instance",
        "credentials": [
            {"sourceFile": "f", "to_review": {}, "to_confirm": {"c": {"create": False, "writeToStore": True}}}
        ],
        "to_delete": {},
    }
    with pytest.raises(PlanValidationError, match="remoteRefPath"):
        validate_plan(plan)


# ---- dump_plan / load_plan round-trip ----

def test_dump_plan_and_load_plan_round_trip(tmp_path):
    plan = {
        "repo_type": "template",
        "generated_at": "2026-08-05T12:00:00Z",
        "credentials": [
            {
                "sourceFile": "templates/env_templates/bss/external-credentials.yml.j2",
                "to_review": {},
                "to_confirm": {
                    "app-db-cred": {
                        "remoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}",
                        "create": True,
                    },
                },
            }
        ],
        "to_delete": {},
    }
    path = tmp_path / "migration-plan.yaml"
    dump_plan(plan, path)
    loaded = load_plan(path)
    assert loaded == plan
