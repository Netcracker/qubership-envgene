import copy
import threading
from pathlib import Path

import pytest

from envgene_shared.crypto.cred_store import CredStore, current_cred_store, open_cred_store
from envgene_shared.crypto.crypt import decrypt_bytes, decrypt_file, encrypt_bytes, encrypt_file, is_encrypted
from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.crypt_utils import effective_set_encrypted_keys
from envgene_shared.crypto.sops_handler import _sops_edit, is_encrypted_SOPS, is_encrypted_SOPS_text
from envgene_shared.tests.crypto.test_crypt import crypt_test_data
from envgene_shared.utils.file_utils import writeToFile
from envgene_shared.utils.yaml_utils import openYaml, readYaml, yaml

SOPS_DATA = crypt_test_data[0]
PLAIN_DATA = {}

CONTENT = """\
first_cred:
    type: secret
    data:
        secret: token-placeholder-123
second_cred:
    type: usernamePassword
    data:
        username: user-placeholder-123
        password: pass-placeholder-123
"""

ES_REF = "ref+vault://secret/path"


@pytest.fixture(autouse=True)
def schema_dir(monkeypatch):
    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schema_dir))
    get_envgene_config_yaml.cache_clear()
    yield
    get_envgene_config_yaml.cache_clear()


def configure(monkeypatch, tmp_path, data):
    get_envgene_config_yaml.cache_clear()
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.setenv("ENVGENE_AGE_PRIVATE_KEY", SOPS_DATA["secret_key"])
    monkeypatch.setenv("PUBLIC_AGE_KEYS", SOPS_DATA["public_key"])
    config = "crypt: false\n" if data is PLAIN_DATA else f"crypt_backend: {data['crypt_backend']}\n"
    writeToFile(str(tmp_path / "configuration" / "config.yml"), config)


def make_cred_file(path, content=CONTENT):
    writeToFile(str(path), content)
    encrypt_file(path, load_result=False)
    return path


@pytest.fixture
def env_dir(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, SOPS_DATA)
    return tmp_path / "environments" / "cluster" / "env"


def test_unchanged_file_is_byte_equal(env_dir):
    first = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    second = make_cred_file(env_dir / "Credentials" / "other-credentials.yml")
    before = (first.read_bytes(), second.read_bytes())
    with open_cred_store() as store:
        obj = store.get(first)
        store.get(second)
        store.put(first, copy.deepcopy(obj))
    assert (first.read_bytes(), second.read_bytes()) == before


def test_changed_file_is_encrypted_and_minimal(env_dir):
    path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    before = path.read_bytes()
    old = openYaml(str(path))
    with open_cred_store() as store:
        store.get(path)["second_cred"]["data"]["password"] = "changed-pass"
    new = openYaml(str(path))
    assert path.read_bytes() != before
    assert is_encrypted_SOPS(path)
    assert new["first_cred"]["data"]["secret"] == old["first_cred"]["data"]["secret"]
    assert new["second_cred"]["data"]["username"] == old["second_cred"]["data"]["username"]
    assert new["second_cred"]["data"]["password"] != old["second_cred"]["data"]["password"]
    assert decrypt_file(path, in_place=False)["second_cred"]["data"]["password"] == "changed-pass"


def test_new_file_is_encrypted(env_dir):
    path = env_dir / "Credentials" / "new-credentials.yml"
    with open_cred_store() as store:
        store.put(path, {"cred": {"type": "secret", "data": {"secret": "value"}}})
    assert is_encrypted_SOPS(path)
    assert decrypt_file(path, in_place=False)["cred"]["data"]["secret"] == "value"


def test_failed_flow_writes_nothing(env_dir):
    first = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    second = make_cred_file(env_dir / "Credentials" / "other-credentials.yml")
    before = (first.read_bytes(), second.read_bytes())
    with pytest.raises(RuntimeError):
        with open_cred_store() as store:
            obj = store.get(first)
            obj["first_cred"]["data"]["secret"] = "changed"
            store.put(first, obj)
            raise RuntimeError("step failed")
    assert (first.read_bytes(), second.read_bytes()) == before
    assert is_encrypted_SOPS(first)
    assert is_encrypted_SOPS(second)
    with pytest.raises(RuntimeError):
        current_cred_store()


def test_open_cred_store_twice_raises(env_dir):
    with open_cred_store():
        with pytest.raises(RuntimeError):
            with open_cred_store():
                pass


def test_path_forms_share_one_entry(env_dir, monkeypatch):
    path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    obj = {"cred": {"type": "secret", "data": {"secret": "value"}}}
    with open_cred_store() as store:
        store.put(str(path), obj)
        monkeypatch.chdir(path.parent)
        assert store.get(Path(path)) is obj
        assert store.get("credentials.yml") is obj
        assert store.get(path.parent / ".." / "Credentials" / "credentials.yml") is obj


