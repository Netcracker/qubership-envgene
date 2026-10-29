from pathlib import Path

import pytest
import yaml
from cryptography.fernet import Fernet

from cloud_passport.main import header_text, process_credentials
from envgene_shared.crypto.cred_store import current_cred_store, open_cred_store
from envgene_shared.crypto.crypt import decrypt_file, encrypt_file
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS
from envgene_shared.tests.crypto.test_crypt import crypt_test_data
from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.constants import FERNET_STR
from envgene_shared.utils.file_utils import writeToFile
from envgenehelper import cleanup_dir
from envgenehelper.errors import ValidationError

SOPS_DATA = crypt_test_data[0]
DISCOVERY_KEY = "n1588R0sm7Df4WJkFLEXd_d-rnKMoPl_8KFlC8yM5CY="

DISCOVERY_CONTENT = """\
first_cred:
    type: usernamePassword
    data:
        username: user-placeholder-123
        password: pass-placeholder-123
"""


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


@pytest.fixture
def discovery_files(tmp_path_factory):
    return make_discovery_files(tmp_path_factory, DISCOVERY_CONTENT)


def make_discovery_files(tmp_path_factory, content):
    fernet = Fernet(DISCOVERY_KEY)
    data = yaml.safe_load(content)["first_cred"]["data"]
    encrypted = {key: FERNET_STR + fernet.encrypt(value.encode()).decode() for key, value in data.items()}
    path = tmp_path_factory.mktemp("discovery") / "sensitive.yml"
    path.write_text(yaml.safe_dump({"first_cred": {"type": "usernamePassword", **encrypted}}))
    return [path]


def test_process_credentials_puts_into_store(project, discovery_files):
    cloud_passport_dir = project / "environments" / "cluster" / "cloud-passport"
    cloud_passport_dir.mkdir(parents=True)
    creds_path = cloud_passport_dir / "cloud-creds.yml"
    with open_cred_store():
        process_credentials(discovery_files, cloud_passport_dir, "cloud", DISCOVERY_KEY)
        assert not creds_path.exists()
        assert current_cred_store().get(creds_path)["first_cred"]["data"]["username"] == "user-placeholder-123"
    assert creds_path.read_text().startswith("# " + header_text.splitlines()[0])
    assert is_encrypted_SOPS(creds_path)
    assert decrypt_file(creds_path, in_place=False)["first_cred"]["data"]["password"] == "pass-placeholder-123"


@pytest.mark.parametrize("password", ["pass-placeholder-123", "pass-changed-456"])
def test_process_credentials_replaces_existing_creds_file(project, tmp_path_factory, password):
    cloud_passport_dir = project / "environments" / "cluster" / "cloud-passport"
    creds_path = cloud_passport_dir / "cloud-creds.yml"
    writeToFile(str(creds_path), "# " + header_text.replace("\n", "\n# ") + "\n" + DISCOVERY_CONTENT)
    encrypt_file(creds_path, load_result=False)
    discovery_files = make_discovery_files(tmp_path_factory, DISCOVERY_CONTENT.replace("pass-placeholder-123", password))
    with open_cred_store():
        cleanup_dir(cloud_passport_dir, keep=["cloud-creds.yml"])
        process_credentials(discovery_files, cloud_passport_dir, "cloud", DISCOVERY_KEY)
    assert creds_path.read_text().startswith("# " + header_text.splitlines()[0])
    assert is_encrypted_SOPS(creds_path)
    assert decrypt_file(creds_path, in_place=False)["first_cred"]["data"]["password"] == password


def test_cleanup_dir_keeps_listed_files(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "file.yml").write_text("a: 1\n")
    (tmp_path / "other.yml").write_text("a: 1\n")
    (tmp_path / "cloud-creds.yml").write_text("a: 1\n")
    cleanup_dir(tmp_path, keep=["cloud-creds.yml"])
    assert [p.name for p in tmp_path.iterdir()] == ["cloud-creds.yml"]


def test_process_credentials_without_sensitive_file_fails(project, tmp_path):
    cloud_passport_dir = project / "environments" / "cluster" / "cloud-passport"
    with open_cred_store():
        with pytest.raises(ValidationError):
            process_credentials([tmp_path / "passport.yml"], cloud_passport_dir, "cloud", DISCOVERY_KEY)
