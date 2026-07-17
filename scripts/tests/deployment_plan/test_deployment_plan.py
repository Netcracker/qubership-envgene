from pathlib import Path

import pytest
from envgenehelper.yaml_helper import writeYamlToFile

from build_env.namespace_map import compute_namespace_map, write_namespace_map
from deployment_plan.generate_deployment_plan import _resolve_app_name, _validate_appdefs
from deployment_plan.deploy_plan_adapter import (
    ApplicationDeploymentEntry,
    application_entries_from_deploy_plan_entities,
    resolve_application_entries,
    resolve_application_source_paths,
)
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


class TestComputeNamespaceMap:
    @pytest.mark.unit
    def test_maps_folder_names_to_namespace_names(self, tmp_path):
        namespaces_dir = tmp_path / "Namespaces"
        bss_dir = namespaces_dir / "bss"
        bss_dir.mkdir(parents=True)
        writeYamlToFile(bss_dir / "namespace.yml", {"name": "dev-bss"})

        assert compute_namespace_map(namespaces_dir) == {"bss": "dev-bss"}

    @pytest.mark.unit
    def test_fails_when_namespaces_dir_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            compute_namespace_map(tmp_path / "Namespaces")


class TestApplicationEntries:
    @pytest.mark.unit
    def test_maps_deploy_plan_entities(self):
        entities = [
            {"wave": 0, "version": "Cloud-Core:1.0", "deployPostfix": "core", "namespace": "dev-core"},
        ]

        assert application_entries_from_deploy_plan_entities(entities) == [
            ApplicationDeploymentEntry(version="Cloud-Core:1.0", deploy_postfix="core", namespace="dev-core"),
        ]


class TestResolveApplicationEntries:
    @pytest.mark.unit
    def test_prefers_deploy_plan_over_sd_on_legacy_flow(self, tmp_path):
        env_dir = tmp_path / "cluster" / "env"
        inventory = env_dir / "Inventory"
        inventory.mkdir(parents=True)
        writeYamlToFile(
            inventory / "deploy-plan.yml",
            [{"wave": 0, "version": "App:1.0", "deployPostfix": "bss", "namespace": "dev-bss"}],
        )
        writeYamlToFile(
            inventory / "solution-descriptor" / "sd.yml",
            {"applications": [{"version": "Other:2.0", "deployPostfix": "other"}]},
        )

        entries = resolve_application_entries(env_dir, env_dir)

        assert entries == [
            ApplicationDeploymentEntry(version="App:1.0", deploy_postfix="bss", namespace="dev-bss"),
        ]

    @pytest.mark.unit
    def test_falls_back_to_sd_when_deploy_plan_missing(self, tmp_path):
        env_dir = tmp_path / "cluster" / "env"
        sd_dir = env_dir / "Inventory" / "solution-descriptor"
        sd_dir.mkdir(parents=True)
        writeYamlToFile(
            sd_dir / "sd.yml",
            {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]},
        )

        entries = resolve_application_entries(env_dir, env_dir)

        assert entries == [ApplicationDeploymentEntry(version="App:1.0", deploy_postfix="bss")]

    @pytest.mark.unit
    def test_gitlab_deploy_requires_deploy_plan(self, tmp_path):
        env_dir = tmp_path / "cluster" / "env"
        sd_dir = env_dir / "Inventory" / "solution-descriptor"
        sd_dir.mkdir(parents=True)
        writeYamlToFile(
            sd_dir / "sd.yml",
            {"applications": [{"version": "App:1.0", "deployPostfix": "bss"}]},
        )

        with pytest.raises(FileNotFoundError):
            resolve_application_entries(env_dir, env_dir, gitlab_deploy=True)


class TestResolveApplicationSourcePaths:
    @pytest.mark.unit
    def test_gitlab_deploy_requires_deploy_plan(self, tmp_path):
        inventory = tmp_path / "Inventory"
        inventory.mkdir(parents=True)

        with pytest.raises(FileNotFoundError):
            resolve_application_source_paths(inventory, gitlab_deploy=True)

    @pytest.mark.unit
    def test_gitlab_deploy_returns_deploy_plan_path(self, tmp_path):
        inventory = tmp_path / "Inventory"
        inventory.mkdir(parents=True)
        deploy_plan_path = inventory / "deploy-plan.yml"
        writeYamlToFile(
            deploy_plan_path,
            [{"wave": 0, "version": "App:1.0", "deployPostfix": "bss"}],
        )

        assert resolve_application_source_paths(inventory, gitlab_deploy=True) == (None, deploy_plan_path)

    @pytest.mark.unit
    def test_legacy_flow_uses_sd_when_deploy_plan_missing(self, tmp_path):
        inventory = tmp_path / "Inventory"
        sd_dir = inventory / "solution-descriptor"
        sd_dir.mkdir(parents=True)
        sd_path = sd_dir / "sd.yml"
        writeYamlToFile(sd_path, {"applications": []})

        assert resolve_application_source_paths(inventory, sd_path=sd_path) == (sd_path, None)


class TestWriteNamespaceMap:
    @pytest.mark.unit
    def test_writes_yaml_to_inventory_path(self, tmp_path):
        output_path = tmp_path / "Inventory" / "namespace-map.yml"
        write_namespace_map({"bss": "dev-bss"}, output_path)

        assert output_path.read_text().strip() == "bss: dev-bss"
