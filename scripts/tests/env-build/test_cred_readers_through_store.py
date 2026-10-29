import threading
from pathlib import Path

import pytest

from build_env.create_credentials import mergeSharedCreds
from cloud_passport.cloud_passport import add_cloud_passport_creds
from creds_rotation.utils import cred_utils
from creds_rotation.utils.cred_utils import read_env_cred_files
from envgene_shared.crypto.cred_store import open_cred_store
from envgene_shared.crypto.crypt import encrypt_file
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS
from envgene_shared.tests.crypto.test_crypt import crypt_test_data
from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.file_utils import writeToFile
from envgenehelper import getEnvCredentials, open_current_env_instance_store, readYaml, validate_creds
from envgenehelper.errors import ValidationError
from envgenehelper.deployer import get_deployer_config, get_value_and_attributes_from_cred

SOPS_DATA = crypt_test_data[0]

CONTENT = """\
first_cred:
    type: secret
    data:
        secret: token-placeholder-123
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


def encrypted(path):
    writeToFile(str(path), CONTENT)
    encrypt_file(path, load_result=False)
    return path


def assert_untouched(path, before):
    assert path.read_bytes() == before
    assert is_encrypted_SOPS(path)


def test_get_env_credentials(project):
    env_dir = project / "environments" / "cluster" / "env"
    path = encrypted(env_dir / "Credentials" / "credentials.yml")
    before = path.read_bytes()
    with open_cred_store():
        assert getEnvCredentials(env_dir)["first_cred"]["data"]["secret"] == "token-placeholder-123"
    assert_untouched(path, before)


def test_validate_creds(project):
    env_dir = project / "environments" / "cluster" / "env"
    path = encrypted(env_dir / "Credentials" / "credentials.yml")
    before = path.read_bytes()
    with open_cred_store():
        validate_creds(str(path.parent))
    assert_untouched(path, before)


def test_validate_creds_checks_creds_only_in_cred_store(project):
    env_dir = project / "environments" / "cluster" / "env"
    path = env_dir / "Credentials" / "credentials.yml"
    with open_cred_store() as store:
        store.put(path, readYaml("cred:\n  type: secret\n  data:\n    secret: envgeneNullValue\n"))
        with pytest.raises(ValidationError):
            validate_creds(str(path.parent))
        store.put(path, readYaml("cred:\n  type: secret\n  data:\n    secret: value\n"))


def test_validate_creds_reads_disk_without_cred_store(project):
    path = project / "environments" / "cluster" / "env" / "Credentials" / "credentials.yml"
    writeToFile(str(path), "cred:\n  type: secret\n  data:\n    secret: envgeneNullValue\n")
    encrypt_file(path, load_result=False)
    with pytest.raises(ValidationError):
        validate_creds(str(path.parent))


def test_deployer_config_reads_creds_from_disk_without_cred_store(project, monkeypatch):
    monkeypatch.setenv("CLUSTER_NAME", "cluster")
    monkeypatch.setenv("ENVIRONMENT_NAME", "env")
    writeToFile(str(project / "environments" / "cluster" / "env" / "Inventory" / "env_definition.yml"),
                "inventory:\n  environmentName: env\n  deployer: cmdb\n")
    writeToFile(str(project / "configuration" / "deployer.yml"),
                "cmdb:\n  deployerUrl: https://cmdb\n"
                "  username: ${envgen.creds.get('cmdb-cred').username}\n"
                "  token: ${envgen.creds.get('cmdb-cred').password}\n")
    creds = project / "configuration" / "deployer-creds.yml"
    writeToFile(str(creds), "cmdb-cred:\n  type: usernamePassword\n  data:\n    username: user\n    password: token\n")
    encrypt_file(creds, load_result=False)
    assert get_deployer_config() == ("https://cmdb", "user", "token")


def test_deployer_cred(project):
    deployer_dir = project / "environments" / "cluster" / "env" / "deployer"
    path = encrypted(deployer_dir / "deployer-creds.yml")
    before = path.read_bytes()
    with open_cred_store():
        value, _ = get_value_and_attributes_from_cred("envgen.creds.get('first_cred').secret", str(deployer_dir))
    assert value == "token-placeholder-123"
    assert_untouched(path, before)


def test_merge_shared_creds(project):
    env_dir = project / "environments" / "cluster" / "env"
    shared = encrypted(project / "environments" / "cluster" / "Credentials" / "shared.yml")
    before = shared.read_bytes()
    env_creds = env_dir / "Credentials" / "credentials.yml"
    with open_cred_store(), open_current_env_instance_store(env_dir) as objects:
        objects.put(env_creds, readYaml("{}"))
        creds = mergeSharedCreds(
            env_creds, env_dir, project / "environments",
            None, readYaml("envTemplate:\n  sharedMasterCredentialFiles:\n    - shared\n"))
    assert creds["first_cred"]["data"]["secret"] == "token-placeholder-123"
    assert_untouched(shared, before)


def test_merge_shared_creds_only_in_cred_store(project):
    env_dir = project / "environments" / "cluster" / "env"
    shared = env_dir / "Inventory" / "credentials" / "inventory_generation_creds.yml"
    env_creds = env_dir / "Credentials" / "credentials.yml"
    with open_cred_store() as store, open_current_env_instance_store(env_dir) as objects:
        store.put(shared, readYaml(CONTENT))
        objects.put(env_creds, readYaml("{}"))
        creds = mergeSharedCreds(
            env_creds, env_dir, project / "environments",
            None, readYaml("envTemplate:\n  sharedMasterCredentialFiles:\n    - inventory_generation_creds\n"))
    assert creds["first_cred"]["data"]["secret"] == "token-placeholder-123"


def test_cloud_passport_creds(project):
    env_dir = project / "environments" / "cluster" / "env"
    passport = project / "environments" / "cluster" / "cloud-passport" / "passport.yml"
    creds = encrypted(passport.parent / "passport-creds.yml")
    before = creds.read_bytes()
    with open_cred_store(), open_current_env_instance_store(env_dir) as objects:
        add_cloud_passport_creds("passport", str(passport), str(env_dir), "", False)
        merged = objects.get(f"{env_dir}/Credentials/credentials.yml")
    assert merged["first_cred"]["data"]["secret"] == "token-placeholder-123"
    assert_untouched(creds, before)


def test_cloud_passport_creds_only_in_cred_store(project):
    env_dir = project / "environments" / "cluster" / "env"
    passport = project / "environments" / "cluster" / "cloud-passport" / "passport.yml"
    with open_cred_store() as store, open_current_env_instance_store(env_dir) as objects:
        store.put(passport.parent / "passport-creds.yml", readYaml(CONTENT))
        add_cloud_passport_creds("passport", str(passport), str(env_dir), "", False)
        merged = objects.get(f"{env_dir}/Credentials/credentials.yml")
    assert merged["first_cred"]["data"]["secret"] == "token-placeholder-123"


def test_rotation_read_env_cred_files(project):
    paths = [str(encrypted(project / "environments" / f"cred{i}.yml")) for i in range(9)]
    before = {p: Path(p).read_bytes() for p in paths}
    with open_cred_store():
        result = read_env_cred_files(paths)
    assert set(result) == set(paths)
    assert all(v["first_cred"]["data"]["secret"] == "token-placeholder-123" for v in result.values())
    for p in paths:
        assert_untouched(Path(p), before[p])


def test_rotation_reads_cred_files_in_parallel(monkeypatch):
    barrier = threading.Barrier(2, timeout=5)

    def read(path):
        barrier.wait()
        return path

    monkeypatch.setattr(cred_utils, "get_cred_file_content", read)
    assert read_env_cred_files(["a", "b"]) == {"a": "a", "b": "b"}
