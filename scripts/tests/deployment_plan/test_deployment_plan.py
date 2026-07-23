import pytest
from envgenehelper.yaml_helper import writeYamlToFile

from deployment_plan.generate_deployment_plan import _resolve_app_name, _validate_appdefs
from pipeline.pipeline_parameters import PipelineParametersHandler


class TestResolveAppName:
    @pytest.mark.unit
    def test_plain_app_version(self):
        assert _resolve_app_name("Cloud-Core:1.0") == "Cloud-Core"

    @pytest.mark.unit
    def test_namespace_app_version(self):
        application = (
            "qa-oss:resource-monitoring.fault-management:"
            "master-20260624.043628-8142"
        )
        assert _resolve_app_name(application) == "resource-monitoring.fault-management"


class TestValidateAppdefs:
    @pytest.mark.unit
    def test_accepts_namespace_app_version_when_appdef_exists(self, tmp_path):
        cluster = "saas_rnd_oss_support261_01"
        env = "qa"
        repo_appdefs = tmp_path / "appdefs"
        repo_appdefs.mkdir()
        writeYamlToFile(
            repo_appdefs / "resource-monitoring.fault-management.yml",
            {"name": "resource-monitoring.fault-management"},
        )

        ctx = PipelineParametersHandler(
            params={},
            internal_params={},
            sensitive_params=[],
            full_env_name=f"{cluster}/{env}",
            cluster_name=cluster,
            env_name=env,
            work_dir=tmp_path,
        )
        applications = [
            (
                "qa-oss:resource-monitoring.fault-management:"
                "master-20260624.043628-8142"
            ),
        ]

        _validate_appdefs(ctx, applications)

    @pytest.mark.unit
    def test_accepts_appdef_from_env_appdefs_dir(self, tmp_path):
        cluster = "cluster-01"
        env = "env-01"
        env_appdefs = tmp_path / "environments" / cluster / env / "AppDefs"
        env_appdefs.mkdir(parents=True)
        writeYamlToFile(env_appdefs / "Cloud-Core.yml", {"name": "Cloud-Core"})

        ctx = PipelineParametersHandler(
            params={},
            internal_params={},
            sensitive_params=[],
            full_env_name=f"{cluster}/{env}",
            cluster_name=cluster,
            env_name=env,
            work_dir=tmp_path,
        )

        _validate_appdefs(ctx, ["qa-core:Cloud-Core:1.0"])

    @pytest.mark.unit
    def test_rejects_namespace_app_version_when_appdef_missing(self, tmp_path):
        cluster = "saas_rnd_oss_support261_01"
        env = "qa"
        env_appdefs = tmp_path / "environments" / cluster / env / "AppDefs"
        env_appdefs.mkdir(parents=True)

        ctx = PipelineParametersHandler(
            params={},
            internal_params={},
            sensitive_params=[],
            full_env_name=f"{cluster}/{env}",
            cluster_name=cluster,
            env_name=env,
            work_dir=tmp_path,
        )
        applications = [
            (
                "qa-oss:resource-monitoring.fault-management:"
                "master-20260624.043628-8142"
            ),
        ]

        with pytest.raises(FileNotFoundError, match="resource-monitoring.fault-management"):
            _validate_appdefs(ctx, applications)
