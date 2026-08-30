"""Tests for external_context: CLI-context YAML builder for external-cred-provision."""

import pytest

from cred_migration.external_context import (
    build_context_entry,
    build_context,
    build_data_from_source,
)


# ---- build_data_from_source ----

def test_build_data_from_source_username_password_dict():
    """Multi-field cred: source data dict passes through as-is."""
    result = build_data_from_source(
        source_data={"username": "admin", "password": "secret"},
        store_type="vault",
    )
    assert result == {"username": "admin", "password": "secret"}


def test_build_data_from_source_secret_dict_passes_through():
    """secret cred: source `data: {secret: X}` also passes through."""
    result = build_data_from_source(source_data={"secret": "token"}, store_type="vault")
    assert result == {"secret": "token"}


def test_build_data_from_source_scalar_becomes_secret_wrapper_for_vault():
    """Vault rejects scalar data; migration promotes bare scalar to {secret: X}."""
    result = build_data_from_source(source_data="plain-token", store_type="vault")
    assert result == {"secret": "plain-token"}


def test_build_data_from_source_scalar_becomes_secret_wrapper_for_openbao():
    """OpenBao behaves like Vault: dict-only stores promote scalars."""
    result = build_data_from_source(source_data="plain-token", store_type="openbao")
    assert result == {"secret": "plain-token"}


def test_build_data_from_source_scalar_stays_scalar_for_aws():
    """AWS accepts scalar data; no promotion needed."""
    result = build_data_from_source(source_data="plain-token", store_type="aws")
    assert result == "plain-token"


# ---- build_context_entry ----

def test_build_context_entry_composes_vals_strategy_data():
    """Single entry has vals (via helper), strategy=overwrite (migration default), data."""
    entry = build_context_entry(
        cred_id="app-db",
        remote_ref_path="prod-cluster/env-a",
        source_data={"username": "u", "password": "p"},
        store_type="vault",
        store_config={"mountPath": "kv"},
        store_id="default_store",
        default_store_id="default_store",
    )
    assert entry == {
        "vals": "ref+vault://kv/data/prod-cluster/env-a/app-db",
        "strategy": "overwrite",
        "data": {"username": "u", "password": "p"},
    }


def test_build_context_entry_scalar_secret_wrapped_for_vault():
    """Vault: scalar source data → {secret: X}."""
    entry = build_context_entry(
        cred_id="token",
        remote_ref_path="prod-cluster",
        source_data="raw-token",
        store_type="vault",
        store_config={"mountPath": "kv"},
        store_id="default_store",
        default_store_id="default_store",
    )
    assert entry["data"] == {"secret": "raw-token"}


# ---- build_context ----

def test_build_context_batches_multiple_creds_in_one_context():
    """CLI accepts one context YAML with all creds; migration batches per apply run."""
    creds = [
        {
            "cred_id": "app-db",
            "remote_ref_path": "prod-cluster/env-a",
            "source_data": {"username": "u", "password": "p"},
            "store_type": "vault",
            "store_config": {"mountPath": "kv"},
            "store_id": "default_store",
        },
        {
            "cred_id": "webex-token",
            "remote_ref_path": "external",
            "source_data": "secret-value",
            "store_type": "vault",
            "store_config": {"mountPath": "kv"},
            "store_id": "default_store",
        },
    ]
    context = build_context(creds, default_store_id="default_store")
    assert context == {
        "credentials": {
            "app-db": {
                "vals": "ref+vault://kv/data/prod-cluster/env-a/app-db",
                "strategy": "overwrite",
                "data": {"username": "u", "password": "p"},
            },
            "webex-token": {
                "vals": "ref+vault://kv/data/external/webex-token",
                "strategy": "overwrite",
                "data": {"secret": "secret-value"},
            },
        }
    }


def test_build_context_rejects_envgene_null_value_placeholder():
    """envgeneNullValue is a placeholder for a value the operator must set; migration cannot
    write it to a Store. Caller should skip such creds; helper still guards against them."""
    with pytest.raises(ValueError, match="envgeneNullValue"):
        build_context_entry(
            cred_id="c",
            remote_ref_path="prod-cluster",
            source_data={"username": "u", "password": "envgeneNullValue"},
            store_type="vault",
            store_config={"mountPath": "kv"},
            store_id="default_store",
            default_store_id="default_store",
        )
