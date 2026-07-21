from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import GitCommandError, Repo

from envgenehelper import decrypt_file, encrypt_file
from envgenehelper.collections_helper import compare_dicts
from envgenehelper.file_helper import writeToFile
from envgenehelper.logger import logger as envgene_logger
from envgenehelper.yaml_helper import openYaml, set_nested_yaml_attribute, writeYamlToFile

import minimize_cred_diffs as mcd

CRED_REL_PATH = 'environments/cluster/env/configuration/credentials.yml'
NEW_CRED_REL_PATH = 'environments/cluster/env/Inventory/credentials/extra-creds.yml'
CRED_CONTENT = """\
first_cred:
    type: secret
    data:
        secret: token-placeholder-123
second_cred:
    type: secret
    data:
        secret: static-secret-456
registry_cred:
    type: usernamePassword
    data:
        username: registry-user
        password: registry-password-789
"""
SOPS_AGE_SECRET_KEY = 'AGE-SECRET-KEY-1AQVCSQDRR5F70H3WJL82EMHMPSDMJPRP0GREJE0Y3M5YJZ25GT9SN0Y6FM'
SOPS_PUBLIC_KEY = 'age1y4hfj9zz05dtqycfk55y4csddch6w2lu9l6wx7r68at5x897ea3qjh0gl9'
SOPS_CRYPT_KWARGS = {
    'secret_key': SOPS_AGE_SECRET_KEY,
    'public_key': SOPS_PUBLIC_KEY,
    'crypt_backend': 'SOPS',
    'ignore_is_crypt': True,
}


@pytest.fixture(autouse=True)
def attach_caplog_handler(caplog):
    envgene_logger.addHandler(caplog.handler)
    yield
    envgene_logger.removeHandler(caplog.handler)


def _encrypt_cred(cred_path: Path) -> None:
    encrypt_file(str(cred_path), **SOPS_CRYPT_KWARGS)


def _simulate_pipeline_cred_update(cred_path: Path, new_secret: str) -> None:
    decrypt_file(str(cred_path), **SOPS_CRYPT_KWARGS)
    plaintext = openYaml(str(cred_path))
    set_nested_yaml_attribute(plaintext, 'first_cred.data.secret', new_secret)
    writeYamlToFile(str(cred_path), plaintext)
    _encrypt_cred(cred_path)


def _assert_only_first_cred_secret_and_mac_differ_from_head(head_encrypted: dict, cred_path: Path) -> None:
    diff_paths, removed_paths = compare_dicts(head_encrypted, openYaml(str(cred_path)))
    allowed_sops_fields = {'mac', 'lastmodified'}
    assert removed_paths == []
    assert ['first_cred', 'data', 'secret'] in diff_paths
    for path in diff_paths:
        if path == ['first_cred', 'data', 'secret']:
            continue
        if path[0] == 'sops' and len(path) == 2 and path[1] in allowed_sops_fields:
            continue
        pytest.fail(f'unexpected diff at {path}')


def _cache_files(cache_dir: Path) -> list[Path]:
    return [path for path in cache_dir.rglob('*') if path.is_file()]


@pytest.fixture
def cred_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('CI_PROJECT_DIR', str(tmp_path))
    monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(tmp_path / 'minimize_cred_diff_cache'))
    monkeypatch.setenv('ENVGENE_AGE_PRIVATE_KEY', SOPS_AGE_SECRET_KEY)
    monkeypatch.setenv('PUBLIC_AGE_KEYS', SOPS_PUBLIC_KEY)

    config_dir = tmp_path / 'configuration'
    config_dir.mkdir(parents=True)
    writeToFile(
        config_dir / 'config.yml',
        'crypt: true\ncrypt_backend: SOPS\n',
    )

    repo = Repo.init(tmp_path)
    with repo.config_writer() as cw:
        cw.set_value('user', 'email', 'test@example.com')
        cw.set_value('user', 'name', 'test')

    cred_path = tmp_path / CRED_REL_PATH
    cred_path.parent.mkdir(parents=True)
    writeToFile(cred_path, CRED_CONTENT)
    _encrypt_cred(cred_path)
    repo.git.add('-A')
    repo.index.commit('add encrypted creds')
    return repo, tmp_path, cred_path


