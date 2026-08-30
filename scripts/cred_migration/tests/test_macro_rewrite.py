"""Tests for macro_rewrite: parse creds macros + emit credRef structures."""

import pytest

from cred_migration.macro_rewrite import CompositeMacroError, rewrite_dict, rewrite_value


def test_rewrite_value_creds_get_username_returns_credref_with_property():
    """${creds.get('X').username} → {$type: credRef, credId: X, property: username}."""
    result = rewrite_value("${creds.get('app-db').username}")
    assert result == {"$type": "credRef", "credId": "app-db", "property": "username"}


def test_rewrite_value_creds_get_password_returns_credref_with_property():
    """${creds.get('X').password} → property: password."""
    result = rewrite_value("${creds.get('app-db').password}")
    assert result == {"$type": "credRef", "credId": "app-db", "property": "password"}


def test_rewrite_value_creds_get_secret_omits_property():
    """${creds.get('X').secret} → single-value cred, property omitted."""
    result = rewrite_value("${creds.get('token-cred').secret}")
    assert result == {"$type": "credRef", "credId": "token-cred"}


def test_rewrite_value_envgen_prefix_treated_as_alias():
    """${envgen.creds.get('X').Y} == ${creds.get('X').Y}."""
    result = rewrite_value("${envgen.creds.get('app-db').username}")
    assert result == {"$type": "credRef", "credId": "app-db", "property": "username"}


def test_rewrite_value_cmdb_prefix_treated_as_alias():
    """${cmdb.creds.get('X').Y} == ${creds.get('X').Y}."""
    result = rewrite_value("${cmdb.creds.get('app-db').secret}")
    assert result == {"$type": "credRef", "credId": "app-db"}


def test_rewrite_value_double_quotes_around_credid():
    """Accept both single and double quotes around credId."""
    result = rewrite_value('${creds.get("app-db").username}')
    assert result == {"$type": "credRef", "credId": "app-db", "property": "username"}


def test_rewrite_value_whitespace_tolerated():
    """Whitespace around identifiers ignored."""
    result = rewrite_value("${ creds.get( 'app-db' ) . password }")
    assert result == {"$type": "credRef", "credId": "app-db", "property": "password"}


def test_rewrite_value_non_macro_returns_input_unchanged():
    """Value that is not a creds macro is returned as-is."""
    assert rewrite_value("plain-string") == "plain-string"
    assert rewrite_value(42) == 42
    assert rewrite_value(None) is None


def test_rewrite_value_composite_raises():
    """Macro embedded in larger string is not rewritable (credRef is structural)."""
    with pytest.raises(CompositeMacroError, match="composite"):
        rewrite_value("user=${creds.get('X').username}@host")


def test_rewrite_value_unknown_property_raises():
    """Property must be one of username/password/secret."""
    with pytest.raises(ValueError, match="property"):
        rewrite_value("${creds.get('X').unknown}")


def test_rewrite_dict_expands_hash_macro_to_two_credref_entries():
    """`#creds{LOGIN, PASSWORD}: cred` expands to LOGIN + PASSWORD credRef entries."""
    result = rewrite_dict({"#creds{LOGIN, PASSWORD}": "test-cred"})
    assert result == {
        "LOGIN": {"$type": "credRef", "credId": "test-cred", "property": "username"},
        "PASSWORD": {"$type": "credRef", "credId": "test-cred", "property": "password"},
    }


def test_rewrite_dict_hash_macro_credscl_and_credsns_expand_same_way():
    """All three hash-macro variants expand identically."""
    assert rewrite_dict({"#credscl{U, P}": "c"}) == {
        "U": {"$type": "credRef", "credId": "c", "property": "username"},
        "P": {"$type": "credRef", "credId": "c", "property": "password"},
    }
    assert rewrite_dict({"#credsns{U, P}": "c"}) == {
        "U": {"$type": "credRef", "credId": "c", "property": "username"},
        "P": {"$type": "credRef", "credId": "c", "property": "password"},
    }


def test_rewrite_dict_processes_value_macros_in_values():
    """Value-side ${creds.get(...)} rewritten to credRef mapping."""
    result = rewrite_dict({"DB_USER": "${creds.get('app-db').username}"})
    assert result == {
        "DB_USER": {"$type": "credRef", "credId": "app-db", "property": "username"}
    }


def test_rewrite_dict_preserves_non_macro_entries_unchanged():
    """Ordinary key/value entries pass through untouched."""
    inp = {"replicas": 3, "region": "us-east-1"}
    assert rewrite_dict(inp) == inp


def test_rewrite_dict_preserves_insertion_order():
    """Rewritten dict keeps the original key order (with expanded hash-macro entries in place)."""
    inp = {
        "A": "plain",
        "#creds{X, Y}": "c",
        "B": "${creds.get('t').secret}",
    }
    result = list(rewrite_dict(inp).keys())
    assert result == ["A", "X", "Y", "B"]
