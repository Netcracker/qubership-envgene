from os import environ, getenv
from pathlib import Path

import pytest
from env_inventory_generation import generate_env_new_approach, Place, resolve_path, INVENTORY, Action
from envgenehelper import get_cluster_name_from_full_name, dumpYamlToStr, get_environment_name_from_full_name, readYaml, \
    cleanup_dir, is_dir_empty
from jinja.jinja import create_jinja_env
from tests.base_test import BaseTest

FEATURE_TEST_DIR = "test_inventory_generation"


def _assert_item(env_dir, item, subdir, inventory=""):
    place = Place(item["place"])
    content = item["content"]
    name = content.get("name") or item["name"]
    path = resolve_path(env_dir, place, subdir, name, inventory)
    assert path.exists(), path
    actual = readYaml(path, safe_load=True)
    assert actual == content


class TestEnvInvGen(BaseTest):
    full_env_name = "cluster-01/env-01"
    env_dir = ""
    site_dir = ""
    cluster_dir = ""
    action: Action = None

    def setup_method(self):
        self.set_project_dir(FEATURE_TEST_DIR, "output")
        cleanup_dir(self.ci_project_dir)

        self.env_name = get_environment_name_from_full_name(self.full_env_name)
        self.cluster = get_cluster_name_from_full_name(self.full_env_name)

        environ["ENV_NAME"] = self.env_name
        environ["CLUSTER_NAME"] = self.cluster
        environ["FULL_ENV_NAME"] = self.full_env_name

        site = Path(self.ci_project_dir) / "environments"
        self.site_dir = site
        self.cluster_dir = self.site_dir / self.cluster
        self.env_dir = site / self.full_env_name

    def set_inv_content(self):
        places = [p.value for p in Place]
        template = create_jinja_env(self.test_data_dir / FEATURE_TEST_DIR / "input").get_template("content.yml.j2")
        content = readYaml(
            text=template.render(places=places, action=self.action.value, env=self.env_name, cluster=self.cluster),
            safe_load=True)
        environ["ENV_INVENTORY_CONTENT"] = dumpYamlToStr(content)

    def test_resolve_path(self):
        env_dir = Path("/repo/environments/cluster-01/env-01")
        cases = [
            (Place.ENV, "parameters", INVENTORY, "ps1",
             "/repo/environments/cluster-01/env-01/Inventory/parameters/ps1.yml"),
            (Place.CLUSTER, "parameters", INVENTORY, "ps1", "/repo/environments/cluster-01/parameters/ps1.yml"),
            (Place.SITE, "parameters", INVENTORY, "ps1", "/repo/environments/parameters/ps1.yml"),
            (Place.ENV, "credentials", INVENTORY, "cred1",
             "/repo/environments/cluster-01/env-01/Inventory/credentials/cred1.yml"),
            (Place.CLUSTER, "credentials", INVENTORY, "cred1", "/repo/environments/cluster-01/credentials/cred1.yml"),
            (Place.SITE, "credentials", INVENTORY, "cred1", "/repo/environments/credentials/cred1.yml"),
            (Place.ENV, "resource_profiles", INVENTORY, "rp1",
             "/repo/environments/cluster-01/env-01/Inventory/resource_profiles/rp1.yml"),
            (Place.CLUSTER, "resource_profiles", INVENTORY, "rp1",
             "/repo/environments/cluster-01/resource_profiles/rp1.yml"),
            (Place.SITE, "resource_profiles", INVENTORY, "rp1", "/repo/environments/resource_profiles/rp1.yml"),
            (Place.ENV, "shared-template-variables", "", "stv1",
             "/repo/environments/cluster-01/env-01/shared-template-variables/stv1.yml"),
            (Place.CLUSTER, "shared-template-variables", "", "stv1",
             "/repo/environments/cluster-01/shared-template-variables/stv1.yml"),
            (Place.SITE, "shared-template-variables", "", "stv1",
             "/repo/environments/shared-template-variables/stv1.yml"),
        ]
        for place, subdir, inventory, name, expected in cases:
            result_path = resolve_path(env_dir, place, subdir, name, inventory)
            assert result_path == Path(expected)

    def test_gen_env_create_delete(self):
        self.action = Action.CREATE_OR_REPLACE
        self.set_inv_content()
        content = readYaml(getenv('ENV_INVENTORY_CONTENT'), safe_load=True)

        generate_env_new_approach()

        for item in content.get("paramSets", []):
            _assert_item(self.env_dir, item, "parameters", INVENTORY)
        for item in content.get("credentials", []):
            _assert_item(self.env_dir, item, "credentials", INVENTORY)
        for item in content.get("resourceProfiles", []):
            _assert_item(self.env_dir, item, "resource_profiles", INVENTORY)
        for item in content.get("sharedTemplateVariables", []):
            _assert_item(self.env_dir, item, "shared-template-variables")

        self.action = Action.DELETE
        self.set_inv_content()

        generate_env_new_approach()

        assert self.site_dir.exists()
        assert is_dir_empty(self.site_dir / "parameters")
        assert is_dir_empty(self.site_dir / "credentials")
        assert is_dir_empty(self.site_dir / "resource_profiles")
        assert is_dir_empty(self.site_dir / "shared-template-variables")

        assert self.cluster_dir.exists()
        assert is_dir_empty(self.cluster_dir / "parameters")
        assert is_dir_empty(self.cluster_dir / "credentials")
        assert is_dir_empty(self.cluster_dir / "resource_profiles")
        assert is_dir_empty(self.cluster_dir / "shared-template-variables")

        assert not self.env_dir.exists()

    @pytest.mark.skip
    def test_env_template_version(self):
        self.action = Action.CREATE_OR_REPLACE
        self.set_inv_content()
        updated_version = "template:v0.0.0"
        environ["ENV_TEMPLATE_VERSION"] = updated_version

        generate_env_new_approach()

        inventory_path = Path(
            self.ci_project_dir) / "environments" / self.full_env_name / INVENTORY / "env_definition.yml"
        inventory = readYaml(inventory_path, safe_load=True)
        assert inventory["envTemplate"]["artifact"] == updated_version
