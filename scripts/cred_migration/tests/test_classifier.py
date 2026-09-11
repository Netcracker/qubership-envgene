"""Tests for classifier: tier assignment + shadow-platform heuristics."""

import pytest

from cred_migration.classifier import (
    Tier,
    classify_tier_by_source_file,
    matches_platform_pattern,
    has_keyword_substring,
    is_known_cloud_passport_cred,
    parse_comment_marker,
    build_signals,
)


# ---- Tier assignment by source file path ----

def test_classify_tier_cloud_passport_creds_file_is_passport_tier():
    tier = classify_tier_by_source_file(
        "environments/prod-cluster/cloud-passport/prod-cluster-creds.yml"
    )
    assert tier is Tier.PASSPORT


def test_classify_tier_credential_template_is_env_tier():
    tier = classify_tier_by_source_file(
        "templates/env_templates/bss/external-credentials.yml.j2"
    )
    assert tier is Tier.ENV


def test_classify_tier_env_scoped_shared_cred_is_env_tier():
    tier = classify_tier_by_source_file(
        "environments/prod-cluster/env-a/Inventory/credentials/arango.yml"
    )
    assert tier is Tier.ENV


def test_classify_tier_repo_scoped_shared_cred_is_external_tier():
    tier = classify_tier_by_source_file("environments/credentials/global.yml")
    assert tier is Tier.EXTERNAL


def test_classify_tier_cluster_scoped_shared_cred_is_external_tier():
    tier = classify_tier_by_source_file(
        "environments/prod-cluster/credentials/shared.yml"
    )
    assert tier is Tier.EXTERNAL


def test_classify_tier_system_credentials_is_external_tier():
    tier = classify_tier_by_source_file("configuration/credentials/credentials.yml")
    assert tier is Tier.EXTERNAL


def test_classify_tier_unknown_path_raises():
    with pytest.raises(ValueError, match="unknown"):
        classify_tier_by_source_file("some/random/path.yml")


# ---- Shadow-platform heuristic: patterns ----

def test_matches_platform_pattern_recognizes_dbaas_prefix():
    assert matches_platform_pattern("dbaas-cluster-dba")
    assert matches_platform_pattern("dbaas_admin")


def test_matches_platform_pattern_recognizes_all_listed_prefixes():
    for cred_id in ["argocd-cred", "arango-x", "cluster-x", "consul-x",
                    "keycloak-x", "maas-x", "vault-x", "k8s-x", "kube-x"]:
        assert matches_platform_pattern(cred_id), cred_id


def test_matches_platform_pattern_bare_prefix_word_matches():
    assert matches_platform_pattern("dbaas")


def test_matches_platform_pattern_case_insensitive():
    assert matches_platform_pattern("DBAAS-CLUSTER-DBA")


def test_matches_platform_pattern_does_not_fire_on_random_cred_id():
    assert not matches_platform_pattern("app-db-cred")
    assert not matches_platform_pattern("bss-endpoint-cred")


# ---- Shadow-platform heuristic: keyword substring ----

def test_has_keyword_substring_finds_cluster():
    assert has_keyword_substring("my-cluster-token")


def test_has_keyword_substring_finds_admin():
    assert has_keyword_substring("APP-ADMIN-CRED")


def test_has_keyword_substring_none_on_ordinary_cred_id():
    assert not has_keyword_substring("app-db-cred")


# ---- Shadow-platform heuristic: comment marker ----

def test_parse_comment_marker_extracts_cloud_passport_hint():
    result = parse_comment_marker("# cloud passport: dbaas-admin")
    assert result is not None and "cloud passport" in result.lower()


def test_parse_comment_marker_ignores_unrelated_comment():
    assert parse_comment_marker("# regular note") is None


def test_parse_comment_marker_none_when_absent():
    assert parse_comment_marker(None) is None
    assert parse_comment_marker("") is None


# ---- build_signals combining ----

def test_build_signals_returns_empty_when_no_hits():
    signals = build_signals(cred_id="ordinary-cred", comment=None)
    assert signals == []


def test_build_signals_captures_platform_pattern_hit():
    signals = build_signals(cred_id="dbaas-admin", comment=None)
    assert any("pattern" in s.lower() for s in signals)


def test_build_signals_captures_keyword_and_pattern_together():
    signals = build_signals(cred_id="cluster-admin", comment=None)
    # both pattern (cluster-*) and keyword (cluster / admin) hit
    assert len(signals) >= 2


def test_is_known_cloud_passport_cred_recognizes_widely_observed_ids():
    """Registry sourced from 25 real Cloud Passport creds files."""
    for cid in ("cloud-deploy-sa-token", "dbaas", "consul", "maasexternal", "coreexternal"):
        assert is_known_cloud_passport_cred(cid), cid


def test_is_known_cloud_passport_cred_recognizes_long_tail_ids():
    """Registry includes cred-ids seen in only 1 repo (still real observed setups)."""
    for cid in ("cmdb-user", "cip-hadoop-principal", "storage-proxy"):
        assert is_known_cloud_passport_cred(cid), cid


def test_is_known_cloud_passport_cred_returns_false_for_unknown():
    assert not is_known_cloud_passport_cred("random-app-cred")
    assert not is_known_cloud_passport_cred("bss-endpoint-cred")


def test_build_signals_fires_registry_signal_for_known_cred():
    signals = build_signals(cred_id="cloud-deploy-sa-token", comment=None)
    assert any("cloud passport" in s.lower() or "registry" in s.lower() for s in signals)


def test_build_signals_captures_comment_marker():
    signals = build_signals(cred_id="x", comment="# cloud passport: something")
    assert any("comment" in s.lower() or "cloud passport" in s.lower() for s in signals)
