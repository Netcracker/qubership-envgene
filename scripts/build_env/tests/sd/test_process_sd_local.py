import os

import pytest
from ruamel.yaml import YAML

from test_sd_helpers import do_prerequisites, assert_sd_contents, load_test_pipeline_sd_data

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from process_sd import handle_sd
from envgenehelper import *
from envgenehelper.env_helper import Environment

yaml = YAML()
TEST_CASES_POSITIVE = [
    "TC-001-002",
    "TC-001-004",
    "TC-001-006",
    "TC-001-008",
    "TC-001-010",
    "TC-001-012",
    "TC-001-014",
    "TC-001-016",
    "TC-001-017",
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


@pytest.mark.parametrize("test_case_name", TEST_CASES_POSITIVE)
def test_sd_positive(test_case_name):
    env = Environment(str(Path(OUTPUT_DIR, test_case_name)), "cluster-01", "env-01")
    do_prerequisites(SD, TEST_SD_DIR, OUTPUT_DIR, test_case_name, env, test_suits_map)
    logger.info(f"======TEST HANDLE_SD_LOCAL_POSITIVE: {test_case_name}======")
    logger.info(f"Starting SD test:"
                f"\n\tTest case: {test_case_name}")

    sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(TEST_SD_DIR, test_case_name)
        
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)
    actual_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")

    assert_sd_contents(TEST_SD_DIR, OUTPUT_DIR, test_case_name, actual_dir, test_suits_map)
    logger.info(f"=====SUCCESS - {test_case_name}======")
