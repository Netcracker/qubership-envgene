import shutil

import pytest

from build_env.main import cleanup_resulting_dir, render_environment
from envgenehelper import delete_dir_if_exists, open_current_env_instance_store, render_workspace_dir
from envgenehelper.business_helper import NamespaceRole

from scripts.tests.base_test import BaseTest

CLUSTER = "cluster-01"
ENV = "env-04"


class TestBuildOverPreviousRun(BaseTest):
    @pytest.fixture(autouse=True)
    def build_setup(self, tmp_path, monkeypatch):
        shutil.copytree(self.test_data_dir / "test_environments", tmp_path / "environments")
        shutil.copytree(self.test_data_dir / "configuration", tmp_path / "configuration")
        monkeypatch.chdir(self.base_dir)
        monkeypatch.setenv("CI_COMMIT_REF_NAME", "branch_name")
        monkeypatch.setenv("FULL_ENV_NAME", f"{CLUSTER}/{ENV}")
        monkeypatch.setenv("CLUSTER_NAME", CLUSTER)
        monkeypatch.setenv("ENVIRONMENT_NAME", ENV)
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.delenv("BG_NS_TARGET", raising=False)
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")
        self.tmp_path = tmp_path
        self.templates_dirs = {NamespaceRole.COMMON: str((self.test_data_dir / "test_templates").resolve())}

    def test_build_ignores_profiles_of_previous_run(self):
        instances_dir = str(self.tmp_path / "environments")
        profiles_dir = self.tmp_path / "environments" / CLUSTER / ENV / "Profiles"
        profiles_dir.mkdir(exist_ok=True)
        stale_profile = profiles_dir / "stale_profile.yml"
        stale_profile.write_text("name: stale_profile\napplications: []\n")

        for _ in range(2):
            delete_dir_if_exists(render_workspace_dir(self.tmp_path))
            with open_current_env_instance_store(profiles_dir.parent) as env_instance_store:
                render_environment(ENV, CLUSTER, self.templates_dirs, instances_dir, self.tmp_path)
                cleanup_resulting_dir(profiles_dir.parent)
                env_instance_store.flush()

        assert (profiles_dir / "dev_billing_override.yml").is_file()
        assert not stale_profile.exists()
