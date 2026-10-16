from unittest.mock import MagicMock, patch

import pytest

from envgenehelper import CurrentEnvInstanceStore
from git_commit.sync_object_hashes import COMMIT_MESSAGE, sync_object_hashes

MANIFEST = "environments/cluster-01/env-01/.envgene/object-hashes.json"


@pytest.fixture
def instance_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    for env_name in ("env-01", "env-02"):
        env_dir = tmp_path / "environments" / "cluster-01" / env_name
        objects = CurrentEnvInstanceStore(env_dir)
        objects.put(env_dir / "tenant.yml", {"name": "tenant"})
        objects.flush()
    return tmp_path


def _run_sync():
    manager = MagicMock()
    manager.create_detached_commit.return_value = "sha"
    with patch("git_commit.sync_object_hashes.GitRepoManager", return_value=manager) as manager_class:
        sync_object_hashes()
    return manager_class, manager


def test_nothing_is_committed_when_manifests_match_the_repository(instance_repo):
    manager_class, _ = _run_sync()

    manager_class.assert_not_called()


def test_manual_edit_commits_only_the_manifest_of_the_edited_environment(instance_repo):
    (instance_repo / "environments" / "cluster-01" / "env-01" / "tenant.yml").write_text("name: edited\n")

    _, manager = _run_sync()

    manager.stage_changes.assert_called_once_with([MANIFEST])
    manager.create_detached_commit.assert_called_once_with(COMMIT_MESSAGE)
    manager.retry_cherry_pick_and_push.assert_called_once_with("sha")
