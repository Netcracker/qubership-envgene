import os

import pytest

from pipeline.pipeline_parameters import PipelineParametersHandler


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("PIPELINE_TYPE", "")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")


class TestPipelineParametersFromEnv:
    @pytest.mark.unit
    def test_populates_fields_from_env_names(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        ctx = PipelineParametersHandler.from_env()

        assert ctx.full_env_name == "cluster-01/env-01"
        assert ctx.cluster_name == "cluster-01"
        assert ctx.env_name == "env-01"
        assert os.environ["FULL_ENV_NAME"] == "cluster-01/env-01"
        assert os.environ["CLUSTER_NAME"] == "cluster-01"
        assert os.environ["ENVIRONMENT_NAME"] == "env-01"

    @pytest.mark.unit
    def test_rejects_multiple_env_names(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        with pytest.raises(ValueError, match="exactly one value"):
            PipelineParametersHandler.from_env()
