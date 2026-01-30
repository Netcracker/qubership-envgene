from os import environ

import pytest
from envgenehelper import get_parent_dir_for_dir

from scripts.build_env.env_inventory_generation import generate_env_new_approach
from scripts.build_env.tests.base_test import BaseTest

test_data = [
    ("cluster-01/env-01", "", ""),
    ("cluster-01/env-02", "", ""),
    ("cluster-01/env-03", "", ""),
]


class TestEnvInvGen(BaseTest):
    @pytest.mark.parametrize("env_name, env_inventory_content_path, env_template_version", test_data)
    def test_generate_env(self, env_name, env_inventory_content_path, env_template_version):
        g_inventory_dir = get_parent_dir_for_dir(self.test_data_dir / "test_inventory_generation")
        environ['ENV_NAME'] =
        environ['CLUSTER_NAME'] =
        environ['ENV_INVENTORY_CONTENT'] =
        generate_env_new_approach()
