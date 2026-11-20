import os

import pytest


@pytest.fixture(autouse=True)
def restore_environ():
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")
    for name in ("CLUSTER_NAME", "ENVIRONMENT_NAME", "IS_LOCAL_DEV_TEST_ENVGENE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def job_preparation_calls(monkeypatch) -> list[tuple]:
    calls: list[tuple] = []
    monkeypatch.setattr(
        "pipeline.orchestrator.run_sparse_checkout",
        lambda env_names: calls.append(("sparse_checkout", list(env_names))),
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.install_certificates",
        lambda: calls.append(("install_certificates",)),
    )
    return calls


@pytest.fixture
def mock_worktrees(monkeypatch):
    monkeypatch.setattr("pipeline.multi_env_runner._create_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._sparse_checkout_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._remove_worktree", lambda *args: None)
