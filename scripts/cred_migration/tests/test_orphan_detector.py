"""Tests for orphan_detector: declared vs referenced cred-id sets."""

from cred_migration.orphan_detector import (
    collect_declared_from_cred_file,
    collect_referenced_from_consumer,
    compute_orphaned_files,
)


# ---- collect_declared_from_cred_file ----

def test_collect_declared_top_level_keys_are_cred_ids():
    """Cred files use cred-id as top-level key."""
    cred_yaml = {
        "arango-db-creds": {"type": "usernamePassword", "data": {"username": "u", "password": "p"}},
        "webex-token": {"type": "secret", "data": {"secret": "s"}},
    }
    assert collect_declared_from_cred_file(cred_yaml) == {"arango-db-creds", "webex-token"}


def test_collect_declared_empty_file_returns_empty_set():
    assert collect_declared_from_cred_file({}) == set()
    assert collect_declared_from_cred_file(None) == set()


# ---- collect_referenced_from_consumer ----

def test_collect_referenced_finds_value_macro_credids():
    """${creds.get('X').username} references cred-id X."""
    consumer = {
        "deployParameters": {
            "DB_USER": "${creds.get('app-db').username}",
            "DB_PASS": "${creds.get('app-db').password}",
        }
    }
    assert collect_referenced_from_consumer(consumer) == {"app-db"}


def test_collect_referenced_finds_envgen_and_cmdb_prefix_macros():
    """Alias prefixes envgen. and cmdb. also count as references."""
    consumer = {
        "deployParameters": {
            "A": "${envgen.creds.get('token-a').secret}",
            "B": "${cmdb.creds.get('token-b').secret}",
        }
    }
    assert collect_referenced_from_consumer(consumer) == {"token-a", "token-b"}


def test_collect_referenced_finds_hash_macro_value_as_credid():
    """Hash-macro value is the cred-id."""
    consumer = {
        "deployParameters": {
            "#creds{LOGIN, PASSWORD}": "app-db",
        }
    }
    assert collect_referenced_from_consumer(consumer) == {"app-db"}


def test_collect_referenced_finds_builtin_cred_fields():
    """credentialsId, defaultCredentialsId, tokenSecret, credential are cred-id references."""
    consumer = {
        "defaultCredentialsId": "cloud-default",
        "maasConfig": {"credentialsId": "maas-cred"},
        "vaultConfig": {"credentialsId": "vault-cred"},
        "consulConfig": {"tokenSecret": "consul-token"},
    }
    result = collect_referenced_from_consumer(consumer)
    assert result == {"cloud-default", "maas-cred", "vault-cred", "consul-token"}


def test_collect_referenced_finds_credref_credid():
    """$type: credRef entries carry an explicit credId field."""
    consumer = {
        "deployParameters": {
            "X": {"$type": "credRef", "credId": "cred-x", "property": "username"},
        }
    }
    assert collect_referenced_from_consumer(consumer) == {"cred-x"}


def test_collect_referenced_scans_nested_lists():
    """Lists of applications, dbaasConfigs, etc. must be traversed."""
    consumer = {
        "dbaasConfigs": [
            {"credentialsId": "db-1"},
            {"credentialsId": "db-2"},
        ],
        "applications": [
            {"parameters": {"U": "${creds.get('app-1').username}"}}
        ],
    }
    assert collect_referenced_from_consumer(consumer) == {"db-1", "db-2", "app-1"}


# ---- compute_orphaned_files ----

def test_compute_orphaned_files_returns_files_with_all_creds_unreferenced():
    """Orphaned = every declared cred-id in that file is missing from the referenced set."""
    declared_by_file = {
        "environments/credentials/used.yml": {"used-cred"},
        "environments/credentials/orphaned.yml": {"orphan-a", "orphan-b"},
    }
    referenced = {"used-cred", "other-thing"}
    assert compute_orphaned_files(declared_by_file, referenced) == {
        "environments/credentials/orphaned.yml"
    }


def test_compute_orphaned_files_file_with_any_used_cred_is_not_orphaned():
    """If ANY declared cred is referenced, the file stays."""
    declared_by_file = {
        "environments/credentials/mixed.yml": {"used-cred", "unused-cred"},
    }
    referenced = {"used-cred"}
    assert compute_orphaned_files(declared_by_file, referenced) == set()


def test_compute_orphaned_files_empty_declared_file_is_orphaned():
    """A file that declares nothing is trivially orphaned."""
    declared_by_file = {"environments/credentials/empty.yml": set()}
    referenced = {"anything"}
    assert compute_orphaned_files(declared_by_file, referenced) == {
        "environments/credentials/empty.yml"
    }
