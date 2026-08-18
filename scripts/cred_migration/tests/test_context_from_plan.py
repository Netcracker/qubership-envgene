"""Tests for context_from_plan: plan + repo → CLI-context dict."""

import pytest
import yaml

from cred_migration.context_from_plan import build_context_from_repo
from cred_migration.pre_flight import PreFlightError


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def _setup_stores(tmp_path):
    _make(tmp_path, "configuration/secret-stores.yml",
          yaml.safe_dump({"default_store": {"type": "vault", "mountPath": "kv"}}))


def test_build_context_from_repo_composes_context_from_source_data(tmp_path):
    _setup_stores(tmp_path)
    _make(tmp_path, "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml",
          yaml.safe_dump({"cred-a": {"type": "usernamePassword",
                                     "data": {"username": "u", "password": "p"}}}))
    plan = {
        "credentials": [{
            "sourceFile": "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml",
            "to_review": {},
            "to_confirm": {"cred-a": {"remoteRefPath": "/prod-cluster", "create": False,
                                       "writeToStore": True}},
        }]
    }
    context, skipped = build_context_from_repo(plan, tmp_path)
    assert skipped == []
    assert context == {
        "credentials": {
            "cred-a": {
                "vals": "ref+vault://kv/data/prod-cluster/cred-a",
                "strategy": "overwrite",
                "data": {"username": "u", "password": "p"},
            }
        }
    }


def test_build_context_from_repo_skips_write_to_store_false(tmp_path):
    _setup_stores(tmp_path)
    _make(tmp_path, "environments/credentials/global.yml",
          yaml.safe_dump({"c": {"type": "secret", "data": {"secret": "s"}}}))
    plan = {
        "credentials": [{
            "sourceFile": "environments/credentials/global.yml",
            "to_review": {},
            "to_confirm": {"c": {"remoteRefPath": "/external", "create": False,
                                  "writeToStore": False}},
        }]
    }
    context, skipped = build_context_from_repo(plan, tmp_path)
    assert context == {"credentials": {}}
    assert skipped == []


def test_build_context_from_repo_collects_envgene_null_value_as_skipped(tmp_path):
    _setup_stores(tmp_path)
    _make(tmp_path, "environments/credentials/global.yml",
          yaml.safe_dump({"c": {"type": "usernamePassword",
                                 "data": {"username": "envgeneNullValue",
                                          "password": "envgeneNullValue"}}}))
    plan = {
        "credentials": [{
            "sourceFile": "environments/credentials/global.yml",
            "to_review": {},
            "to_confirm": {"c": {"remoteRefPath": "/external", "create": False,
                                  "writeToStore": True}},
        }]
    }
    context, skipped = build_context_from_repo(plan, tmp_path)
    assert context == {"credentials": {}}
    assert skipped == ["c"]


def test_build_context_from_repo_errors_on_multi_store(tmp_path):
    """Multi-store secret-stores.yml violates Assumption 1."""
    _make(tmp_path, "configuration/secret-stores.yml",
          yaml.safe_dump({"a": {"type": "vault"}, "b": {"type": "aws"}}))
    plan = {"credentials": []}
    with pytest.raises(PreFlightError, match="multiple"):
        build_context_from_repo(plan, tmp_path)


def test_build_context_from_repo_batches_all_entries_into_one_context(tmp_path):
    _setup_stores(tmp_path)
    _make(tmp_path, "environments/credentials/a.yml",
          yaml.safe_dump({"c1": {"type": "secret", "data": {"secret": "x"}}}))
    _make(tmp_path, "environments/credentials/b.yml",
          yaml.safe_dump({"c2": {"type": "secret", "data": {"secret": "y"}}}))
    plan = {
        "credentials": [
            {"sourceFile": "environments/credentials/a.yml", "to_review": {},
             "to_confirm": {"c1": {"remoteRefPath": "/external", "create": False,
                                    "writeToStore": True}}},
            {"sourceFile": "environments/credentials/b.yml", "to_review": {},
             "to_confirm": {"c2": {"remoteRefPath": "/external", "create": False,
                                    "writeToStore": True}}},
        ]
    }
    context, _ = build_context_from_repo(plan, tmp_path)
    assert set(context["credentials"].keys()) == {"c1", "c2"}
