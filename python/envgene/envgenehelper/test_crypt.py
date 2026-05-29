import os
import copy
import shutil
import tempfile
import pytest
from subprocess import SubprocessError

from ruyaml import CommentedMap

from .collections_helper import compare_dicts

from . import crypt as crypt_module
from .crypt import (
    decrypt_file,
    encrypt_file,
    decrypt_all_cred_files_for_env,
    encrypt_all_cred_files_for_env,
    is_encrypted,
)
from .file_helper import check_file_exists, writeToFile
from .yaml_helper import openYaml, set_nested_yaml_attribute, writeYamlToFile

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

    new_yaml = decrypt_file(**crypt_kwargs, ignore_is_crypt=False, is_crypt=False)
    assert init_yaml != new_yaml # should not try to decrypt with is_crypt false, so new_yaml is still encrypted
    new_yaml = decrypt_file(**crypt_kwargs, ignore_is_crypt=True, is_crypt=False)
    assert init_yaml == new_yaml

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
    set_nested_yaml_attribute(new_content, 'first_cred.data.secret', 'new-value')
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


@pytest.fixture(params=['SOPS', 'Fernet'])
def encrypt_all_env(request, monkeypatch):
    crypt_backend = request.param
    if crypt_backend == 'SOPS':
        secret_key = crypt_test_data[0]['secret_key']
        public_key = crypt_test_data[0]['public_key']
        monkeypatch.setenv('ENVGENE_AGE_PRIVATE_KEY', secret_key)
        monkeypatch.setenv('PUBLIC_AGE_KEYS', public_key)
    else:
        secret_key = crypt_test_data[1]['secret_key']
        public_key = None
        monkeypatch.setenv('SECRET_KEY', secret_key)

    project_dir = tempfile.mkdtemp()
    cred_dir = os.path.join(project_dir, 'configuration', 'credentials')
    os.makedirs(cred_dir)
    cred_file = os.path.join(cred_dir, 'credentials.yml')
    shutil.copy(TEST_FILE, cred_file)

    config_path = os.path.join(project_dir, 'configuration', 'config.yml')
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(f'crypt: true\ncrypt_backend: {crypt_backend}\n')

    monkeypatch.setenv('CI_PROJECT_DIR', project_dir)
    monkeypatch.delenv('ENV_NAMES', raising=False)
    monkeypatch.setattr(crypt_module, 'BASE_DIR', project_dir)

    bulk_kwargs = {
        'crypt_backend': crypt_backend,
        'secret_key': secret_key,
        'public_key': public_key,
        'ignore_is_crypt': True,
        'is_crypt': True,
    }

    yield cred_file, bulk_kwargs

    crypt_module._cleanup_cred_backups()
    shutil.rmtree(project_dir, ignore_errors=True)


def test_encrypt_all_cred_files_minimize_diff(encrypt_all_env):
    cred_file, bulk_kwargs = encrypt_all_env
    crypt_kwargs = {'file_path': cred_file, **bulk_kwargs}

    initial_enc_content = encrypt_file(**crypt_kwargs)
    decrypt_all_cred_files_for_env(**bulk_kwargs)

    backup_dir = crypt_module._cred_backup_dir()
    backup_path = crypt_module._cred_backup_path(cred_file)
    assert backup_dir.startswith(tempfile.gettempdir())
    assert not backup_dir.startswith(os.path.dirname(cred_file))
    assert os.path.exists(backup_path)

    encrypt_all_cred_files_for_env(**bulk_kwargs)
    assert not os.path.exists(backup_dir)

    diff_paths, removed_paths = compare_dicts(initial_enc_content, openYaml(cred_file))
    assert len(removed_paths) == 0 and len(diff_paths) == 0


def test_encrypt_all_cred_files_no_minimize_diff_without_backup(encrypt_all_env):
    cred_file, bulk_kwargs = encrypt_all_env
    crypt_kwargs = {'file_path': cred_file, **bulk_kwargs}

    initial_enc_content = encrypt_file(**crypt_kwargs)
    decrypt_file(**crypt_kwargs)

    # No decrypt_all called beforehand, so no backup exists
    assert crypt_module._get_cred_backup_path(cred_file) is None

    encrypt_all_cred_files_for_env(**bulk_kwargs)
    new_enc_content = openYaml(cred_file)

    # Without minimize_diff all values are re-encrypted, so ciphertext must differ
    diff_paths, _ = compare_dicts(initial_enc_content, new_enc_content)
    assert len(diff_paths) > 0
