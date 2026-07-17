import pytest

from .deploy_plan_adapter import EnvgeneDeployPlan, adapt_sd_to_deploy_plan
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
    def test_falls_back_to_deploy_postfix_when_not_in_namespace_map(self, env_dir):
        sd_path = env_dir / "Inventory" / "solution-descriptor" / "sd.yaml"
        writeYamlToFile(sd_path, {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]})

        deploy_plan = adapt_sd_to_deploy_plan({})

        assert deploy_plan.entities[0].namespace == "bss"

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
