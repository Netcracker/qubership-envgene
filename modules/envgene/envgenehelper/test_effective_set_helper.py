import pytest

from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan
from envgenehelper.effective_set_helper import apply_no_sd_mode


class FakeCtx:
    def __init__(self, deploy_plan_entities):
        self.deploy_plan = EnvgeneDeployPlan(entities=deploy_plan_entities)


@pytest.fixture(autouse=True)
def clear_sd_env(monkeypatch):
    monkeypatch.delenv("SD_DATA", raising=False)
    monkeypatch.delenv("SD_VERSION", raising=False)
    monkeypatch.delenv("APPLICATION_VERSIONS", raising=False)


class TestApplyNoSdMode:
    @pytest.mark.unit
    def test_clears_deploy_plan_when_no_sd_input_and_committed_sd_disabled(self, monkeypatch):
        monkeypatch.setattr("envgenehelper.effective_set_helper.get_envgene_config_yaml",
                             lambda: {"use_committed_sd": False})
        entity = DeployPlanEntity(version="app:1.0", deployPostfix="ns-1", namespace="ns-1")
        ctx = FakeCtx([entity])

        apply_no_sd_mode(ctx)

        assert ctx.deploy_plan.entities == []

    @pytest.mark.unit
    def test_keeps_deploy_plan_when_committed_sd_enabled(self, monkeypatch):
        monkeypatch.setattr("envgenehelper.effective_set_helper.get_envgene_config_yaml",
                             lambda: {"use_committed_sd": True})
        entity = DeployPlanEntity(version="app:1.0", deployPostfix="ns-1", namespace="ns-1")
        ctx = FakeCtx([entity])

        apply_no_sd_mode(ctx)

        assert ctx.deploy_plan.entities == [entity]

    @pytest.mark.unit
    def test_keeps_deploy_plan_when_sd_data_present(self, monkeypatch):
        monkeypatch.setattr("envgenehelper.effective_set_helper.get_envgene_config_yaml",
                             lambda: {"use_committed_sd": False})
        monkeypatch.setenv("SD_DATA", "some-sd-payload")
        entity = DeployPlanEntity(version="app:1.0", deployPostfix="ns-1", namespace="ns-1")
        ctx = FakeCtx([entity])

        apply_no_sd_mode(ctx)

        assert ctx.deploy_plan.entities == [entity]

    @pytest.mark.unit
    def test_keeps_deploy_plan_when_application_versions_present(self, monkeypatch):
        monkeypatch.setattr("envgenehelper.effective_set_helper.get_envgene_config_yaml",
                             lambda: {"use_committed_sd": False})
        monkeypatch.setenv("APPLICATION_VERSIONS", "app:1.0")
        entity = DeployPlanEntity(version="app:1.0", deployPostfix="ns-1", namespace="ns-1")
        ctx = FakeCtx([entity])

        apply_no_sd_mode(ctx)

        assert ctx.deploy_plan.entities == [entity]
