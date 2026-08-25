from unittest.mock import MagicMock, patch

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


class TestModeAwareCommit:
    @staticmethod
    def _run_commit(manager):
        with patch("git_commit.git_commit.GitRepoManager", return_value=manager), \
                patch("git_commit.git_commit._git_commit_lock"), \
                patch("git_commit.git_commit.minimize_cred_diffs"):
            git_commit()

    def test_gitlab_deploy_restores_dcl_outputs_after_commit(self):
        manager = MagicMock()
        manager.stage_changes.return_value = True
        manager.create_detached_commit.return_value = "commit-sha"
        manager.snapshot_excluded_paths.return_value = ["effective-set/deployment"]

        self._run_commit(manager)

        manager.stage_changes.assert_called_once_with()
        manager.remove_dcl_paths_from_index.assert_called_once_with()
        manager.restore_excluded_paths.assert_called_once_with(["effective-set/deployment"])

    def test_legacy_does_not_prepare_dcl_outputs_for_removal(self):
        manager = MagicMock()
        manager.stage_changes.return_value = False

        self._run_commit(manager)

        manager.remove_dcl_paths_from_index.assert_not_called()
