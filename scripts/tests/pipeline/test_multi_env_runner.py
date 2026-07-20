import io
import subprocess
import sys

import pytest

from pipeline.multi_env_runner import _child_env_for, _fan_out, _run_child_subprocess, dispatch


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)


class TestChildEnvFor:
    @pytest.mark.unit
    def test_sets_env_scoped_variables(self, monkeypatch):
        monkeypatch.setenv("GLOBAL_FLAG", "keep")

        child = _child_env_for("cluster-01/env-01")

        assert child["GLOBAL_FLAG"] == "keep"
        assert child["ENV_NAMES"] == "cluster-01/env-01"
        assert child["FULL_ENV_NAME"] == "cluster-01/env-01"
        assert child["CLUSTER_NAME"] == "cluster-01"
        assert child["ENVIRONMENT_NAME"] == "env-01"


class TestRunChildSubprocess:
    @pytest.mark.unit
    def test_relays_prefixed_child_output(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr)

        class FakeStdout:
            def __init__(self):
                self._lines = iter(["child log line\n"])

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._lines)

        class FakeProc:
            stdout = FakeStdout()

            def wait(self):
                return 0

        monkeypatch.setattr(
            subprocess,
            "Popen",
            lambda *args, **kwargs: FakeProc(),
        )

        assert _run_child_subprocess("cluster-01/env-01") == 0
        assert stderr.getvalue() == "[cluster-01/env-01] child log line\n"


class TestDispatch:
    @pytest.mark.unit
    def test_single_env_runs_pipeline_in_process(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        called: list[str] = []

        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_single_env_pipeline",
            lambda: called.append("run"),
        )

        assert dispatch() == 0
        assert called == ["run"]

    @pytest.mark.unit
    def test_multi_env_fan_out_runs_subprocess_per_env(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        runs: list[str] = []

        def fake_run_child(full_env_name):
            runs.append(full_env_name)
            return 0

        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_child_subprocess",
            fake_run_child,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_single_env_pipeline",
            pytest.fail,
        )

        assert dispatch() == 0
        assert sorted(runs) == ["cluster-01/env-01", "cluster-02/env-02"]

    @pytest.mark.unit
    def test_multi_env_collects_failures(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        def fake_run_child(full_env_name):
            return 0 if full_env_name == "cluster-01/env-01" else 2

        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_child_subprocess",
            fake_run_child,
        )

        assert dispatch() == 1
