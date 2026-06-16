import logging
import os
import shutil
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


@pytest.fixture
def cred_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('CI_PROJECT_DIR', str(tmp_path))
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
            mcd.main()

        assert openYaml(str(cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_only_changed_secret_fields_differ_from_head(self, cred_repo):
        _, _, cred_path = cred_repo
        head_encrypted = openYaml(str(cred_path))
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        mcd.main()

        diff_paths, removed_paths = compare_dicts(head_encrypted, openYaml(str(cred_path)))
        assert removed_paths == []
        assert ['first_cred', 'data', 'secret'] in diff_paths
        assert ['sops', 'mac'] in diff_paths

    @pytest.mark.unit
    def test_new_cred_file_is_left_unchanged(self, cred_repo):
        repo, tmp_path, _ = cred_repo
        new_cred_path = tmp_path / NEW_CRED_REL_PATH
        new_cred_path.parent.mkdir(parents=True)
        writeToFile(new_cred_path, CRED_CONTENT)
        _encrypt_cred(new_cred_path)
        repo.git.add(NEW_CRED_REL_PATH)
        working_copy_before = openYaml(str(new_cred_path))

        mcd.main()

        assert openYaml(str(new_cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_non_cred_files_are_left_unchanged(self, cred_repo):
        _, tmp_path, cred_path = cred_repo
        readme_path = tmp_path / 'README.md'
        writeToFile(readme_path, 'changed\n')
        head_encrypted = openYaml(str(cred_path))

        mcd.main()

        assert readme_path.read_text(encoding='utf-8') == 'changed\n'
        diff_paths, removed_paths = compare_dicts(head_encrypted, openYaml(str(cred_path)))
        assert removed_paths == []
        assert diff_paths == []

    @pytest.mark.unit
    def test_git_diff_failure_logs_error_and_aborts(self, monkeypatch, caplog):
        repo = MagicMock()
        repo.git.diff.side_effect = GitCommandError('diff', 128, stderr='fatal: bad revision')
        monkeypatch.setenv('CI_PROJECT_DIR', '/tmp/repo')

        with patch.object(mcd, 'get_crypt', return_value=True), patch.object(mcd, 'Repo', return_value=repo):
            with caplog.at_level(logging.ERROR, logger='envgene'):
                with pytest.raises(RuntimeError, match='git diff against HEAD failed'):
                    mcd.main()

        assert 'git diff against HEAD failed' in caplog.text

    @pytest.mark.unit
    def test_head_read_failure_logs_warning_and_leaves_file_unchanged(self, cred_repo, caplog):
        _, _, cred_path = cred_repo
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')
        working_copy_before = openYaml(str(cred_path))

        repo = MagicMock()
        repo.git.diff.return_value = f'{CRED_REL_PATH}\n'
        repo.head.commit.tree.__getitem__.side_effect = OSError('cannot read blob at HEAD')

        with patch.object(mcd, 'Repo', return_value=repo):
            with caplog.at_level(logging.WARNING, logger='envgene'):
                mcd.main()

        assert 'Cannot read credential file at HEAD' in caplog.text
        assert openYaml(str(cred_path)) == working_copy_before

    @pytest.mark.unit
    def test_cache_hit_skips_decrypt_and_encrypt(self, cred_repo, tmp_path, monkeypatch):
        _, _, cred_path = cred_repo
        cache_dir = tmp_path / 'minimize_cache'
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(cache_dir))
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        with patch.object(mcd, 'decrypt_file') as decrypt_mock, patch.object(mcd, 'encrypt_file') as encrypt_mock:
            mcd.main()
            mcd.main()

        assert decrypt_mock.call_count == 1
        assert encrypt_mock.call_count == 1
        assert len(list(cache_dir.glob('*.enc'))) == 1

    @pytest.mark.unit
    def test_cache_miss_when_head_changes(self, cred_repo, tmp_path, monkeypatch):
        repo, repo_path, cred_path = cred_repo
        cache_dir = tmp_path / 'minimize_cache'
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', str(cache_dir))
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        with patch.object(mcd, 'decrypt_file') as decrypt_mock, patch.object(mcd, 'encrypt_file') as encrypt_mock:
            mcd.main()
            assert decrypt_mock.call_count == 1
            assert encrypt_mock.call_count == 1

            shutil.copy2(cred_path, repo_path / 'head_snapshot.yml')
            _encrypt_cred(cred_path)
            repo.git.add(CRED_REL_PATH)
            repo.index.commit('remote cred rotation')

            _simulate_pipeline_cred_update(cred_path, 'updated-secret-again')
            mcd.main()

        assert decrypt_mock.call_count == 2
        assert encrypt_mock.call_count == 2
        assert len(list(cache_dir.glob('*.enc'))) == 2

    @pytest.mark.unit
    def test_default_cache_dir_uses_ci_job_id(self, monkeypatch):
        monkeypatch.delenv('MINIMIZE_CRED_DIFF_CACHE_DIR', raising=False)
        monkeypatch.setenv('CI_JOB_ID', '55767405')

        assert mcd._default_cache_dir() == Path('/tmp/minimize_cred_diff_cache_55767405')

    @pytest.mark.unit
    def test_default_cache_dir_uses_process_id_without_ci(self, monkeypatch):
        monkeypatch.delenv('MINIMIZE_CRED_DIFF_CACHE_DIR', raising=False)
        monkeypatch.delenv('CI_JOB_ID', raising=False)
        monkeypatch.delenv('GITHUB_RUN_ID', raising=False)

        cache_dir = mcd._default_cache_dir()

        assert cache_dir == Path(f'/tmp/minimize_cred_diff_cache_{os.getpid()}')

    @pytest.mark.unit
    def test_cache_disabled_runs_minimize_on_every_call(self, cred_repo, monkeypatch):
        _, _, cred_path = cred_repo
        monkeypatch.setenv('MINIMIZE_CRED_DIFF_CACHE_DIR', 'off')
        _simulate_pipeline_cred_update(cred_path, 'updated-secret')

        with patch.object(mcd, 'decrypt_file') as decrypt_mock, patch.object(mcd, 'encrypt_file') as encrypt_mock:
            mcd.main()
            mcd.main()

        assert decrypt_mock.call_count == 2
        assert encrypt_mock.call_count == 2
