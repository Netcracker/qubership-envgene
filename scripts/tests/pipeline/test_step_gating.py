import os

os.environ.setdefault("CI_PROJECT_DIR", "/tmp")
os.environ.setdefault("ENV_NAMES", "cluster-01/env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")
os.environ.setdefault("ENVIRONMENT_NAME", "env-01")

import pytest

from envgenehelper.models import PipelineType

from pipeline.orchestrator import (
    AppregdefRenderStep,
    DeployPostfixNamespaceMapStep,
    EnvBuildStep,
    GenerateDeploymentPlanStep,
    ProcessSdStep,
)
from pipeline.pipeline_parameters import PipelineParametersHandler

GITLAB_DEPLOY = PipelineType.GITLAB_DEPLOY.value


@pytest.fixture(autouse=True)
def pipeline_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
    monkeypatch.setenv("ENV_BUILDER", "false")
    monkeypatch.setenv("GENERATE_EFFECTIVE_SET", "false")
    monkeypatch.setenv("PIPELINE_TYPE", "")
    monkeypatch.setenv("APPLICATION_VERSIONS", "")


def _ctx(**overrides) -> PipelineParametersHandler:
    for key, value in overrides.items():
        os.environ[key] = str(value).lower() if isinstance(value, bool) else str(value)
    return PipelineParametersHandler.from_env()


class TestStepGating:
    @pytest.mark.unit
    def test_gitlab_deploy_runs_appregdef_render_and_deploy_plan(self):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY)

        assert AppregdefRenderStep().should_run(ctx)
        assert DeployPostfixNamespaceMapStep().should_run(ctx)
        assert GenerateDeploymentPlanStep().should_run(ctx)
        assert EnvBuildStep().should_run(ctx)
        assert not ProcessSdStep().should_run(ctx)

    @pytest.mark.unit
    def test_env_builder_legacy_flow(self):
        ctx = _ctx(ENV_BUILDER="true", SD_VERSION="Cloud-Core:1.0")

        assert AppregdefRenderStep().should_run(ctx)
        assert not DeployPostfixNamespaceMapStep().should_run(ctx)
        assert ProcessSdStep().should_run(ctx)
        assert EnvBuildStep().should_run(ctx)
        assert not GenerateDeploymentPlanStep().should_run(ctx)

    @pytest.mark.unit
    def test_process_sd_skipped_for_gitlab_deploy_even_with_application_versions(self):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, APPLICATION_VERSIONS="Cloud-Core:1.0")

        assert not ProcessSdStep().should_run(ctx)
