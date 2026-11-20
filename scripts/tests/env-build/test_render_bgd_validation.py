import shutil

import pytest

from build_env.main import render_environment
from envgenehelper import open_current_env_instance_store
from envgenehelper.business_helper import NamespaceRole

from scripts.tests.base_test import BaseTest

CLUSTER = "bgd-cluster"
ENV = "bgd-env"


class TestRenderBgdValidation(BaseTest):
    @pytest.fixture(autouse=True)
    def build_setup(self, tmp_path, monkeypatch):
        shutil.copytree(self.test_data_dir / "test_environments", tmp_path / "environments")
        shutil.copytree(self.test_data_dir / "configuration", tmp_path / "configuration")
        templates_dir = tmp_path / "templates"
        shutil.copytree(self.test_data_dir / "test_templates", templates_dir)
        bg_domain_template = templates_dir / "env_templates" / "bgd" / "bg_domain.yml.j2"
        bg_domain_template.write_text(bg_domain_template.read_text().replace(
            "{{current_env.name}}-bg-controller", "{{current_env.name}}-missing-controller"))
        monkeypatch.chdir(self.base_dir)
        monkeypatch.setenv("CI_COMMIT_REF_NAME", "branch_name")
        monkeypatch.setenv("FULL_ENV_NAME", f"{CLUSTER}/{ENV}")
        monkeypatch.setenv("CLUSTER_NAME", CLUSTER)
        monkeypatch.setenv("ENVIRONMENT_NAME", ENV)
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("BG_NS_TARGET", "origin")
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")
        self.tmp_path = tmp_path
        self.templates_dirs = {NamespaceRole.COMMON: str(templates_dir)}

    def test_bg_domain_with_unknown_namespace_fails_build(self):
        instances_dir = str(self.tmp_path / "environments")

        with pytest.raises(ValueError) as exc_info:
            with open_current_env_instance_store(self.tmp_path / "environments" / CLUSTER / ENV):
                render_environment(ENV, CLUSTER, self.templates_dirs, instances_dir, self.tmp_path)

        assert any(entry.name == "validate_bgd" for entry in exc_info.traceback)
