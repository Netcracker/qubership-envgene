import os
import shutil

import pytest

from build_env.namespace_render import compute_namespace_map
from build_env.render_config_env import EnvGenerator, build_minimal_render_context
from scripts.tests.base_test import BaseTest


class TestNamespaceMap(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def setup_environments_dir(self):
        environments_dir = self.test_data_dir / "environments"
        shutil.rmtree(environments_dir, ignore_errors=True)
        shutil.copytree(self.test_data_dir / "test_environments", environments_dir)
        yield
        shutil.rmtree(environments_dir, ignore_errors=True)

    @pytest.fixture(autouse=True)
    def change_test_dir(self, monkeypatch):
        monkeypatch.chdir(self.base_dir)

    def _prepare_templates(self):
        templates_dir = str((self.test_data_dir / "test_templates").resolve())
        os.makedirs(f"{self.test_data_dir}/tmp/templates", exist_ok=True)
        if not os.path.exists(f"{self.test_data_dir}/tmp/templates/env_templates"):
            shutil.copytree(templates_dir, f"{self.test_data_dir}/tmp/templates", dirs_exist_ok=True)

    def _set_env(self, cluster_name: str, env_name: str, bg_ns_target: str | None = None) -> None:
        if bg_ns_target is None:
            os.environ.pop("BG_NS_TARGET", None)
        else:
            os.environ["BG_NS_TARGET"] = bg_ns_target
        os.environ["FULL_ENV_NAME"] = f"{cluster_name}/{env_name}"
        os.environ["CLUSTER_NAME"] = cluster_name
        os.environ["ENVIRONMENT_NAME"] = env_name
        os.environ["CI_PROJECT_DIR"] = str(self.test_data_dir)
        self._prepare_templates()

    def _render_map(self, cluster_name: str, env_name: str, bg_ns_target: str | None = None) -> dict:
        self._set_env(cluster_name, env_name, bg_ns_target)
        env_dir = f"{self.test_data_dir}/environments/{cluster_name}/{env_name}"
        context_vars = build_minimal_render_context(env_name, cluster_name, env_dir, str(self.test_data_dir))
        return EnvGenerator().render_namespaces_for_map(env_name, context_vars)

    @pytest.mark.unit
    def test_bgd_maps_both_sides_without_bg_ns_target(self):
        namespace_map = self._render_map("bgd-cluster", "bgd-env")
        assert namespace_map["app"] == {
            "origin": "bgd-env-origin-app",
            "peer": "bgd-env-peer-app",
        }

    @pytest.mark.unit
    def test_bgd_target_does_not_change_namespace_map(self):
        namespace_map = self._render_map("bgd-cluster", "bgd-env", "origin")
        assert set(namespace_map["app"]) == {"origin", "peer"}

    @pytest.mark.parametrize("operation", ["CLEAN", "DEPLOY"])
    def test_non_bgd_operations_work_without_bg_ns_target(self, operation):
        self._set_env("cluster-01", "env-01")
        os.environ["OPERATION_TYPE"] = operation

        namespace_map = self._render_map("cluster-01", "env-01")

        assert namespace_map

    @pytest.mark.unit
    def test_invalid_bg_ns_target_fails_validation(self):
        with pytest.raises(ValueError, match="BG_NS_TARGET must be 'origin' or 'peer'"):
            self._render_map("cluster-01", "env-01", "candidate")

    @pytest.mark.unit
    def test_compute_namespace_map_writes_per_side_keys(self, monkeypatch):
        self._set_env("bgd-cluster", "bgd-env")
        result = compute_namespace_map()
        assert result["app"]["origin"] == "bgd-env-origin-app"
        assert result["app"]["peer"] == "bgd-env-peer-app"
        map_file = self.test_data_dir / "environments" / "bgd-cluster" / "bgd-env" / "Inventory" / "namespace-map.yml"
        assert map_file.is_file()
