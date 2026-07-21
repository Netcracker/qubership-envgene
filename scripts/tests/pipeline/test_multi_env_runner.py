import io
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.multi_env_runner import (
    _child_env_for,
    _fan_out,
    _run_child_subprocess,
    dispatch,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)


class TestChildEnvFor:
    @pytest.mark.unit
    def test_sets_env_scoped_variables(self, monkeypatch):
        monkeypatch.setenv("GLOBAL_FLAG", "keep")

        child = _child_env_for("cluster-01/env-01", Path("/tmp/worktrees/cluster-01/env-01"))

        assert child["GLOBAL_FLAG"] == "keep"
        assert child["ENV_NAMES"] == "cluster-01/env-01"
        assert child["FULL_ENV_NAME"] == "cluster-01/env-01"
        assert child["CLUSTER_NAME"] == "cluster-01"
        assert child["ENVIRONMENT_NAME"] == "env-01"
        assert child["CI_PROJECT_DIR"] == "/tmp/worktrees/cluster-01/env-01"
        assert child["ENVGENE_WORKTREE"] == "1"


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

        assert _run_child_subprocess("cluster-01/env-01", Path("/tmp/worktrees/cluster-01/env-01")) == 0
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
    def test_multi_env_fan_out_runs_subprocess_per_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        runs: list[tuple[str, Path]] = []
        copied: list[tuple[str, Path]] = []

        def fake_run_child(full_env_name, worktree_path):
            runs.append((full_env_name, worktree_path))
            return 0

        monkeypatch.setattr(
            "pipeline.multi_env_runner._create_worktree",
            lambda base, path, sha: None,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._remove_worktree",
            lambda base, path: None,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._copy_worktree_outputs",
            lambda path, main, env: copied.append((env, path)),
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_child_subprocess",
            fake_run_child,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_single_env_pipeline",
            pytest.fail,
        )

        assert dispatch() == 0
        assert sorted(runs) == [
            ("cluster-01/env-01", tmp_path / "tmp" / "worktrees" / "cluster-01" / "env-01"),
            ("cluster-02/env-02", tmp_path / "tmp" / "worktrees" / "cluster-02" / "env-02"),
        ]
        assert sorted(copied) == sorted(runs)

    @pytest.mark.unit
    def test_multi_env_collects_failures(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        def fake_run_child(full_env_name, worktree_path):
            return 0 if full_env_name == "cluster-01/env-01" else 2

        monkeypatch.setattr(
            "pipeline.multi_env_runner._create_worktree",
            lambda base, path, sha: None,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._remove_worktree",
            lambda base, path: None,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._copy_worktree_outputs",
            lambda path, main, env: None,
        )
        monkeypatch.setattr(
            "pipeline.multi_env_runner._run_child_subprocess",
            fake_run_child,
        )

        assert dispatch() == 1
