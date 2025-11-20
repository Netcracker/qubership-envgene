import os

import pytest
from unittest.mock import patch
from ruamel.yaml import YAML

from test_sd_helpers import do_prerequisites, assert_sd_contents, load_test_pipeline_sd_data

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from handle_sd import handle_sd
from envgenehelper import *
from envgenehelper.env_helper import Environment

yaml = YAML()

TEST_CASES_POSITIVE = [
    "TC-001-098",
]

TEST_CASES_NEGATIVE = {
    "TC-001-099": ValueError,
}

test_suits_map = {
    "basic_not_first": [],
    "basic_first": [],
    "exclude": [],
    "extended": ["TC-001-098", "TC-001-099"],
    "replace": []
}

TEST_SD_DIR = Path(getAbsPath("../../test_data/test_handle_sd"))
OUTPUT_DIR = getAbsPath("../../tmp/test_handle_sd")
SD = "sd.yaml"


@pytest.mark.parametrize("test_case_name", TEST_CASES_POSITIVE)
@patch("handle_sd.download_sd_by_appver")
def test_sd_positive(mock_download_sd, test_case_name):
    env = Environment(str(Path(OUTPUT_DIR, test_case_name)), "cluster-01", "env-01")
    do_prerequisites(SD, TEST_SD_DIR, OUTPUT_DIR, test_case_name, env, test_suits_map)
    logger.info(f"======TEST HANDLE_SD_ARTIFACT_POSITIVE: {test_case_name}======")
    logger.info(f"Starting SD test:"
                f"\n\tTest case: {test_case_name}")

    sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(TEST_SD_DIR, test_case_name)

    file_path = Path(TEST_SD_DIR, test_case_name, f"mock_sd.json")
    sd_data = openJson(file_path)
    mock_download_sd.return_value = sd_data
        
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)
    actual_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")

    assert_sd_contents(TEST_SD_DIR, OUTPUT_DIR, test_case_name, actual_dir, test_suits_map)
    logger.info(f"=====SUCCESS - {test_case_name}======")
    
    
@pytest.mark.parametrize("test_case_name,expected_exception", [(k, v) for k, v in TEST_CASES_NEGATIVE.items()])
@patch("handle_sd.download_sd_by_appver")
def test_sd_negative(mock_download_sd, test_case_name, expected_exception):
    env = Environment(str(Path(OUTPUT_DIR, test_case_name)), "cluster-01", "env-01")
    do_prerequisites(SD, TEST_SD_DIR, OUTPUT_DIR, test_case_name, env, test_suits_map)
    logger.info(f"======TEST HANDLE_SD_ARTIFACT_NEGATIVE: {test_case_name}======")
    logger.info(f"Starting SD test:"
                f"\n\tTest case: {test_case_name}")

    sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(TEST_SD_DIR, test_case_name)

    file_path = Path(TEST_SD_DIR, test_case_name, f"mock_sd.json")
    sd_data = openJson(file_path)
    mock_download_sd.return_value = sd_data
    
    with pytest.raises(expected_exception):
        handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)

    logger.info(f"=====SUCCESS - {test_case_name}======")