def test_deleted_file_keeps_original_bytes(env_dir):
    path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    with open_cred_store() as store:
        path.unlink()
        obj = store.get(path)
        assert obj["first_cred"]["data"]["secret"] == "token-placeholder-123"
    assert not path.exists()


def test_put_equal_object_does_not_recreate_deleted_file(env_dir):
    path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    with open_cred_store() as store:
        path.unlink()
        store.put(path, copy.deepcopy(store.get(path)))
    assert not path.exists()


def test_get_missing_file_with_allow_default_returns_empty_and_writes_nothing(env_dir):
    path = env_dir / "Credentials" / "credentials.yml"
    with open_cred_store() as store:
        assert store.get(path, allow_default=True) == {}
    assert not path.exists()


def test_get_reads_file_unknown_at_open_from_disk(env_dir):
    with open_cred_store() as store:
        path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
        before = path.read_bytes()
        assert store.get(path)["first_cred"]["data"]["secret"] == "token-placeholder-123"
    assert path.read_bytes() == before


def test_exists_sees_put_and_disk_but_not_deleted_file(env_dir):
    on_disk = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    deleted = make_cred_file(env_dir / "Credentials" / "other-credentials.yml")
    only_put = env_dir / "Credentials" / "new-credentials.yml"
    with open_cred_store() as store:
        deleted.unlink()
        store.put(only_put, {"cred": {"type": "secret", "data": {"secret": "value"}}})
        assert store.exists(on_disk)
        assert store.exists(only_put)
        assert not store.exists(deleted)


def test_get_missing_file_without_allow_default_raises(env_dir):
    with open_cred_store() as store:
        with pytest.raises(KeyError):
            store.get(env_dir / "Credentials" / "credentials.yml")


def test_editor_exits_200_on_same_content_other_format(env_dir, tmp_path):
    path = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    before = path.read_bytes()
    reformatted = tmp_path / "reformatted.yml"
    reformatted.write_text(
        "first_cred:\n  type: 'secret'\n  data:\n    secret: 'token-placeholder-123'\n"
        "second_cred:\n  type: usernamePassword\n  data:\n"
        "    username: 'user-placeholder-123'\n    password: 'pass-placeholder-123'\n"
    )
    _sops_edit(path, reformatted, SOPS_DATA["public_key"])
    assert path.read_bytes() == before


def make_es_file(env_dir, content):
    return make_cred_file(env_dir / "effective-set" / "runtime" / "credentials.yaml", content)


def test_es_file_new_literal_key_uses_new_regex(env_dir):
    path = make_es_file(env_dir, f"a: one\nr: {ES_REF}\n")
    with open_cred_store() as store:
        store.put(path, {"a": "one", "b": "two", "r": ES_REF})
    raw = openYaml(str(path))
    assert raw["a"].startswith("ENC[")
    assert raw["b"].startswith("ENC[")
    assert raw["r"] == ES_REF


def test_es_file_same_literal_keys_uses_edit(env_dir):
    path = make_es_file(env_dir, f"a: one\nc: three\nr: {ES_REF}\n")
    old = openYaml(str(path))
    with open_cred_store() as store:
        store.put(path, {"a": "changed", "c": "three", "r": ES_REF})
    raw = openYaml(str(path))
    assert raw["c"] == old["c"]
    assert raw["a"] != old["a"]
    assert raw["a"].startswith("ENC[")
    assert decrypt_file(path, in_place=False)["a"] == "changed"


def test_es_file_without_references_with_non_string_values_uses_edit(env_dir):
    path = make_es_file(env_dir, "a: one\nn: 5\nb: true\n")
    old = openYaml(str(path))
    with open_cred_store() as store:
        store.put(path, {"a": "changed", "n": 5, "b": True})
    raw = openYaml(str(path))
    assert raw["n"] == old["n"]
    assert raw["b"] == old["b"]
    assert raw["a"] != old["a"]
    assert decrypt_file(path, in_place=False)["a"] == "changed"


def test_effective_set_encrypted_keys_follow_sops_rules():
    without_references = {"a": "one", "n": 5, "b": True, "z": None, "e": "", "d": {"inner": 1}, "l": [{"item": "x"}]}
    with_references = {"a": "one", "n": 5, "r": ES_REF}
    assert effective_set_encrypted_keys(without_references) == {"a", "n", "b", "inner", "item"}
    assert effective_set_encrypted_keys(with_references) == {"a"}


