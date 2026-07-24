from pathlib import Path

import pytest

from pipeline.orchestrator import dispatch
from pipeline.multi_env_runner import _child_env_for


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)


class TestChildEnvFor:
    @pytest.mark.unit
    def test_sets_env_scoped_variables(self, monkeypatch):
        monkeypatch.setenv("GLOBAL_FLAG", "keep")

        child = _child_env_for(
            "cluster-01/env-01",
            Path("/tmp/worktrees/cluster-01/env-01"),
        )

        assert child["GLOBAL_FLAG"] == "keep"
        assert child["ENV_NAMES"] == "cluster-01/env-01"
        assert child["FULL_ENV_NAME"] == "cluster-01/env-01"
        assert child["CLUSTER_NAME"] == "cluster-01"
        assert child["ENVIRONMENT_NAME"] == "env-01"
        assert child["CI_PROJECT_DIR"] == "/tmp/worktrees/cluster-01/env-01"


class TestDispatch:
    @pytest.mark.unit
    def test_single_env_runs_pipeline_in_process(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        called: list[str] = []

        monkeypatch.setattr(
            "pipeline.orchestrator.run_single_env_pipeline",
            lambda: called.append("run"),
        )

        assert dispatch() == 0
        assert called == ["run"]

    @pytest.mark.unit
    def test_multi_env_fan_out_runs_subprocess_per_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        runs: list[tuple[str, Path, Path]] = []
        copied: list[tuple[str, Path]] = []

        def fake_run_child(full_env_name, worktree_path, logs_dir):
            runs.append((full_env_name, worktree_path, logs_dir))
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
            "pipeline.orchestrator.run_single_env_pipeline",
            pytest.fail,
        )

        assert dispatch() == 0
        assert sorted(runs) == [
            (
                "cluster-01/env-01",
                tmp_path / "tmp" / "worktrees" / "cluster-01" / "env-01",
                tmp_path / "tmp" / "logs",
            ),
            (
                "cluster-02/env-02",
                tmp_path / "tmp" / "worktrees" / "cluster-02" / "env-02",
                tmp_path / "tmp" / "logs",
            ),
        ]
        assert sorted(copied) == [r[:2] for r in sorted(runs)]

    @pytest.mark.unit
    def test_multi_env_collects_failures(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        def fake_run_child(full_env_name, worktree_path, logs_dir):
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
