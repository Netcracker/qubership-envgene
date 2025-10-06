import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from test_helper import TestHelpers

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from handle_sd import handle_sd
from envgenehelper import *
from envgenehelper.env_helper import Environment

yaml = YAML()
TEST_CASES = [
    "TC-001-002",
    "TC-001-004",
    "TC-001-006",
    "TC-001-008",
    "TC-001-010",
    "TC-001-012",
    "TC-001-014",
    "TC-001-016",
    "TC-001-017"
]

test_suits_map = {
    "basic_not_first": ["TC-001-010", "TC-001-012"],
    "basic_first": ["TC-001-002", "TC-001-004"],
    "exclude": ["TC-001-014", "TC-001-016"],
    "extended": ["TC-001-017"],
    "replace": ["TC-001-008", "TC-001-006"]
}

TEST_SD_DIR = Path(getAbsPath("../../test_data/test_handle_sd"))
OUTPUT_DIR = getAbsPath("../../tmp/test_handle_sd")
SD = "sd.yaml"


def load_test_pipeline_sd_data(test_case_name):
    file_path = Path(TEST_SD_DIR, test_case_name, f"{test_case_name}.yaml")
    test_data = openYaml(file_path)
    sd_data = test_data.get("SD_DATA", "{}")
    sd_source_type = test_data.get("SD_SOURCE_TYPE", "")
    sd_version = test_data.get("SD_VERSION", "")
    sd_delta = test_data.get("SD_DELTA", "")
    sd_merge_mode = test_data.get("SD_REPO_MERGE_MODE", "basic-merge")
    return sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode


def do_prerequisites(test_case_name, env):
    TestHelpers.clean_test_dir(OUTPUT_DIR)
    pr_dir = TEST_SD_DIR.joinpath("prerequisites")
    target_sd_dir = Path(env.env_path, "Inventory", "solution-descriptor")

    if test_case_name in ["TC-001-006", "TC-001-008"]:
        writeYamlToFile(target_sd_dir.joinpath(SD), "")
    elif test_case_name in ["TC-001-010", "TC-001-012"]:
        writeYamlToFile(target_sd_dir.joinpath(SD), openYaml(pr_dir.joinpath("basic").joinpath(SD)))
    elif test_case_name in ["TC-001-014", "TC-001-016"]:
        writeYamlToFile(target_sd_dir.joinpath(SD), openYaml(pr_dir.joinpath("exclude").joinpath(SD)))
    elif test_case_name in ["TC-001-017"]:
        writeYamlToFile(target_sd_dir.joinpath(SD), openYaml(pr_dir.joinpath("extended").joinpath(SD)))


def do_asserts(test_case_name, actual_dir):
    er_dir = TEST_SD_DIR.joinpath("ER")

    expected_subdir = next((name for name, tests in test_suits_map.items() if test_case_name in tests), None)
    expected_dir = er_dir.joinpath(expected_subdir)
    TestHelpers.assert_dirs_content(expected_dir, actual_dir, True, True)
    TestHelpers.clean_test_dir(OUTPUT_DIR)


@pytest.mark.parametrize("test_case_name", TEST_CASES)
def test_sd(test_case_name):
    env = Environment(str(Path(OUTPUT_DIR, test_case_name)), "cluster-01", "env-01")
    do_prerequisites(test_case_name, env)
    logger.info(f"======TEST HANDLE_SD: {test_case_name}======")
    logger.info(f"Starting SD test:"
                f"\n\tTest case: {test_case_name}")

    sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(test_case_name)

    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)
    actual_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")

    do_asserts(test_case_name, actual_dir)
    logger.info(f"=====SUCCESS - {test_case_name}======")