def test_es_file_without_literal_keys_written_plain(env_dir):
    path = make_es_file(env_dir, f"a: one\nr: {ES_REF}\n")
    with open_cred_store() as store:
        store.put(path, {"r": ES_REF})
    assert not is_encrypted_SOPS(path)
    assert openYaml(str(path))["r"] == ES_REF


def test_unchanged_es_file_is_byte_equal(env_dir):
    path = make_es_file(env_dir, f"a: one\nr: {ES_REF}\n")
    before = path.read_bytes()
    with open_cred_store() as store:
        store.put(path, copy.deepcopy(store.get(path)))
    assert path.read_bytes() == before


def test_put_of_unread_es_file_recreates_deleted_file(env_dir):
    path = make_es_file(env_dir, f"a: one\nr: {ES_REF}\n")
    with open_cred_store() as store:
        path.unlink()
        store.put(path, {"a": "one", "r": ES_REF})
    assert path.exists()


def test_empty_cred_file_is_ignored(env_dir):
    path = env_dir / "Credentials" / "credentials.yml"
    writeToFile(str(path), "")
    with open_cred_store() as store:
        assert store.get(path) == {}
        store.put(path, {})
    assert path.read_bytes() == b""


def test_crypt_false_unchanged_untouched_changed_rewritten(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, PLAIN_DATA)
    env_dir = tmp_path / "environments" / "cluster" / "env"
    first = make_cred_file(env_dir / "Credentials" / "credentials.yml")
    second = make_cred_file(env_dir / "Credentials" / "other-credentials.yml")
    before = (first.read_bytes(), second.read_bytes())
    with open_cred_store() as store:
        store.get(first)
        store.get(second)["first_cred"]["data"]["secret"] = "changed"
    assert first.read_bytes() == before[0]
    assert second.read_bytes() != before[1]
    assert not is_encrypted(second)
    assert decrypt_file(second, in_place=False)["first_cred"]["data"]["secret"] == "changed"


def test_crypt_false_writes_plain(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, PLAIN_DATA)
    path = tmp_path / "environments" / "cluster" / "env" / "Credentials" / "new-credentials.yml"
    with open_cred_store() as store:
        store.put(path, {"cred": {"type": "secret", "data": {"secret": "value"}}})
    assert not is_encrypted(path)
    assert decrypt_file(path, in_place=False)["cred"]["data"]["secret"] == "value"


def test_put_is_thread_safe(tmp_path):
    store = CredStore([])
    paths = [tmp_path / f"{index}.yml" for index in range(50)]
    threads = [threading.Thread(target=store.put, args=(path, {"index": index})) for index, path in enumerate(paths)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert [store.get(path) for path in paths] == [{"index": index} for index in range(50)]


@pytest.fixture
def plain_env_dir(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, PLAIN_DATA)
    return tmp_path / "environments" / "cluster" / "env"


def test_cred_file_written_sorted_quoted_without_comments(plain_env_dir):
    path = plain_env_dir / "Credentials" / "credentials.yml"
    with open_cred_store() as store:
        store.put(path, yaml.load("# top\ncred:\n  data:\n    secret: value  # eol\n  type: secret\n"))
    text = path.read_text(encoding="utf-8")
    assert list(openYaml(str(path))["cred"]) == ["type", "data"]
    assert 'secret: "value"' in text
    assert "#" not in text


def test_es_file_written_unformatted(plain_env_dir):
    path = plain_env_dir / "effective-set" / "runtime" / "credentials.yaml"
    with open_cred_store() as store:
        store.put(path, {"b": "two", "a": "one"})
    assert path.read_text(encoding="utf-8") == "b: two\na: one\n"


def test_header_written_before_content(plain_env_dir):
    path = plain_env_dir.parent / "cloud-passport" / "cloud-creds.yml"
    with open_cred_store() as store:
        store.put(path, {"cred": {"type": "secret", "data": {"secret": "value"}}}, "first\nsecond")
    assert path.read_text(encoding="utf-8").startswith("# first\n# second\ncred:")


def test_invalid_cred_file_fails_on_write(plain_env_dir):
    path = plain_env_dir / "Credentials" / "credentials.yml"
    with pytest.raises(ValueError):
        with open_cred_store() as store:
            store.put(path, {"cred": "not-an-object"})


def test_bytes_round_trip_without_disk(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, SOPS_DATA)
    path = tmp_path / "environments" / "cluster" / "env" / "Credentials" / "credentials.yml"
    encrypted = encrypt_bytes(CONTENT.encode("utf-8"), path)
    assert is_encrypted_SOPS_text(encrypted.decode("utf-8"))
    assert decrypt_bytes(encrypted, path) == readYaml(CONTENT)
    assert not path.exists()
