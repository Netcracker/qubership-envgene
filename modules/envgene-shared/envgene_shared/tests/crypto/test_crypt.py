import os
import copy
from pathlib import Path
import subprocess
import pytest
from subprocess import SubprocessError

from ruyaml import CommentedMap

from envgene_shared.utils.collections_utils import compare_dicts
from envgene_shared.crypto.crypt import decrypt_file, encrypt_file, is_encrypted, _parallel_cred_op, detect_crypt_backend_from_file
from envgene_shared.utils.file_utils import check_file_exists, writeToFile
from envgene_shared.utils.yaml_utils import openYaml, writeYamlToFile

TEST_CONTENT = """\
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
TEST_FILE = 'test_data/test_crypt.yaml'
TEST_FILE_OLD = 'test_data/old_test_crypt.yaml'
NOT_EXISTING_TEST_FILE = 'test_data/not_existing_test_crypt.yaml'
EFFECTIVE_SET_FILE = 'test_data/effective-set/runtimee/credentials.yaml'

crypt_test_data = [
    {
        'crypt_backend': 'SOPS',
        'secret_key': 'AGE-SECRET-KEY-1AQVCSQDRR5F70H3WJL82EMHMPSDMJPRP0GREJE0Y3M5YJZ25GT9SN0Y6FM',
        'public_key': 'age1y4hfj9zz05dtqycfk55y4csddch6w2lu9l6wx7r68at5x897ea3qjh0gl9',
    },
    {
        'crypt_backend': 'Fernet',
        'secret_key': 'n1588R0sm7Df4WJkFLEXd_d-rnKMoPl_8KFlC8yM5CY=',
        'public_key': None,
    },
    {
        'crypt_backend': None,
        'secret_key': 'n1588R0sm7Df4WJkFLEXd_d-rnKMoPl_8KFlC8yM5CY=',
        'public_key': None,
    },
]
crypt_functions_data = [ decrypt_file, encrypt_file ]

@pytest.fixture(autouse=True)
def schema_dir(monkeypatch):
    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schema_dir))

def reset_test_files():
    writeToFile(TEST_FILE, TEST_CONTENT)
    if os.path.exists(NOT_EXISTING_TEST_FILE):
        os.remove(NOT_EXISTING_TEST_FILE)

@pytest.fixture(params=crypt_test_data)
def crypt_kwargs(request):
    reset_test_files()
    request.addfinalizer(reset_test_files)

    crypt_kwargs = {'file_path': TEST_FILE}
    crypt_kwargs.update(request.param)

    yield crypt_kwargs


@pytest.fixture
def effective_set_setup():
    effective_dir = os.path.dirname(EFFECTIVE_SET_FILE)
    os.makedirs(effective_dir, exist_ok=True)    
    yield    
    if os.path.exists(EFFECTIVE_SET_FILE):
        os.remove(EFFECTIVE_SET_FILE)


def test_basic(crypt_kwargs):
    init_yaml, enc_yaml, dec_yaml = run_encryption_cycle(crypt_kwargs)
    assert dec_yaml == init_yaml and enc_yaml != init_yaml

def run_encryption_cycle(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']
    init_yaml = openYaml(cred_file)
    encrypt_file(**crypt_kwargs)
    enc_yaml = openYaml(cred_file)
    decrypt_file(**crypt_kwargs)
    dec_yaml = openYaml(cred_file)
    return init_yaml, enc_yaml, dec_yaml

def test_repetition(crypt_kwargs):
    # crypt doesn't fail when trying to decrypt unencrypted file
    decrypt_file(**crypt_kwargs)
    # crypt doesn't fail when trying to encrypt encrypted file
    encrypt_file(**crypt_kwargs)
    encrypt_file(**crypt_kwargs)

def test_with_in_place_false(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']
    init_yaml = openYaml(cred_file)

    # test encryption
    enc_yaml_in_air = encrypt_file(**crypt_kwargs, in_place=False)
    assert init_yaml != enc_yaml_in_air
    curr_yaml_in_file = openYaml(cred_file)
    assert init_yaml == curr_yaml_in_file

    # check encrypt in place
    enc_yaml = encrypt_file(**crypt_kwargs)
    assert init_yaml != enc_yaml

    # test decryption
    curr_yaml_in_air = decrypt_file(**crypt_kwargs, in_place=False)
    assert init_yaml == curr_yaml_in_air
    curr_yaml_in_file = openYaml(cred_file)
    assert init_yaml != curr_yaml_in_file

    # check decrypt in place
    dec_yaml = decrypt_file(**crypt_kwargs)
    assert init_yaml == dec_yaml

def test_ignore_crypt(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']
    init_yaml = openYaml(cred_file)

    new_yaml = encrypt_file(**crypt_kwargs, ignore_is_crypt=False, is_crypt=False)
    assert init_yaml == new_yaml
    new_yaml = encrypt_file(**crypt_kwargs, ignore_is_crypt=True, is_crypt=False)
    assert init_yaml != new_yaml

    with pytest.raises(ValueError, match="Parameter crypt is set to false"):
        decrypt_file(**crypt_kwargs, ignore_is_crypt=False, is_crypt=False)
    new_yaml = decrypt_file(**crypt_kwargs, ignore_is_crypt=True, is_crypt=False)
    assert init_yaml == new_yaml

def test_skip_yaml_load_when_crypt_disabled_and_load_result_false(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']
    init_yaml = openYaml(cred_file)

    assert encrypt_file(**crypt_kwargs, is_crypt=False, load_result=False) is None
    assert decrypt_file(**crypt_kwargs, is_crypt=False, load_result=False) is None
    assert openYaml(cred_file) == init_yaml

def test_parallel_encrypt_with_crypt_disabled_and_load_result_false(tmp_path):
    cred_paths = []
    for index in range(6):
        cred_path = tmp_path / f"credentials-{index}.yml"
        writeToFile(str(cred_path), TEST_CONTENT)
        cred_paths.append(str(cred_path))

    _parallel_cred_op(
        cred_paths,
        encrypt_file,
        crypt_backend='SOPS',
        is_crypt=False,
        load_result=False,
    )

@pytest.mark.parametrize("crypt_func", crypt_functions_data)
def test_with_file_missing(crypt_kwargs, crypt_func):
    cred_file = NOT_EXISTING_TEST_FILE
    crypt_kwargs['file_path'] = cred_file
    assert not check_file_exists(cred_file)

    with pytest.raises((FileNotFoundError, SubprocessError)):
        new_yaml = crypt_func(**crypt_kwargs)

    new_yaml = crypt_func(**crypt_kwargs, allow_default=True)
    assert type(new_yaml) is CommentedMap
    new_yaml = crypt_func(**crypt_kwargs, allow_default=True, default_yaml=dict)
    assert type(new_yaml) is dict

    assert not check_file_exists(cred_file)

def test_is_encrypted(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']
    assert not is_encrypted(cred_file)

    encrypt_file(**crypt_kwargs)
    assert is_encrypted(cred_file, crypt_kwargs['crypt_backend'])

    decrypt_file(**crypt_kwargs)
    assert not is_encrypted(cred_file, crypt_kwargs['crypt_backend'])

def test_minimize_diff(crypt_kwargs):
    cred_file = crypt_kwargs['file_path']

    initial_content = openYaml(cred_file)

    initial_enc_content = encrypt_file(**crypt_kwargs)
    old_cred_file = TEST_FILE_OLD
    writeYamlToFile(old_cred_file, initial_enc_content)

    # test without changes
    decrypt_file(**crypt_kwargs)
    encrypt_file(**crypt_kwargs, minimize_diff=True, old_file_path=old_cred_file)

    diff_paths, removed_paths = compare_dicts(initial_enc_content, openYaml(cred_file))
    assert len(removed_paths) == 0 and len(diff_paths) == 0

    # test with one change
    new_content = copy.deepcopy(initial_content)
    # set_nested_yaml_attribute(new_content, 'first_cred.data.secret', 'new-value')
    new_content["first_cred"]["data"]["secret"] = "new-value"
    writeYamlToFile(cred_file, new_content)
    new_enc_content = encrypt_file(**crypt_kwargs, minimize_diff=True, old_file_path=old_cred_file)

    diff_paths, removed_paths = compare_dicts(initial_enc_content, new_enc_content)
    assert len(removed_paths) == 0
    assert ['first_cred', 'data', 'secret'] in diff_paths
    if crypt_kwargs.get('crypt_backend') == 'SOPS':
        assert ['sops', 'mac'] in diff_paths
    else:
        assert len(diff_paths) == 1

    # test wrong parameter combination
    with pytest.raises(ValueError):
        encrypt_file(**crypt_kwargs, minimize_diff=True)


def test_encrypt_file_scenarios(crypt_kwargs, effective_set_setup):

    backend = crypt_kwargs.get('crypt_backend')
    if not backend:
        return

    local_kwargs = crypt_kwargs.copy()
    encrypt_file(**local_kwargs)
    
    standard_yaml = openYaml(TEST_FILE)
    assert standard_yaml["first_cred"]["type"] == "secret"
    assert standard_yaml["first_cred"]["data"]["secret"] != "token-placeholder-123"

    mixed_content = (
        "api_key: plain-literal-text-token\n"
        "token: ref+aws/secret/token\n"
        "ESO_TOKEN:\n"
        "  normalizedSecretName: test_cluster_01/env-1/dummy-token\n"
        "  secretStoreId: default-store\n"
    )
    writeToFile(EFFECTIVE_SET_FILE, mixed_content)
    
    local_kwargs['file_path'] = EFFECTIVE_SET_FILE
    encrypt_file(**local_kwargs)
    
    mixed_yaml = openYaml(EFFECTIVE_SET_FILE)

    assert mixed_yaml['token'] == "ref+aws/secret/token"
    assert mixed_yaml['ESO_TOKEN']['secretStoreId'] == "default-store"
    assert mixed_yaml['ESO_TOKEN']['normalizedSecretName'] == "test_cluster_01/env-1/dummy-token"
    assert mixed_yaml['api_key'] != "plain-literal-text-token"

    pure_literal_content = (
        "api_key: plain-literal-text-token\n"
        "db_password: plain-password-123\n"
    )
    writeToFile(EFFECTIVE_SET_FILE, pure_literal_content)
    encrypt_file(**local_kwargs)
    
    full_yaml = openYaml(EFFECTIVE_SET_FILE)
    assert full_yaml['api_key'] != "plain-literal-text-token"
    assert full_yaml['db_password'] != "plain-password-123"


def test_decrypt_auto_detects_backend_from_file(crypt_kwargs):
    backend = crypt_kwargs.get('crypt_backend')
    if not backend:
        return

    encrypt_file(**crypt_kwargs)
    assert is_encrypted(TEST_FILE, backend)

    wrong_backend = "Fernet" if backend == "SOPS" else "SOPS"
    local_kwargs = crypt_kwargs.copy()
    local_kwargs['crypt_backend'] = wrong_backend
    
    decrypt_file(**local_kwargs)
    
    decrypted_yaml = openYaml(TEST_FILE)
    assert decrypted_yaml["first_cred"]["data"]["secret"] == "token-placeholder-123"
