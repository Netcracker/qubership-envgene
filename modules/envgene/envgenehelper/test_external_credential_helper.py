import subprocess
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from .external_credential_helper import _parse_secret_payload, _get_property_value, find_external_credential_by_id, extract_external_cred, find_secret_store_by_id, resolve_external_credential_reference, load_all_secret_stores, resolve_external_credential_data, _get_secret_store_payload_cached
from envgenehelper.errors import ValidationError


@pytest.fixture
def mock_configs():
    credentials_config = {
        "my-cred-id": {
            "type": "external",
            "remoteRefPath": "secret/data/my-path",            
            "create": False,
            "properties": [{"name": "username"}, {"name": "password"}]
        }
    }
    secret_stores_config = {
        "default_store": {"type": "vault", "url": "https://example.com"},
       }
    return credentials_config, secret_stores_config



@pytest.mark.parametrize(
    "cred_map, expected_output, expected_error, error_match",
    [
        ({"$type": "credRef", "credId": "test-id"}, "test-id", None, None),
        ({"$type": "credRef", "credId": "   "}, None, ValueError, "Invalid credRef"),
        ({"$type": "otherType"}, None, None, None),
    ]
)
def test_extract_external_cred(cred_map, expected_output, expected_error, error_match):
    if expected_error:
        with pytest.raises(expected_error, match=error_match):
            extract_external_cred(cred_map)
    else:
        assert extract_external_cred(cred_map) == expected_output


@pytest.mark.parametrize(
    "raw_payload, expected_output, expected_error, error_match",
    [
        ("username: admin\npassword: 123", {"username": "admin", "password": 123}, None, None),
        ("plain_text_secret_string", "plain_text_secret_string", None, None),
        ("{invalid_json: [missing", None, ValueError, "not valid YAML or JSON"),
        ("- item1\n- item2", None, ValueError, "Unsupported secret payload type"),
    ]
)
def test_parse_secret_payload(raw_payload, expected_output, expected_error, error_match):
    if expected_error:
        with pytest.raises(expected_error, match=error_match):
            _parse_secret_payload(raw_payload)
    else:
        assert _parse_secret_payload(raw_payload) == expected_output


@pytest.mark.parametrize(
    "property_name, store_type, payload, expected_output, expected_error, error_match",
    [
        ("username", "vault", {"username": "db_user"}, "db_user", None, None),
        (None, "vault", {"value": "vault_token"}, "vault_token", None, None),
        ("any_prop", "vault", "raw_string", "raw_string", None, None),
        ("password", "vault", {"username": "db_user"}, None, ValueError, "Secret store did not return expected property"),
    ]
)
def test_get_property_value(property_name, store_type, payload, expected_output, expected_error, error_match):
    if expected_error:
        with pytest.raises(expected_error, match=error_match):
            _get_property_value("my-cred", property_name, store_type, payload)
    else:
        assert _get_property_value("my-cred", property_name, store_type, payload) == expected_output


@pytest.mark.unit
def test_find_external_credential_by_id_not_found(mock_configs):
    cred_conf, _ = mock_configs
    with pytest.raises(ValidationError, match="not found in credentials file"):
        find_external_credential_by_id("non-existent", cred_conf)


@pytest.mark.unit
def test_load_all_secret_stores_missing_file():
    with patch("os.environ", {"CI_PROJECT_DIR": "/tmp"}), \
        patch.object(Path, "is_file", return_value=False):
        assert load_all_secret_stores() == {}


@pytest.mark.unit
def test_resolve_external_credential_reference_success(mock_configs, monkeypatch):
    _get_secret_store_payload_cached.cache_clear()

    cred_conf, store_conf = mock_configs
    credential_reference = {"$type": "credRef", "credId": "my-cred-id", "property": "password"}
    
    mock_sub_process = MagicMock()
    mock_sub_process.stdout = json.dumps({"my-cred-id": "vals://vault/secret/path"})
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_sub_process)
    monkeypatch.setattr(
        "envgenehelper.external_credential_helper.load_all_secret_stores", 
        lambda *args, **kwargs: store_conf
    )
    
    mock_sm_instance = MagicMock()
    mock_sm_instance.read_secret.return_value = yaml.dump({"username": "admin", "password": "super-secret-password"})
    monkeypatch.setattr(
        "envgenehelper.external_credential_helper.SecretManager", 
        lambda *args, **kwargs: mock_sm_instance
    )

    result = resolve_external_credential_reference(credential_reference, cred_conf)
    assert result == "super-secret-password"


@pytest.mark.unit
def test_resolve_external_credential_data_all_properties(mock_configs, monkeypatch):
    _get_secret_store_payload_cached.cache_clear()
    cred_conf, store_conf = mock_configs
    
    mock_sub_process = MagicMock()
    mock_sub_process.stdout = json.dumps({"my-cred-id": "vals://vault/secret/path"})
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_sub_process)
    monkeypatch.setattr(
        "envgenehelper.external_credential_helper.load_all_secret_stores", 
        lambda *args, **kwargs: store_conf
    )
    
    mock_sm_instance = MagicMock()
    mock_sm_instance.read_secret.return_value = yaml.dump({"username": "app_user", "password": "password123"})
    monkeypatch.setattr(
        "envgenehelper.external_credential_helper.SecretManager", 
        lambda *args, **kwargs: mock_sm_instance
    )
         
    result = resolve_external_credential_data("my-cred-id", cred_conf)
    assert result == {"username": "app_user", "password": "password123"}