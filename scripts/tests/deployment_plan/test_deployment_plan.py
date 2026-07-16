from pathlib import Path

import pytest
from envgenehelper.yaml_helper import writeYamlToFile

from build_env.namespace_map import compute_namespace_map, write_namespace_map
from deployment_plan.application_entries import (
    ApplicationDeploymentEntry,
    application_entries_from_deploy_plan_entities,
)
from deployment_plan.deploy_plan_adapter import resolve_application_entries


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
    def test_prefers_deploy_plan_over_sd(self, tmp_path):
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


class TestWriteNamespaceMap:
    @pytest.mark.unit
    def test_writes_yaml_to_inventory_path(self, tmp_path):
        output_path = tmp_path / "Inventory" / "namespace-map.yml"
        write_namespace_map({"bss": "dev-bss"}, output_path)

        assert output_path.read_text().strip() == "bss: dev-bss"
