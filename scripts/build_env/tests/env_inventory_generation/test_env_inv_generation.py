from os import environ

import pytest
from envgenehelper import parse_env_names, get_cluster_name_from_full_name, openYaml, dumpYamlToStr, \
    get_environment_name_from_full_name

from scripts.build_env.env_inventory_generation import generate_env_new_approach
from scripts.build_env.tests.base_test import BaseTest

test_data = [
    ("cluster-01/env-01", "", "")
]


class TestEnvInvGen(BaseTest):
    @pytest.mark.parametrize("env_names, env_inventory_content_path, env_template_version", test_data)
    def test_generate_env(self, env_names, env_inventory_content_path, env_template_version):
        g_inventory_dir = self.test_data_dir / "test_inventory_generation"
        full_env_name = parse_env_names(env_names)[0]
        environ['ENV_NAME'] = get_environment_name_from_full_name(full_env_name)
        environ['CLUSTER_NAME'] = get_cluster_name_from_full_name(full_env_name)
        environ['FULL_ENV_NAME'] = full_env_name
        content = openYaml(g_inventory_dir / "input.json")
        environ['ENV_INVENTORY_CONTENT'] = dumpYamlToStr(content)
        generate_env_new_approach()
