from os import environ
from pathlib import Path

from envgenehelper import get_cluster_name_from_full_name, dumpYamlToStr, get_environment_name_from_full_name, readYaml, \
    cleanup_dir

from env_inventory_generation import generate_env_new_approach, Place, resolve_path, INVENTORY

from jinja.jinja import create_jinja_env
from tests.base_test import BaseTest

FEATURE_TEST_DIR = "test_inventory_generation"


def _assert_item(env_dir, item, subdir, inventory=""):
    place = Place(item["place"])
    name = item["content"]["name"]
    path = resolve_path(env_dir, place, subdir, name, inventory)
    assert path.exists(), path
    actual = readYaml(path, safe_load=True)
    expected = item["content"]
    assert actual == expected


class TestEnvInvGen(BaseTest):

    def test_generate_env_create(self):

        self.set_project_dir(FEATURE_TEST_DIR, "output")
        cleanup_dir(self.ci_project_dir)

        full_env_name = "cluster-01/env-01"

        env_name = get_environment_name_from_full_name(full_env_name)
        cluster = get_cluster_name_from_full_name(full_env_name)

        environ["ENV_NAME"] = env_name
        environ["CLUSTER_NAME"] = cluster
        environ["FULL_ENV_NAME"] = full_env_name

        places = [p.value for p in Place]
        action = "create_or_replace"
        template = create_jinja_env(self.test_data_dir / FEATURE_TEST_DIR / "input").get_template("content.yml.j2")
        content = readYaml(text=template.render(places=places, action=action, env=env_name, cluster=cluster),
                           safe_load=True)
        environ["ENV_INVENTORY_CONTENT"] = dumpYamlToStr(content)

        generate_env_new_approach()

        env_dir = Path(self.ci_project_dir) / "environments" / full_env_name
        for item in content.get("paramSets", []):
            _assert_item(env_dir, item, "parameters", INVENTORY)
        for item in content.get("credentials", []):
            _assert_item(env_dir, item, "credentials", INVENTORY)
        for item in content.get("resourceProfiles", []):
            _assert_item(env_dir, item, "resource_profiles", INVENTORY)
        for item in content.get("sharedTemplateVariables", []):
            _assert_item(env_dir, item, "shared-template-variables")
