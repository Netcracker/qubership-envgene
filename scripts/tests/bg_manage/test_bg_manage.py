import json
import os
import shutil

import bg_manage.bg_manage as bg_manage
from envgenehelper.business_helper import getEnvDefinitionPath
from envgenehelper.test_helpers import TestHelpers
from envgenehelper.yaml_helper import openYaml
from scripts.tests.base_test import BaseTest

FULL_ENV_NAME = "bgd-cluster/bgd-env"
FEATURE_TEST_DIR = "test_bg_manage"

BG_STATE_TEMPLATE = {
    "controllerNamespace": "bg-controller",
    "originNamespace": {
        "name": "bgd-env-origin-app",
        "state": "active",
        "version": "v5"
    },
    "peerNamespace": {
        "name": "bgd-env-peer-app",
        "state": "candidate",
        "version": "v6"
    },
    "updateTime": "2023-07-07T10:00:54Z"
}


class TestBgManage(BaseTest):

    def setup_method(self):
        self.set_ci_project_dir(FEATURE_TEST_DIR)
        os.environ["FULL_ENV_NAME"] = FULL_ENV_NAME
        os.environ["BG_STATE"] = json.dumps(BG_STATE_TEMPLATE)
        self.test_data_path = self.test_data_dir / FEATURE_TEST_DIR
        self.env_path = self.test_data_path / "environments" / FULL_ENV_NAME
        self.origin_ns_path = self.env_path / "Namespaces" / "origin-app"
        self.peer_ns_path = self.env_path / "Namespaces" / "peer-app"

        shutil.rmtree(self.test_data_path / "environments", ignore_errors=True)
        shutil.copytree(self.test_data_path / "environments_sample", self.test_data_path / "environments")

        open(self.env_path / ".origin-active", 'w').close()
        open(self.env_path / ".peer-idle", 'w').close()

    def test_warmup_copies_active_to_candidate(self):
        extra_files, missing_files, mismatch, _ = TestHelpers.compare_dirs_content(
            self.origin_ns_path, self.peer_ns_path)
        assert extra_files and missing_files and mismatch, \
            "Namespaces don't have enough differences before the warm up operation test"

        bg_manage.run_warmup()

        expected_diff = {
            "namespace.yml": '-name: "bgd-env-origin-app"\n'
                             '+name: "bgd-env-peer-app"\n'
        }
        TestHelpers.assert_dirs_content(self.origin_ns_path, self.peer_ns_path, True, True, expected_diff)

        dotfiles = {p.name for p in self.env_path.iterdir() if p.name.startswith('.') and p.is_file()}
        assert dotfiles == {".origin-active", ".peer-idle"}

        env_definition = openYaml(getEnvDefinitionPath(self.env_path))
        bg_ns_artifacts = env_definition["envTemplate"]["bgNsArtifacts"]
        assert bg_ns_artifacts["origin"] == "bgd:v1.1.0-origin"
        assert bg_ns_artifacts["peer"] == "bgd:v1.1.0-origin"