class TestCredentialDiffMinimization:
    @pytest.mark.unit
    def test_crypt_disabled_leaves_working_tree_unchanged(self, cred_repo):
        _, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')
        working_copy_before = openYaml(str(cred_path))

        with patch.object(mcd, 'get_crypt', return_value=False):
            mcd.minimize_cred_diffs()

        assert openYaml(str(cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_only_changed_credential_fields_differ_from_head(self, cred_repo):
        _, _, cred_path = cred_repo
        head_encrypted = openYaml(str(cred_path))
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        mcd.minimize_cred_diffs()

        _assert_only_first_cred_secret_and_mac_differ_from_head(head_encrypted, cred_path)

    @pytest.mark.unit
    def test_deleted_cred_file_does_not_crash(self, cred_repo):
        repo, _, _ = cred_repo
        repo.git.rm(CRED_REL_PATH)

        mcd.minimize_cred_diffs()

    @pytest.mark.unit
    def test_new_cred_file_is_left_unchanged(self, cred_repo):
        repo, tmp_path, _ = cred_repo
        new_cred_path = tmp_path / NEW_CRED_REL_PATH
        new_cred_path.parent.mkdir(parents=True)
        writeToFile(new_cred_path, CRED_CONTENT)
        _encrypt_cred(new_cred_path)
        repo.git.add(NEW_CRED_REL_PATH)
        working_copy_before = openYaml(str(new_cred_path))

        mcd.minimize_cred_diffs()

        assert openYaml(str(new_cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_git_diff_failure_aborts(self, monkeypatch, tmp_path):
        repo = MagicMock()
        repo.git.diff.side_effect = GitCommandError('diff', 128, stderr='fatal: bad revision')
        monkeypatch.setenv('CI_PROJECT_DIR', '/tmp/repo')
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(tmp_path / 'cache'))

        with patch.object(mcd, 'get_crypt', return_value=True), patch.object(mcd, 'Repo', return_value=repo):
            with pytest.raises(RuntimeError, match='git diff against HEAD failed'):
                mcd.minimize_cred_diffs()

    @pytest.mark.unit
    def test_head_read_failure_leaves_file_unchanged(self, cred_repo):
        _, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')
        working_copy_before = openYaml(str(cred_path))

        repo = MagicMock()
        repo.git.diff.return_value = f'{CRED_REL_PATH}\n'
        repo.head.commit.tree.__getitem__.side_effect = OSError('cannot read blob at HEAD')

        with patch.object(mcd, 'Repo', return_value=repo):
            mcd.minimize_cred_diffs()

        assert openYaml(str(cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_push_retry_reproduces_same_minimised_output(self, cred_repo):
        _, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')
        pre_minimised_input = cred_path.read_bytes()

        mcd.minimize_cred_diffs()
        first_pass = cred_path.read_bytes()

        cred_path.write_bytes(pre_minimised_input)
        mcd.minimize_cred_diffs()

        assert cred_path.read_bytes() == first_pass

    @pytest.mark.unit
    def test_head_change_recomputes_against_new_base(self, cred_repo):
        repo, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        mcd.minimize_cred_diffs()
        first_pass = cred_path.read_bytes()

        _simulate_pipeline_cred_update(cred_path, 'remote-head-secret')
        repo.git.add(CRED_REL_PATH)
        repo.index.commit('remote credential update')
        new_head_encrypted = openYaml(str(cred_path))

        _simulate_pipeline_cred_update(cred_path, 'updated-secret-again')
        mcd.minimize_cred_diffs()

        assert cred_path.read_bytes() != first_pass
        _assert_only_first_cred_secret_and_mac_differ_from_head(new_head_encrypted, cred_path)

    @pytest.mark.unit
    def test_separate_cache_dirs_do_not_share_entries(self, cred_repo, tmp_path, monkeypatch):
        _, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        cache_a = tmp_path / 'job-a-cache'
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(cache_a))
        mcd.minimize_cred_diffs()
        cache_a_files = _cache_files(cache_a)

        cache_b = tmp_path / 'job-b-cache'
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(cache_b))
        mcd.minimize_cred_diffs()

        assert cache_a_files
        assert _cache_files(cache_b)
        assert _cache_files(cache_b) != cache_a_files
