"""Tests for source_rewriter: transform cred entries to type:external form."""

import pytest

from cred_migration.source_rewriter import (
    UnsupportedCredTypeError,
    PartialMigrationError,
    derive_properties,
    rewrite_source_entry,
)


# ---- derive_properties ----

def test_derive_properties_username_password_returns_list_of_named_entries():
    result = derive_properties({"username": "u", "password": "p"})
    assert result == [{"name": "username"}, {"name": "password"}]


def test_derive_properties_single_secret_returns_none():
    """secret-type creds have no properties block."""
    assert derive_properties({"secret": "s"}) is None


def test_derive_properties_scalar_data_returns_none():
    """Scalar data (single-value secret) has no properties block."""
    assert derive_properties("plain-token") is None


# ---- rewrite_source_entry ----

def test_rewrite_source_entry_username_password_produces_external_with_properties():
    source = {"type": "usernamePassword", "data": {"username": "u", "password": "p"}}
    plan_entry = {"remoteRefPath": "/prod-cluster/env-a/bss", "create": True}
    result = rewrite_source_entry(source, plan_entry)
    assert result == {
        "type": "external",
        "remoteRefPath": "/prod-cluster/env-a/bss",
        "create": True,
        "properties": [{"name": "username"}, {"name": "password"}],
    }


def test_rewrite_source_entry_secret_omits_properties_block():
    source = {"type": "secret", "data": {"secret": "s"}}
    plan_entry = {"remoteRefPath": "/external", "create": False}
    result = rewrite_source_entry(source, plan_entry)
    assert result == {
        "type": "external",
        "remoteRefPath": "/external",
        "create": False,
    }


def test_rewrite_source_entry_secret_with_scalar_data_omits_properties():
    source = {"type": "secret", "data": "plain-token"}
    plan_entry = {"remoteRefPath": "/external", "create": False}
    result = rewrite_source_entry(source, plan_entry)
    assert "properties" not in result
    assert result["type"] == "external"


def test_rewrite_source_entry_unsupported_type_raises():
    source = {"type": "vaultAppRole", "data": {"roleId": "r", "secretId": "s"}}
    plan_entry = {"remoteRefPath": "/x", "create": False}
    with pytest.raises(UnsupportedCredTypeError, match="vaultAppRole"):
        rewrite_source_entry(source, plan_entry)


def test_rewrite_source_entry_already_external_raises_partial_migration():
    source = {"type": "external", "remoteRefPath": "/x", "create": False}
    plan_entry = {"remoteRefPath": "/x", "create": False}
    with pytest.raises(PartialMigrationError, match="already"):
        rewrite_source_entry(source, plan_entry)


def test_rewrite_source_entry_omits_create_when_false_for_external_tier():
    """Consistent with external-tier default (`create` field omitted, implicit false)."""
    source = {"type": "secret", "data": {"secret": "s"}}
    plan_entry = {"remoteRefPath": "/external", "create": False}
    result = rewrite_source_entry(source, plan_entry, omit_create_when_false=True)
    assert "create" not in result
