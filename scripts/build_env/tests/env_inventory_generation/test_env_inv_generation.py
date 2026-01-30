from os import environ

import pytest
from envgenehelper import parse_env_names, get_cluster_name_from_full_name, dumpYamlToStr, \
    get_environment_name_from_full_name, readYaml

from scripts.build_env.env_inventory_generation import generate_env_new_approach, Place
from scripts.build_env.jinja.jinja import create_jinja_env
from scripts.build_env.tests.base_test import BaseTest

test_data = [
    ("cluster-01/env-01", "", "")
]


class TestEnvInvGen(BaseTest):
    @pytest.mark.parametrize("env_names, env_inventory_content_path, env_template_version", test_data)
    def test_generate_env_create(self, env_names, env_inventory_content_path, env_template_version):
        g_inventory_dir = self.test_data_dir / "test_inventory_generation"
        full_env_name = parse_env_names(env_names)[0]
        env_name = get_environment_name_from_full_name(full_env_name)
        cluster = get_cluster_name_from_full_name(full_env_name)

        environ['ENV_NAME'] = env_name
        environ['CLUSTER_NAME'] = cluster
        environ['FULL_ENV_NAME'] = full_env_name

        places = [p.value for p in Place]
        action = "create_or_replace"

        template = create_jinja_env(g_inventory_dir).get_template("input_content.yml.j2")
        content = readYaml(text=template.render(places=places, action=action, env=env_name, cluster=cluster),
                           safe_load=True)
        environ['ENV_INVENTORY_CONTENT'] = dumpYamlToStr(content)

        generate_env_new_approach()

