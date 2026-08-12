from os import environ

import pytest

from build_env.main import render_environment
from envgenehelper import *
from envgene_shared import *
from envgenehelper.business_helper import NamespaceRole
from envgenehelper.test_helpers import TestHelpers

from scripts.tests.base_test import BaseTest

test_data = [
    # (cluster_name, environment_name, template)
    ("cluster-01", "env-01", "composite-prod", {}),
    ("cluster-01", "env-02", "composite-dev", {}),
    ("cluster-01", "env-03", "composite-dev", {}),
    ("cluster-01", "env-04", "simple", {}),
    ("cluster01", "env01", "test-01", {}),
    ("cluster01", "env03", "test-template-1", {}),
    ("cluster01", "env04", "test-template-2", {}),
    ("bgd-cluster", "bgd-env", "bgd", {}),
    ("bgd-cluster", "bgd-ns-artifacts-env", "bgd-ns-artifacts", {NamespaceRole.PEER: "test_data/test_templates_peer", NamespaceRole.ORIGIN: "test_data/test_templates_origin"}),
    ("cluster03", "rpo-replacement-mode", "simple", {}),
    ("cluster-01", "env-extcred", "extcred-template", {}),
]


class TestEnvBuild(BaseTest):
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

    @pytest.mark.parametrize("cluster_name, env_name, version, extra_templates", test_data)
    def test_render_envs(self, cluster_name, env_name, version, extra_templates):
        g_templates_dirs = {
            NamespaceRole.COMMON: str((self.test_data_dir / "test_templates").resolve())
        }
        g_templates_dirs.update(extra_templates)

        g_inventory_dir = str((self.test_data_dir / "test_environments").resolve())
        g_output_dir = str((self.base_dir / "/tmp/test_environments").resolve())

        os.environ['CI_COMMIT_REF_NAME'] = "branch_name"
        environ['FULL_ENV_NAME'] = cluster_name + '/' + env_name
        environ['CLUSTER_NAME'] = cluster_name
        environ['ENVIRONMENT_NAME'] = env_name
        environ['CI_PROJECT_DIR'] = str(self.test_data_dir)

        if version in ("bgd", "bgd-ns-artifacts"):
            os.environ["BG_NS_TARGET"] = "origin"
        else:
            os.environ.pop("BG_NS_TARGET", None)

        render_environment(env_name, cluster_name, g_templates_dirs, g_inventory_dir, g_output_dir, self.test_data_dir)
        source_dir = f"{g_inventory_dir}/{cluster_name}/{env_name}"
        generated_dir = f"{g_output_dir}/{cluster_name}/{env_name}"
        files_to_compare = get_all_files_in_dir(source_dir)
        logger.info(dump_as_yaml_format(files_to_compare))
        TestHelpers.assert_dirs_content(source_dir, generated_dir, True, False)

