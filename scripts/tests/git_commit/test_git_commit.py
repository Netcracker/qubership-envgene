from unittest.mock import MagicMock, call, patch

import pytest

from git_commit.git_commit import build_commit_message, git_commit


class TestBuildCommitMessage:
    def test_default(self, monkeypatch):
        monkeypatch.setenv("DEPLOYMENT_TICKET_ID", "TICKET-123")
        monkeypatch.setenv("CLUSTER_NAME", "my-cluster")
        monkeypatch.setenv("ENVIRONMENT_NAME", "my-env")

        msg = build_commit_message()

        assert msg == 'TICKET-123 [ci_skip] Update "my-cluster/my-env" environment'

    def test_custom_message(self, monkeypatch):
        monkeypatch.setenv("DEPLOYMENT_TICKET_ID", "TICKET-123")
        monkeypatch.setenv("COMMIT_MESSAGE", "deploy hotfix")

        msg = build_commit_message()

        assert msg == "TICKET-123 deploy hotfix"

    def test_with_session_id(self, monkeypatch):
        monkeypatch.setenv("DEPLOYMENT_TICKET_ID", "TICKET-123")
        monkeypatch.setenv("CLUSTER_NAME", "my-cluster")
        monkeypatch.setenv("ENVIRONMENT_NAME", "my-env")
        monkeypatch.setenv("DEPLOYMENT_SESSION_ID", "sess-abc")

        msg = build_commit_message()

        assert msg == 'TICKET-123 [ci_skip] Update "my-cluster/my-env" environment\n\nDEPLOYMENT-SESSION-ID: sess-abc'

    def test_empty_ticket_no_leading_space(self, monkeypatch):
        monkeypatch.delenv("DEPLOYMENT_TICKET_ID", raising=False)
        monkeypatch.setenv("CLUSTER_NAME", "c")
        monkeypatch.setenv("ENVIRONMENT_NAME", "e")

        msg = build_commit_message()

        assert not msg.startswith(" ")
        assert msg == '[ci_skip] Update "c/e" environment'


class TestGitCommit:
    @staticmethod
    def _run_commit(manager):
        with patch("git_commit.git_commit.GitRepoManager", return_value=manager), \
                patch("git_commit.git_commit._git_commit_lock"), \
                patch("git_commit.git_commit.minimize_cred_diffs"):
            git_commit()

    def test_removes_dcl_paths_before_checking_for_staged_changes(self):
        manager = MagicMock()
        manager._has_staged_changes.return_value = False

        self._run_commit(manager)

        stage_idx = manager.mock_calls.index(call.stage_changes())
        remove_dcl_idx = manager.mock_calls.index(call.remove_dcl_paths_from_index())
        check_idx = manager.mock_calls.index(call._has_staged_changes())
        assert stage_idx < remove_dcl_idx < check_idx

    def test_skips_commit_when_no_staged_changes_remain_after_dcl_removal(self):
        manager = MagicMock()
        manager._has_staged_changes.return_value = False

        self._run_commit(manager)

        manager.create_detached_commit.assert_not_called()
        manager.retry_cherry_pick_and_push.assert_not_called()

    def test_commits_and_pushes_when_real_changes_are_staged(self):
        manager = MagicMock()
        manager._has_staged_changes.return_value = True
        manager.create_detached_commit.return_value = "commit-sha"
        manager.snapshot_excluded_paths.return_value = ["effective-set/deployment"]

        self._run_commit(manager)

        manager.create_detached_commit.assert_called_once()
        manager.retry_cherry_pick_and_push.assert_called_once_with("commit-sha")
        manager.restore_excluded_paths.assert_called_once_with(["effective-set/deployment"])

    def test_restores_excluded_paths_even_if_push_fails(self):
        manager = MagicMock()
        manager._has_staged_changes.return_value = True
        manager.create_detached_commit.return_value = "commit-sha"
        manager.snapshot_excluded_paths.return_value = ["effective-set/deployment"]
        manager.retry_cherry_pick_and_push.side_effect = RuntimeError("push failed")

        with pytest.raises(RuntimeError):
            self._run_commit(manager)

        manager.restore_excluded_paths.assert_called_once_with(["effective-set/deployment"])
