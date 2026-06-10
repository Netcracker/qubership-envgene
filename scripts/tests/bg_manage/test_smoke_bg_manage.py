import json
import os
import shutil

import bg_manage.bg_manage as bg_manage
from envgenehelper.test_helpers import TestHelpers
from tests.base_test import BaseTest

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
        "state": "idle",
        "version": "v6"
    },
    "updateTime": "2023-07-07T10:00:54Z"
}


class TestBgManageScript(BaseTest):

    def setup_method(self):
        self.set_ci_project_dir(FEATURE_TEST_DIR)
        os.environ["FULL_ENV_NAME"] = FULL_ENV_NAME
        self.test_data_path = self.test_data_dir / FEATURE_TEST_DIR
        self.env_path = self.test_data_path / "environments" / FULL_ENV_NAME
        self.origin_ns_path = self.env_path / "Namespaces" / "origin-app"
        self.peer_ns_path = self.env_path / "Namespaces" / "peer-app"

        shutil.rmtree(self.test_data_path / "environments", ignore_errors=True)
        shutil.copytree(self.test_data_path / "environments_sample", self.test_data_path / "environments")

        os.environ["BG_STATE"] = json.dumps(BG_STATE_TEMPLATE)

    def _set_bg_state(self, origin_state: str, peer_state: str):
        state = dict(BG_STATE_TEMPLATE)
        state["originNamespace"] = dict(BG_STATE_TEMPLATE["originNamespace"], state=origin_state)
        state["peerNamespace"] = dict(BG_STATE_TEMPLATE["peerNamespace"], state=peer_state)
        os.environ["BG_STATE"] = json.dumps(state)

    def _validate_state(self, expected_state: set):
        dotfiles = {p.name for p in self.env_path.iterdir() if p.name.startswith('.') and p.is_file()}
        assert expected_state == dotfiles

    def _run_bg_manage_check(self, origin_state: str, peer_state: str):
        self._set_bg_state(origin_state, peer_state)
        bg_manage.run_bg_manage()
        self._validate_state({f".origin-{origin_state}", f".peer-{peer_state}"})

    def test_bg_manage_script(self):
        # test init operation
        self._validate_state(set())
        self._run_bg_manage_check("active", "idle")

        # test warmup
        # verify that origin and peer have differences
        extra_files, missing_files, mismatch, _ = TestHelpers.compare_dirs_content(
            self.origin_ns_path, self.peer_ns_path)
        assert extra_files and missing_files and mismatch, \
            "Namespaces don't have enough differences before the warm up operation test"

        self._run_bg_manage_check("active", "candidate")
        # name of candidate in namespace.yml should remain unchanged after warm up and be only difference left
        expected_diff = {
            "namespace.yml": '-name: "bgd-env-origin-app"\n'
                             '+name: "bgd-env-peer-app"\n'
        }
        TestHelpers.assert_dirs_content(self.origin_ns_path, self.peer_ns_path, True, True, expected_diff)

        # test promote
        self._run_bg_manage_check("legacy", "active")

        # test commit
        self._run_bg_manage_check("idle", "active")
