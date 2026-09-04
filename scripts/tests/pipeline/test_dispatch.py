import pytest

from pipeline.orchestrator import dispatch


class TestDispatch:
    @pytest.mark.unit
    def test_single_env_runs_pipeline_in_process(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        called: list[str] = []

        monkeypatch.setattr(
            "pipeline.orchestrator.run_single_env_pipeline",
            lambda: called.append(True),
        )
        finalize_calls: list[str] = []
        monkeypatch.setattr(
            "pipeline.orchestrator.finalize_artifacts",
            lambda *args, **kwargs: finalize_calls.append(True),
        )

        assert dispatch() == 0
        assert called == [True]
        assert finalize_calls == [True]

    @pytest.mark.unit
    def test_fan_out_child_skips_finalize(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("ENVGENE_FAN_OUT_CHILD", "1")
        called: list[str] = []

        monkeypatch.setattr(
            "pipeline.orchestrator.run_single_env_pipeline",
            lambda: called.append(True),
        )
        monkeypatch.setattr(
            "pipeline.orchestrator.finalize_artifacts",
            pytest.fail,
        )

        assert dispatch() == 0
        assert called == [True]

    @pytest.mark.unit
    def test_multi_env_fan_out_runs_subprocess_per_env(self, monkeypatch, tmp_path, mock_worktrees):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        runs: list[str] = []

        def fake_run_child(full_env_name, worktree_path, logs_dir, artifacts_output_dir):
            runs.append(full_env_name)
            return 0

        monkeypatch.setattr("pipeline.multi_env_runner._run_child_subprocess", fake_run_child)
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", pytest.fail)
        finalize_calls: list[str] = []
        monkeypatch.setattr(
            "pipeline.orchestrator.finalize_artifacts",
            lambda *args, **kwargs: finalize_calls.append(True),
        )

        assert dispatch() == 0
        assert sorted(runs) == ["cluster-01/env-01", "cluster-02/env-02"]
        assert finalize_calls == [True]

    @pytest.mark.unit
    def test_multi_env_collects_failures(self, monkeypatch, tmp_path, mock_worktrees):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        monkeypatch.setattr("pipeline.orchestrator.finalize_artifacts", lambda *args, **kwargs: None)

        def fake_run_child(full_env_name, worktree_path, logs_dir, artifacts_output_dir):
            return 0 if full_env_name == "cluster-01/env-01" else 2

        monkeypatch.setattr("pipeline.multi_env_runner._run_child_subprocess", fake_run_child)

        assert dispatch() == 1
