from pathlib import Path

import pytest

from envgene_shared.crypto.cred_store import current_cred_store, open_cred_store
from envgene_shared.crypto.crypt import decrypt_file, encrypt_file
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS
from envgene_shared.tests.crypto.test_crypt import crypt_test_data
from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.file_utils import writeToFile
from inventory.env_inventory_generation import Action, INVENTORY, Place, handle_objects, save_creds

SOPS_DATA = crypt_test_data[0]

CONTENT = """\
first_cred:
    type: secret
    data:
        secret: token-placeholder-123
"""

NEW_CREDS = {"first_cred": {"type": "secret", "data": {"secret": "token-changed-456"}}}


@pytest.fixture
def project(monkeypatch, tmp_path):
    get_envgene_config_yaml.cache_clear()
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(Path(__file__).resolve().parents[3] / "schemas"))
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.setenv("ENVGENE_AGE_PRIVATE_KEY", SOPS_DATA["secret_key"])
    monkeypatch.setenv("PUBLIC_AGE_KEYS", SOPS_DATA["public_key"])
    writeToFile(str(tmp_path / "configuration" / "config.yml"), f"crypt_backend: {SOPS_DATA['crypt_backend']}\n")
    yield tmp_path
    get_envgene_config_yaml.cache_clear()


def encrypted(path):
    writeToFile(str(path), CONTENT)
    encrypt_file(path, load_result=False)
    return path


def test_save_creds_puts_into_store(project):
    path = encrypted(project / "environments" / "cluster" / "env" / "Credentials" / "credentials.yml")
    before = path.read_bytes()
    with open_cred_store():
        save_creds(path, NEW_CREDS)
        assert path.read_bytes() == before
        assert current_cred_store().get(path) == NEW_CREDS
    assert path.read_bytes() != before
    assert is_encrypted_SOPS(path)
    assert decrypt_file(path, in_place=False)["first_cred"]["data"]["secret"] == "token-changed-456"


def test_handle_objects_credentials_put_into_store(project):
    env_dir = project / "environments" / "cluster" / "env"
    path = encrypted(env_dir / "Inventory" / "credentials" / "cred1.yml")
    before = path.read_bytes()
    objects = [{"place": Place.ENV.value, "action": Action.CREATE_OR_REPLACE.value, "name": "cred1",
                "content": NEW_CREDS}]
    with open_cred_store():
        handle_objects(env_dir, objects, "credentials", INVENTORY, encrypt=True)
        assert path.read_bytes() == before
        assert current_cred_store().get(path)["first_cred"]["data"]["secret"] == "token-changed-456"
    assert is_encrypted_SOPS(path)
    assert decrypt_file(path, in_place=False)["first_cred"]["data"]["secret"] == "token-changed-456"
