import os
import json
import shutil
from pathlib import Path

from envgenehelper.test_helpers import TestHelpers
import bg_manage

os.environ["FULL_ENV_NAME"] = "etbss-ocp-01/env-amber"
TEST_DATA_PATH = Path(f"{os.getenv('CI_PROJECT_DIR')}/test_data/test_bg_manage")
TEST_DATA_ENV_PATH = TEST_DATA_PATH.joinpath('environments',os.getenv("FULL_ENV_NAME", ""))
TEST_DATA_NAMESPACES_PATH = TEST_DATA_ENV_PATH.joinpath('Namespaces')
ORIGIN_NS_PATH = TEST_DATA_ENV_PATH.joinpath('Namespaces','bss')
PEER_NS_PATH = TEST_DATA_ENV_PATH.joinpath('Namespaces','core')

os.environ["CI_PROJECT_DIR"] = str(TEST_DATA_PATH)
os.environ["BG_STATE"] = """
{
  "controllerNamespace": "devops-apps-test-1-bg-controller",
  "originNamespace": {
    "name": "env-amber-bss",
    "state": "active",
    "version": "v5"
  },
  "peerNamespace": {
    "name": "env-amber-core",
    "state": "idle",
    "version": "v6"
  },
  "updateTime": "2023-07-07T10:00:54Z"
}
"""
bg_manage.ENV_PATH = str(TEST_DATA_ENV_PATH)
bg_manage.NAMESPACES_PATH = str(TEST_DATA_NAMESPACES_PATH)
bg_manage.BG_STATE = json.loads(os.getenv("BG_STATE"))

def validate_state(expected_state: set[str]):
    env_path_dotfiles = {p.name for p in Path(TEST_DATA_ENV_PATH).iterdir() if p.name.startswith('.') and p.is_file()}
    assert expected_state == env_path_dotfiles

def run_bg_manage_check(origin_state: str, peer_state: str):
    bg_manage.BG_STATE["originNamespace"]["state"] = origin_state
    bg_manage.BG_STATE["peerNamespace"]["state"] = peer_state
    bg_manage.run_bg_manage()
    validate_state({f".origin-{origin_state}",f".peer-{peer_state}"})

def test_bg_manage_script():
    shutil.rmtree(f"{TEST_DATA_PATH}/environments", ignore_errors=True)
    shutil.copytree(f"{TEST_DATA_PATH}/environments_sample", f"{TEST_DATA_PATH}/environments")

    # test init operation
    validate_state(set())
    run_bg_manage_check("active","idle")

    # test warmup
    # verify that origin and peer have differences
    extra_files, missing_files, mismatch, _ = TestHelpers.compare_dirs_content(ORIGIN_NS_PATH, PEER_NS_PATH)
    assert extra_files and missing_files and mismatch, "Namespaces don't have enough differences before the warm up operation test"

    run_bg_manage_check("active","candidate")
    # name of candidate in namespace.yml should remain unchanged after warm up and be only difference left
    expected_diff = {
        "namespace.yml": '-name: "env-amber-bss"\n'
                         '+name: "env-amber-core"\n'
    }
    TestHelpers.assert_dirs_content(ORIGIN_NS_PATH, PEER_NS_PATH, True, True, expected_diff)

    # test promote
    run_bg_manage_check("legacy","active")

    # test commit
    run_bg_manage_check("idle", "active")
