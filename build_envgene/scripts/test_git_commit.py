from git_commit import build_commit_message


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
