import pytest

from envgenehelper.errors import ValidationError
from envgenehelper.system_creds_helper import (
    DEFAULT_SECRET_STORE,
    resolve_secret_store_id,
    validate_system_credential,
    validate_system_credentials,
    resolve_integration_param,
)


def test_resolve_secret_store_id_defaults_to_default_store():
    assert resolve_secret_store_id({}) == DEFAULT_SECRET_STORE
    assert resolve_secret_store_id({"secretStore": ""}) == DEFAULT_SECRET_STORE
    assert resolve_secret_store_id({"secretStore": "prod_store"}) == "prod_store"


def test_validate_system_credential_rejects_create_true():
    secret_stores = {"default_store": {"type": "vault", "mountPath": "secret"}}
    with pytest.raises(ValidationError, match="create: true"):
        validate_system_credential(
            "self-token-cred",
            {"type": "external", "create": True, "remoteRefPath": "/vcs/bot"},
            secret_stores,
        )


def test_validate_system_credential_rejects_aws_store():
    secret_stores = {
        "prod_store": {"type": "aws", "region": "eu-west-1"},
    }
    with pytest.raises(ValidationError, match="only vault and gcp"):
        validate_system_credential(
            "registry-cred",
            {"type": "external", "secretStore": "prod_store", "remoteRefPath": "/registry"},
            secret_stores,
        )


def test_validate_system_credential_defaults_secret_store():
    secret_stores = {"default_store": {"type": "gcp", "projectId": "123"}}
    validate_system_credential(
        "self-token-cred",
        {"type": "external", "remoteRefPath": "/vcs/bot"},
        secret_stores,
    )


def test_validate_system_credentials_skips_local_entries():
    secret_stores = {"default_store": {"type": "vault", "mountPath": "secret"}}
    validate_system_credentials(
        {
            "local-cred": {
                "type": "secret",
                "data": {"secret": "value"},
            }
        },
        secret_stores,
    )


def test_resolve_integration_param_prefers_config_over_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "from-env")
    cred_config = {}
    integration = {"self_token": "from-config"}
    assert (
        resolve_integration_param(integration, "self_token", ["GITHUB_TOKEN"], cred_config)
        == "from-config"
    )


def test_resolve_integration_param_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "from-env")
    cred_config = {}
    assert (
        resolve_integration_param({}, "self_token", ["GITHUB_TOKEN", "GITLAB_TOKEN"], cred_config)
        == "from-env"
    )


def test_fetch_cred_value_supports_cred_ref(monkeypatch):
    from envgenehelper.creds_helper import fetch_cred_value

    cred_ref = {"$type": "credRef", "credId": "self-token-cred"}
    cred_config = {
        "self-token-cred": {
            "type": "external",
            "remoteRefPath": "/vcs/bot",
        }
    }

    monkeypatch.setattr(
        "envgenehelper.system_creds_helper.resolve_cred_ref",
        lambda ref, config, base_dir=None, secret_stores=None: "resolved-token",
    )
    assert fetch_cred_value(cred_ref, cred_config) == "resolved-token"
