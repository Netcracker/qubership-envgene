from pathlib import Path

import pytest
import yaml

from creds_rotation.utils.cred_utils import decrypt_payload, update_file
from envgene_shared.crypto.cred_store import current_cred_store, open_cred_store
from envgene_shared.crypto.crypt import decrypt_file, encrypt_file
from envgene_shared.crypto.sops_handler import encrypt_SOPS_bytes, is_encrypted_SOPS, is_encrypted_SOPS_text
from envgene_shared.tests.crypto.test_crypt import crypt_test_data
from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.file_utils import writeToFile

SOPS_DATA = crypt_test_data[0]

CONTENT = """\
first_cred:
    type: secret
    data:
        secret: token-placeholder-123
"""

UPDATED = {"first_cred": {"type": "secret", "data": {"secret": "token-changed-456"}}}


@pytest.fixture
def cred_file(monkeypatch, tmp_path):
    get_envgene_config_yaml.cache_clear()
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(Path(__file__).resolve().parents[3] / "schemas"))
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.setenv("ENVGENE_AGE_PRIVATE_KEY", SOPS_DATA["secret_key"])
    monkeypatch.setenv("PUBLIC_AGE_KEYS", SOPS_DATA["public_key"])
    writeToFile(str(tmp_path / "configuration" / "config.yml"), f"crypt_backend: {SOPS_DATA['crypt_backend']}\n")
    path = tmp_path / "environments" / "cluster" / "credentials" / "creds.yml"
    writeToFile(str(path), CONTENT)
    encrypt_file(path, load_result=False)
    yield path
    get_envgene_config_yaml.cache_clear()


def test_update_file_puts_into_store(cred_file):
    before = cred_file.read_bytes()
    with open_cred_store():
        update_file({str(cred_file): UPDATED})
        assert cred_file.read_bytes() == before
        assert current_cred_store().get(cred_file) == UPDATED
    assert cred_file.read_bytes() != before
    assert is_encrypted_SOPS(cred_file)
    assert decrypt_file(cred_file, in_place=False)["first_cred"]["data"]["secret"] == "token-changed-456"


def test_decrypt_payload_from_memory(cred_file, tmp_path):
    payload = {"rotation_items": [{"namespace": "ns", "parameter_key": "KEY", "context": "deployParameters",
                                   "parameter_value": "secret-value"}]}
    encrypted = encrypt_SOPS_bytes(yaml.dump(payload, sort_keys=False).encode("utf-8"), "payload.yml")
    assert is_encrypted_SOPS_text(encrypted.decode("utf-8"))
    assert decrypt_payload(encrypted) == payload
