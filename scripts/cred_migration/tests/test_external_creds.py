"""Tests for external_creds helpers (VALS URI + normalization)."""

import pytest

from cred_migration.external_creds import (
    SecretReferenceError,
    build_vals_uri,
    normalize_secret_name,
)


def test_build_vals_uri_vault_default_store_produces_kv_data_prefix():
    """Java contract mirror: vault + default_store → ref+vault://<mountPath>/data/<name>."""
    result = build_vals_uri(
        store_type="vault",
        store_config={"mountPath": "kv"},
        normalized_name="prod-cluster/env-a/arango-db-creds",
        store_id="default_store",
        default_store_id="default_store",
    )
    assert result == "ref+vault://kv/data/prod-cluster/env-a/arango-db-creds"


def test_build_vals_uri_vault_non_default_store_appends_query_param():
    """Non-default store_id → append ?secret_store_id=<id> (`?` separator for non-AWS)."""
    result = build_vals_uri(
        store_type="vault",
        store_config={"mountPath": "kv"},
        normalized_name="prod-cluster/env-a/arango-db-creds",
        store_id="secondary_store",
        default_store_id="default_store",
    )
    assert result == "ref+vault://kv/data/prod-cluster/env-a/arango-db-creds?secret_store_id=secondary_store"


def test_build_vals_uri_azure_default_store():
    """Java contract mirror: azure + default_store → ref+azurekeyvault://<vaultName>/<name>."""
    result = build_vals_uri(
        store_type="azure",
        store_config={"vaultName": "prod-kv"},
        normalized_name="prod-cluster--env-a--arango",
        store_id="default_store",
        default_store_id="default_store",
    )
    assert result == "ref+azurekeyvault://prod-kv/prod-cluster--env-a--arango"


def test_build_vals_uri_aws_default_store_appends_region_query():
    """Java contract mirror: aws + default_store → ref+awssecrets://<name>?region=<region>."""
    result = build_vals_uri(
        store_type="aws",
        store_config={"region": "us-east-1"},
        normalized_name="prod-cluster/env-a/arango",
        store_id="default_store",
        default_store_id="default_store",
    )
    assert result == "ref+awssecrets://prod-cluster/env-a/arango?region=us-east-1"


def test_build_vals_uri_aws_non_default_store_uses_ampersand_separator():
    """AWS URI already has ?region= so secret_store_id must be joined with `&`."""
    result = build_vals_uri(
        store_type="aws",
        store_config={"region": "us-east-1"},
        normalized_name="prod-cluster/env-a/arango",
        store_id="secondary_store",
        default_store_id="default_store",
    )
    assert result == "ref+awssecrets://prod-cluster/env-a/arango?region=us-east-1&secret_store_id=secondary_store"


def test_build_vals_uri_gcp_default_store():
    """Java contract mirror: gcp + default_store → ref+gcpsecrets://<projectId>/<name>."""
    result = build_vals_uri(
        store_type="gcp",
        store_config={"projectId": "my-gcp-project"},
        normalized_name="prod-cluster--env-a--arango",
        store_id="default_store",
        default_store_id="default_store",
    )
    assert result == "ref+gcpsecrets://my-gcp-project/prod-cluster--env-a--arango"


def test_normalize_secret_name_vault_simple_concat():
    """Java parity: vault → remoteRefPath + '/' + credId. No cred-id length cap for vault."""
    result = normalize_secret_name(
        remote_ref_path="prod-cluster/env-a",
        cred_id="arango-db-creds",
        store_type="vault",
    )
    assert result == "prod-cluster/env-a/arango-db-creds"


def test_normalize_secret_name_vault_rejects_illegal_character():
    """VAULT_PATTERN = ^[a-zA-Z0-9/_-]+$. Space (or @, ., !) is illegal."""
    with pytest.raises(SecretReferenceError, match="vault"):
        normalize_secret_name(
            remote_ref_path="prod cluster/env-a",  # space is illegal
            cred_id="arango",
            store_type="vault",
        )


def test_normalize_secret_name_azure_basic_no_truncation():
    """Azure: segments joined with '--', append '--<credId>'. No truncation when short."""
    result = normalize_secret_name(
        remote_ref_path="prod/env-a",
        cred_id="app-db",
        store_type="azure",
    )
    assert result == "prod--env-a--app-db"


