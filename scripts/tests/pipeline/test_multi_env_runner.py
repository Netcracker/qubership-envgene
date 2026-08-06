import os

import pytest

from pipeline.multi_env_runner import _run_child_subprocess


class TestMultiEnvChildSubprocess:
    @pytest.mark.unit
    def test_run_child_subprocess_sets_per_env_vars(self, monkeypatch, tmp_path):
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
