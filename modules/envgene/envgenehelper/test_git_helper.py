from unittest.mock import MagicMock, patch

import pytest
from git import GitCommandError

from .git_helper import GitContext, GitRepoManager


def make_context(**overrides):
    defaults = {
        "platform": "gitlab",
        "server_protocol": "https",
        "server_host": "gitlab.example.com",
        "project_path": "org/repo",
        "ref_name": "main",
        "user_email": "ci@example.com",
        "user_name": "ci-bot",
        "token": "secret-token",
        "commit_sha": "abc123",
    }
    return GitContext(**{**defaults, **overrides})


def make_manager(ctx=None):
    if ctx is None:
        ctx = make_context()
    with patch("envgenehelper.git_helper.Repo"), \
            patch.object(GitContext, "from_env", return_value=ctx), \
            patch.object(GitRepoManager, "get_sparse_checkout_paths", return_value=[]):
        manager = GitRepoManager()
    manager.repo.git.execute = MagicMock()
    return manager


class TestResolveRemoteUrl:
    def test_gitlab(self):
        ctx = make_context(platform="gitlab", server_protocol="https",
                           server_host="gitlab.example.com", project_path="org/repo",
                           user_name="ci-bot", token="tok")
        manager = make_manager(ctx)
        assert manager._resolve_remote_url() == "https://ci-bot:tok@gitlab.example.com/org/repo.git"

    def test_github(self):
        ctx = make_context(platform="github", server_protocol="https",
                           server_host="github.com", project_path="org/repo",
                           token="gh-tok")
        manager = make_manager(ctx)
        assert manager._resolve_remote_url() == "https://gh-tok@github.com/org/repo.git"


class TestStageChanges:
    def test_filters_nonexistent_paths(self, tmp_path):
        existing = tmp_path / "environments" / "cluster" / "env"
        existing.mkdir(parents=True)

        manager = make_manager()
        manager.repo.git.add = MagicMock()
        manager.repo.git.diff = MagicMock(side_effect=["", (1, "", "")])

        manager.stage_changes([str(existing), "/nonexistent/path"])

        added_paths = manager.repo.git.add.call_args[0]
        assert str(existing) in added_paths
        assert "/nonexistent/path" not in added_paths

    def test_raises_on_unexpected_exit_code(self):
        manager = make_manager()
        manager.repo.git.add = MagicMock()
        manager.repo.git.diff = MagicMock(side_effect=["", (2, "", "")])

        with pytest.raises(RuntimeError):
            manager.stage_changes([])


class TestCherryPickAndPush:
    def test_aborts_on_cherry_pick_git_error(self):
        manager = make_manager()
        manager._fetch = MagicMock()
        manager.repo.git.cherry_pick = MagicMock(
            side_effect=[GitCommandError("cherry-pick", 1, "conflict"), None]
        )

        with pytest.raises(RuntimeError):
            manager._cherry_pick_and_push("deadbeef")

        manager.repo.git.cherry_pick.assert_called_with("--abort", with_exceptions=False)

    def test_aborts_on_cherry_pick_os_error(self):
        manager = make_manager()
        manager._fetch = MagicMock()
        manager.repo.git.cherry_pick = MagicMock(side_effect=[OSError("disk full"), None])

        with pytest.raises(RuntimeError):
            manager._cherry_pick_and_push("deadbeef")

        manager.repo.git.cherry_pick.assert_called_with("--abort", with_exceptions=False)

    def test_aborts_on_push_error(self):
        manager = make_manager()
        manager._fetch = MagicMock()
        manager.repo.git.cherry_pick = MagicMock()
        manager.repo.git.push = MagicMock(side_effect=GitCommandError("push", 1, "rejected"))

        with pytest.raises(RuntimeError):
            manager._cherry_pick_and_push("deadbeef")

        manager.repo.git.cherry_pick.assert_called_with("--abort", with_exceptions=False)
