import json
import logging
import os
from types import SimpleNamespace

import pytest

from envgenehelper import logger
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


class TestPrepareJob:
    @pytest.fixture(autouse=True)
    def no_pipeline_run(self, monkeypatch):
        monkeypatch.setattr("pipeline.orchestrator.finalize_artifacts", lambda *args, **kwargs: None)

    @pytest.mark.unit
    def test_resolves_env_then_checks_out_then_installs_certs(self, monkeypatch, tmp_path, job_preparation_calls):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")
        monkeypatch.delenv("ENV_NAMES", raising=False)
        seen_env_names: list[str] = []
        monkeypatch.setattr(
            "pipeline.orchestrator.run_single_env_pipeline",
            lambda: seen_env_names.append(os.environ["ENV_NAMES"]),
        )

        assert dispatch() == 0
        assert job_preparation_calls == [("sparse_checkout", ["cluster-01/env-01"]), ("install_certificates",)]
        assert seen_env_names == ["cluster-01/env-01"]
        env_dir = f"{tmp_path}/environments/cluster-01/env-01"
        assert os.environ["LOCAL_APPDEFS_PATH"] == f"{env_dir}/AppDefs"
        assert os.environ["LOCAL_REGDEFS_PATH"] == f"{env_dir}/RegDefs"

    @pytest.mark.unit
    def test_multi_env_checks_out_all_envs_once(self, monkeypatch, mock_worktrees, job_preparation_calls):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        monkeypatch.setattr("pipeline.multi_env_runner._run_child_subprocess", lambda *args: 0)

        assert dispatch() == 0
        assert job_preparation_calls == [
            ("sparse_checkout", ["cluster-01/env-01", "cluster-02/env-02"]),
            ("install_certificates",),
        ]
        assert "LOCAL_APPDEFS_PATH" not in os.environ

    @pytest.mark.unit
    def test_fan_out_child_skips_preparation(self, monkeypatch, job_preparation_calls):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("ENVGENE_FAN_OUT_CHILD", "1")
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", lambda: None)

        assert dispatch() == 0
        assert job_preparation_calls == []
        assert "LOCAL_APPDEFS_PATH" not in os.environ

    @pytest.mark.unit
    def test_local_test_mode_skips_checkout(self, monkeypatch, job_preparation_calls, caplog):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("IS_LOCAL_DEV_TEST_ENVGENE", "true")
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", lambda: None)
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.INFO, logger=logger.name):
            assert dispatch() == 0
        assert job_preparation_calls == [("install_certificates",)]
        assert os.environ["LOCAL_APPDEFS_PATH"].endswith("/environments/cluster-01/env-01/AppDefs")
        assert "END: prepare_job" in caplog.text
        assert "- SUCCESS" in caplog.text

    @pytest.mark.unit
    def test_invalid_env_selection_fails_before_checkout(self, monkeypatch, job_preparation_calls, caplog):
        monkeypatch.delenv("ENV_NAMES", raising=False)
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", pytest.fail)
        monkeypatch.setattr(logger, "propagate", True)

        with caplog.at_level(logging.INFO, logger=logger.name):
            with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
                dispatch()
        assert job_preparation_calls == []
        assert "- FAILED" in caplog.text

    @pytest.mark.unit
    def test_starts_metrics_before_failed_preparation(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ENV_NAMES", raising=False)
        monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID", raising=False)
        monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
        monkeypatch.setenv("CI_JOB_ID", "job-123")
        monkeypatch.setenv("CI_JOB_NAME", "env-prepare")
        calls = []
        monkeypatch.setattr(
            "pipeline.metrics_collector_activity.requests.post",
            lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
        )

        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            dispatch()

        assert [event["type"] for event in calls] == ["start"]
        trace_file = tmp_path / "tmp" / ".metrics-collector-trace-id"
        assert trace_file.read_text(encoding="utf-8") == calls[0]["traceid"]
        assert (tmp_path / "tmp" / ".metrics-collector-client" / "pipeline" / "metrics_collector_cli.py").is_file()

    @pytest.mark.unit
    def test_fan_out_child_does_not_start_metrics(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("ENVGENE_FAN_OUT_CHILD", "1")
        monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
        monkeypatch.setattr("pipeline.orchestrator.run_single_env_pipeline", lambda: None)
        monkeypatch.setattr(
            "pipeline.metrics_collector_activity.requests.post",
            lambda *args, **kwargs: pytest.fail("child must not send start"),
        )

        assert dispatch() == 0
        assert not (tmp_path / "tmp" / ".metrics-collector-trace-id").exists()
