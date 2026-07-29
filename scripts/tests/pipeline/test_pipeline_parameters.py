import os

import pytest

from pipeline.orchestrator import dispatch
from pipeline.pipeline_parameters import PipelineParametersHandler
from pipeline.resolve_env_names import resolve_env_names


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)
    monkeypatch.delenv("PIPELINE_TYPE", raising=False)
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")


class TestResolveEnvNames:
    @pytest.mark.unit
    def test_fails_when_no_env_selection(self):
        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_names()

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "extra_env",
        [
            {"CLUSTER_NAME": "cluster-01"},
            {"ENVIRONMENT_NAME": "env-01"},
            {"CLUSTER_NAME": "cluster-01", "ENVIRONMENT_NAME": "env-01"},
        ],
    )
    def test_fails_when_env_names_combined_with_per_env_vars(self, monkeypatch, extra_env):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        for key, value in extra_env.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(
            ValueError,
            match="Set ENV_NAMES only, or both CLUSTER_NAME and ENVIRONMENT_NAME, but not both at the same time",
        ):
            resolve_env_names()

    @pytest.mark.unit
    def test_passes_with_env_names_only(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_fails_when_env_names_has_invalid_format(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01-env-01")

        with pytest.raises(ValueError, match="Invalid environment name"):
            resolve_env_names()

    @pytest.mark.unit
    def test_synthesises_env_names_from_cluster_and_environment_name(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_fails_when_only_cluster_name_provided(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")

        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_names()

    @pytest.mark.unit
    def test_allows_multi_env_when_pipeline_type_unset(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        assert resolve_env_names() == ["cluster-01/env-01", "cluster-02/env-02"]

    @pytest.mark.unit
    def test_rejects_multi_env_for_gitlab_deploy(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        with pytest.raises(ValueError, match="Multiple values in ENV_NAMES are not supported"):
            resolve_env_names()

    @pytest.mark.unit
    def test_allows_single_env_for_gitlab_deploy(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]


class TestPipelineParametersFromEnv:
    @pytest.mark.unit
    def test_populates_fields_from_full_env_name(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        ctx = PipelineParametersHandler.from_env()

        assert ctx.full_env_name == "cluster-01/env-01"
        assert ctx.cluster_name == "cluster-01"
        assert ctx.env_name == "env-01"
        assert os.environ["FULL_ENV_NAME"] == "cluster-01/env-01"
        assert os.environ["CLUSTER_NAME"] == "cluster-01"
        assert os.environ["ENVIRONMENT_NAME"] == "env-01"


@pytest.fixture
def mock_worktrees(monkeypatch):
    monkeypatch.setattr("pipeline.multi_env_runner._create_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._sparse_checkout_worktree", lambda *args: None)
    monkeypatch.setattr("pipeline.multi_env_runner._remove_worktree", lambda *args: None)


class TestRunSingleEnvEntrypoint:
    @pytest.mark.unit
    def test_run_child_subprocess_sets_per_env_vars(self, monkeypatch, tmp_path):
        from pipeline.multi_env_runner import _run_child_subprocess

        captured: dict = {}

        class FakeProc:
            def __init__(self):
                self.stdout = open(os.devnull, encoding="utf-8")

            def wait(self):
                self.stdout.close()
                return 0

        def fake_popen(cmd, **kwargs):
            captured["env"] = kwargs["env"]
            return FakeProc()

        monkeypatch.setattr("pipeline.multi_env_runner.subprocess.Popen", fake_popen)

        worktree = tmp_path / "worktree"
        _run_child_subprocess("cluster-02/env-02", worktree, tmp_path / "logs")

        assert captured["env"]["ENV_NAMES"] == "cluster-02/env-02"
        assert captured["env"]["FULL_ENV_NAME"] == "cluster-02/env-02"
        assert captured["env"]["CLUSTER_NAME"] == "cluster-02"
        assert captured["env"]["ENVIRONMENT_NAME"] == "env-02"
        assert captured["env"]["CI_PROJECT_DIR"] == str(worktree)


class TestDispatch:
    @pytest.mark.unit
    def test_single_env_runs_pipeline_in_process(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        called: list[str] = []

        monkeypatch.setattr(
            "pipeline.orchestrator.run_single_env_pipeline",
            lambda: called.append(True),
        )

        assert dispatch() == 0
        assert called == [True]

    @pytest.mark.unit
    def test_multi_env_fan_out_runs_subprocess_per_env(self, monkeypatch, tmp_path, mock_worktrees):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        runs: list[str] = []

        def fake_run_child(full_env_name, worktree_path, logs_dir):
            runs.append(full_env_name)
            return 0

        monkeypatch.setattr("pipeline.multi_env_runner._run_child_subprocess", fake_run_child)
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", pytest.fail)

        assert dispatch() == 0
        assert sorted(runs) == ["cluster-01/env-01", "cluster-02/env-02"]

    @pytest.mark.unit
    def test_multi_env_collects_failures(self, monkeypatch, tmp_path, mock_worktrees):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        def fake_run_child(full_env_name, worktree_path, logs_dir):
            return 0 if full_env_name == "cluster-01/env-01" else 2

        monkeypatch.setattr("pipeline.multi_env_runner._run_child_subprocess", fake_run_child)

        assert dispatch() == 1
