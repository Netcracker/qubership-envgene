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
    GenerateEffectiveSetStep,
    ProcessDeploymentPlanStep,
    ProcessSdStep,
    RegdefV2AdapterStep,
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
        assert ProcessDeploymentPlanStep().should_run(ctx)
        assert EnvBuildStep().should_run(ctx)
        assert not ProcessSdStep().should_run(ctx)

    @pytest.mark.unit
    def test_env_builder_legacy_flow(self):
        ctx = _ctx(ENV_BUILDER="true", SD_VERSION="Cloud-Core:1.0")

        assert AppregdefRenderStep().should_run(ctx)
        assert not DeployPostfixNamespaceMapStep().should_run(ctx)
        assert ProcessSdStep().should_run(ctx)
        assert EnvBuildStep().should_run(ctx)
        assert not ProcessDeploymentPlanStep().should_run(ctx)

    @pytest.mark.unit
    def test_legacy_sd_version_runs_appregdef_render_without_env_builder(self):
        ctx = _ctx(ENV_BUILDER="false", SD_VERSION="Cloud-Core:1.0")

        assert AppregdefRenderStep().should_run(ctx)

    @pytest.mark.unit
    @pytest.mark.parametrize("env_builder, sd_version, generate_effective_set, expected", [
        ("true", "Cloud-Core:1.0", "true", True),
        ("false", "Cloud-Core:1.0", "true", False),
        ("true", "", "true", False),
        ("true", "Cloud-Core:1.0", "false", False),
    ])
    def test_legacy_regdefv2_adapter_requires_sd_env_builder_and_effective_set(self, env_builder, sd_version,
                                                                               generate_effective_set, expected):
        ctx = _ctx(ENV_BUILDER=env_builder, SD_VERSION=sd_version,
                   GENERATE_EFFECTIVE_SET=generate_effective_set)

        assert RegdefV2AdapterStep().should_run(ctx) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("operation, bgd_operation, expected", [
        ("DEPLOY", "", True),
        ("CLEAN", "", True),
        ("BGD", "warmup", True),
        ("BGD", "promote", False),
    ])
    def test_gitlab_deploy_regdefv2_adapter_gating(self, operation, bgd_operation, expected):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, OPERATION_TYPE=operation, BGD_OPERATION=bgd_operation)

        assert RegdefV2AdapterStep().should_run(ctx) == expected

    @pytest.mark.unit
    def test_process_sd_skipped_for_gitlab_deploy_even_with_application_versions(self):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, APPLICATION_VERSIONS="Cloud-Core:1.0")

        assert not ProcessSdStep().should_run(ctx)

    @pytest.mark.unit
    def test_appregdef_render_and_env_build_run_together_for_clean(self):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, OPERATION_TYPE="CLEAN")

        assert AppregdefRenderStep().should_run(ctx)
        assert EnvBuildStep().should_run(ctx)

    @pytest.mark.unit
    def test_env_build_skipped_for_bgd(self):
        ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, OPERATION_TYPE="BGD", BGD_OPERATION="warmup")

        assert AppregdefRenderStep().should_run(ctx)
        assert not EnvBuildStep().should_run(ctx)

    @pytest.mark.unit
    def test_generate_effective_set_runs_for_deploy_clean_and_warmup(self):
        for operation, bgd_operation in (("DEPLOY", ""), ("CLEAN", ""), ("BGD", "warmup")):
            ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, OPERATION_TYPE=operation, BGD_OPERATION=bgd_operation)

            assert GenerateEffectiveSetStep().should_run(ctx)

    @pytest.mark.unit
    def test_generate_effective_set_skipped_for_other_bgd_operations(self):
        for bgd_operation in ("promote", "commit", "rollback", "init-domain"):
            ctx = _ctx(PIPELINE_TYPE=GITLAB_DEPLOY, OPERATION_TYPE="BGD", BGD_OPERATION=bgd_operation)

            assert not GenerateEffectiveSetStep().should_run(ctx)
