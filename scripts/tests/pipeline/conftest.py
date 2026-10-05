import pytest


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")


@pytest.fixture
def mock_worktrees(monkeypatch):
    monkeypatch.setattr("pipeline.multi_env_runner._create_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._sparse_checkout_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._remove_worktree", lambda *args: None)