def test_normalize_secret_name_azure_truncates_long_segment():
    """Azure segment > 20 chars: truncate to (max-6=14) chars + '-' + sha256[:5].

    Segment 'verylongenvironmentnamehere' (27 chars) → 'verylongenviro' + '-' + '6f8e4'.
    """
    result = normalize_secret_name(
        remote_ref_path="prod/verylongenvironmentnamehere",
        cred_id="app",
        store_type="azure",
    )
    assert result == "prod--verylongenviro-6f8e4--app"


def test_normalize_secret_name_azure_drops_segments_past_fourth():
    """Azure caps at 4 path segments; extras are silently dropped before append."""
    result = normalize_secret_name(
        remote_ref_path="a/b/c/d/e/f",
        cred_id="app",
        store_type="azure",
    )
    assert result == "a--b--c--d--app"


def test_normalize_secret_name_azure_rejects_long_cred_id():
    """Non-vault stores enforce MAX_CRED_ID_LENGTH=32 on the cred-id."""
    with pytest.raises(SecretReferenceError, match="Credential ID"):
        normalize_secret_name(
            remote_ref_path="p/e",
            cred_id="x" * 33,
            store_type="azure",
        )


def test_normalize_secret_name_azure_rejects_illegal_character():
    """AZURE_PATTERN = ^[a-zA-Z0-9-]+$. '_' or '/' after normalization is illegal."""
    with pytest.raises(SecretReferenceError, match="azure"):
        normalize_secret_name(
            remote_ref_path="prod/env-a",
            cred_id="app_db",  # underscore not in Azure pattern
            store_type="azure",
        )


def test_normalize_secret_name_aws_rejects_total_length_over_512():
    """AWS_MAX_LENGTH=512. Achievable when segments un-capped: 8 segments of 119 chars each

    exceeds the cap (~988 chars pre-cred_id) so total > 512 even after cred_id append."""
    long_path = "/".join("x" * 119 for _ in range(8))
    with pytest.raises(SecretReferenceError, match="Final Normalized Secret Name"):
        normalize_secret_name(
            remote_ref_path=long_path,
            cred_id="app",
            store_type="aws",
        )


def test_normalize_secret_name_aws_basic_uses_slash_delimiter():
    """AWS: segments joined with '/', append '/<credId>'."""
    result = normalize_secret_name(
        remote_ref_path="prod/env-a",
        cred_id="app-db",
        store_type="aws",
    )
    assert result == "prod/env-a/app-db"


def test_normalize_secret_name_aws_keeps_all_segments():
    """AWS has no per-store segment limit (Integer.MAX_VALUE in Java)."""
    result = normalize_secret_name(
        remote_ref_path="a/b/c/d/e/f",
        cred_id="app",
        store_type="aws",
    )
    assert result == "a/b/c/d/e/f/app"


def test_normalize_secret_name_aws_truncates_long_segment():
    """AWS segment > 119 chars: truncate to 113 chars + '-' + sha256[:5]."""
    long_seg = "z" * 130
    result = normalize_secret_name(
        remote_ref_path=long_seg,
        cred_id="app",
        store_type="aws",
    )
    prefix = "z" * 113
    import hashlib as _h
    hash5 = _h.sha256(long_seg.encode()).hexdigest()[:5]
    assert result == f"{prefix}-{hash5}/app"


def test_normalize_secret_name_gcp_basic_uses_double_dash_delimiter():
    """GCP: segments joined with '--', append '--<credId>'."""
    result = normalize_secret_name(
        remote_ref_path="prod/env-a",
        cred_id="app_db",
        store_type="gcp",
    )
    assert result == "prod--env-a--app_db"


def test_normalize_secret_name_gcp_rejects_illegal_character():
    """GCP_PATTERN = ^[a-zA-Z0-9_-]+$. '/' after normalization is illegal - dashed dash '/' handled by join."""
    with pytest.raises(SecretReferenceError, match="gcp"):
        normalize_secret_name(
            remote_ref_path="prod/env-a",
            cred_id="app.db",  # dot not in GCP pattern
            store_type="gcp",
        )
