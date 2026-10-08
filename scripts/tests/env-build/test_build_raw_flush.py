import os
import shutil
from unittest import mock

import pytest

import build_env.main as build_main
from pipeline.orchestrator import EnvBuildStep
from pipeline.pipeline_parameters import PipelineParametersHandler

from scripts.tests.base_test import BaseTest

CLUSTER = "cluster-01"
ENV = "env-04"


def _snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class TestBuildRawFlush(BaseTest):
    @pytest.fixture(autouse=True)
    def build_setup(self, tmp_path, monkeypatch):
        instances_dir = tmp_path / "environments"
        shutil.copytree(self.test_data_dir / "test_environments", instances_dir)
        shutil.copytree(self.test_data_dir / "test_templates", tmp_path / "tmp" / "templates")
        shutil.copytree(self.test_data_dir / "configuration", tmp_path / "configuration")
        monkeypatch.chdir(self.base_dir)
        monkeypatch.setenv("CI_COMMIT_REF_NAME", "branch_name")
        monkeypatch.setenv("ENV_NAMES", f"{CLUSTER}/{ENV}")
        monkeypatch.setenv("FULL_ENV_NAME", f"{CLUSTER}/{ENV}")
        monkeypatch.setenv("CLUSTER_NAME", CLUSTER)
        monkeypatch.setenv("ENVIRONMENT_NAME", ENV)
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("PIPELINE_TYPE", "")
        monkeypatch.delenv("BG_NS_TARGET", raising=False)
        monkeypatch.delenv("ARTIFACTS_OUTPUT_DIR", raising=False)

        def fail_midway(*args, **kwargs):
            raise RuntimeError("midway")

        monkeypatch.setattr(build_main, "create_credentials", fail_midway)
        self.instances_dir = instances_dir
        self.artifacts_dir = tmp_path / "artifacts"
        self.raw_dir = self.artifacts_dir / CLUSTER / ENV / "render"
        with mock.patch.dict(os.environ):
            yield

    def _build(self):
        before = _snapshot(self.instances_dir)
        with pytest.raises(RuntimeError):
            EnvBuildStep().execute(PipelineParametersHandler.from_env())
        assert _snapshot(self.instances_dir) == before

    def test_failure_writes_objects_as_is_to_artifacts(self, monkeypatch):
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")

        self._build()

        written = {p.relative_to(self.raw_dir).as_posix() for p in self.raw_dir.rglob("*") if p.is_file()}
        assert {"tenant.yml", "cloud.yml", "Namespaces/billing/namespace.yml"} <= written
        assert not (self.raw_dir / "Credentials").exists()
        assert not (self.raw_dir / "Inventory").exists()
        assert not (self.raw_dir / "tenant.yml").read_text().startswith("#")

    def test_failure_writes_nothing_when_strategy_is_never(self, monkeypatch):
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")

        self._build()

        assert not self.artifacts_dir.exists()
