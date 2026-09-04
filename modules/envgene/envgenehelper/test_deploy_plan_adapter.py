import pytest

from .deploy_plan_adapter import EnvgeneDeployPlan, adapt_sd_to_deploy_plan
from .errors import ReferenceError
from .yaml_helper import openYaml, writeYamlToFile


@pytest.fixture(autouse=True)
def env_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("FULL_ENV_NAME", "cluster-01/env-01")
    return tmp_path / "environments" / "cluster-01" / "env-01"


class TestAdaptSdToDeployPlan:
    @pytest.mark.unit
    def test_uses_namespace_map_when_available(self, env_dir):
        sd_path = env_dir / "Inventory" / "solution-descriptor" / "sd.yaml"
        writeYamlToFile(sd_path, {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]})

        deploy_plan = adapt_sd_to_deploy_plan({"bss": "dev-bss"})

        assert len(deploy_plan.entities) == 1
        entity = deploy_plan.entities[0]
        assert entity.version == "App:1.0"
        assert entity.deploy_postfix == "bss"
        assert entity.namespace == "dev-bss"

    @pytest.mark.unit
    def test_uses_selected_bgd_namespace_when_map_contains_both_sides(self, env_dir, monkeypatch):
        sd_path = env_dir / "Inventory" / "solution-descriptor" / "sd.yaml"
        writeYamlToFile(sd_path, {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]})
        monkeypatch.setenv("BG_NS_TARGET", "origin")

        deploy_plan = adapt_sd_to_deploy_plan(
            {"bss": {"origin": "dev-bss-origin", "peer": "dev-bss-peer"}}
        )

        assert deploy_plan.entities[0].namespace == "dev-bss-origin"

    @pytest.mark.unit
    def test_raises_when_deploy_postfix_not_in_namespace_map(self, env_dir):
        sd_path = env_dir / "Inventory" / "solution-descriptor" / "sd.yaml"
        writeYamlToFile(sd_path, {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]})

        with pytest.raises(ReferenceError, match="bss"):
            adapt_sd_to_deploy_plan({"other-postfix": "dev-other"})

    @pytest.mark.unit
    def test_writes_deploy_plan_to_disk(self, env_dir):
        sd_path = env_dir / "Inventory" / "solution-descriptor" / "sd.yaml"
        writeYamlToFile(sd_path, {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]})

        adapt_sd_to_deploy_plan({"bss": "dev-bss"})

        written = openYaml(EnvgeneDeployPlan.path())
        assert written == [{"version": "App:1.0", "deployPostfix": "bss", "namespace": "dev-bss",
                             "wave": 0, "generationType": "UniqForApp", "generationId": ""}]

    @pytest.mark.unit
    def test_empty_sd_produces_empty_deploy_plan(self, env_dir):
        deploy_plan = adapt_sd_to_deploy_plan({})

        assert deploy_plan.entities == []


class TestEnvgeneDeployPlanDpPath:
    @pytest.mark.unit
    def test_bare_construction_has_no_dp_path(self, env_dir):
        assert EnvgeneDeployPlan(entities=[]).dp_path is None

    @pytest.mark.unit
    def test_read_binds_dp_path_to_explicit_source(self, env_dir):
        dp_path = env_dir / "Inventory" / "delta-deploy-plan.yml"
        writeYamlToFile(dp_path, [])

        plan = EnvgeneDeployPlan.read(dp_path)

        assert plan.dp_path == dp_path

    @pytest.mark.unit
    def test_read_defaults_dp_path_to_full_path(self, env_dir):
        writeYamlToFile(EnvgeneDeployPlan.path(), [])

        plan = EnvgeneDeployPlan.read()

        assert plan.dp_path == EnvgeneDeployPlan.path()

    @pytest.mark.unit
    def test_write_binds_dp_path_to_explicit_target(self, env_dir):
        delta_path = EnvgeneDeployPlan.delta_path()
        plan = EnvgeneDeployPlan(entities=[])

        plan.write(delta_path)

        assert plan.dp_path == delta_path
        assert delta_path.is_file()

    @pytest.mark.unit
    def test_write_defaults_dp_path_to_full_path(self, env_dir):
        plan = EnvgeneDeployPlan(entities=[])

        plan.write()

        assert plan.dp_path == EnvgeneDeployPlan.path()
        assert EnvgeneDeployPlan.path().is_file()
