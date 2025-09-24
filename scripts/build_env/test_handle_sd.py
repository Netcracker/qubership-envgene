import os
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
    # (cluster_name, environment_name, test_case_name)
    ("cluster01", "env02", "TC-001-002"),
    ("cluster01", "env02", "TC-001-004"),
    ("cluster01", "env01", "TC-001-006"),
    ("cluster01", "env02", "TC-001-008"),
    ("cluster01", "env02", "TC-001-010"),
    ("cluster01", "env02", "TC-001-012"),
    ("cluster01", "env02", "TC-001-014"),
    ("cluster01", "env02", "TC-001-016")
]

TEST_SD_DIR = getAbsPath("../../test_data/test_handle_sd")
ETALON_ENV_DIR = getAbsPath("../../test_data/test_environments")
OUTPUT_DIR = getAbsPath("../../tmp/test_handle_sd")


def load_test_sd_data(test_case_name):
    logger.info(f"Loading test data for case: {test_case_name}")

    # Try both yaml and yml extensions
    test_file = None
    for ext in ['yaml', 'yml']:
        file_path = os.path.join(TEST_SD_DIR, test_case_name, f"{test_case_name}.{ext}")
        if os.path.exists(file_path):
            test_file = file_path
            break

    if test_file is None:
        error_msg = f"Test case file not found for {test_case_name} in {TEST_SD_DIR}/{test_case_name}/ (tried both .yaml and .yml)"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    test_data = openYaml(test_file)

    # Extract SD parameters with defaults
    sd_data = test_data.get("SD_DATA", "{}")
    sd_source_type = test_data.get("SD_SOURCE_TYPE", "")
    sd_version = test_data.get("SD_VERSION", "")
    sd_delta = test_data.get("SD_DELTA", "")
    sd_merge_mode = test_data.get("SD_REPO_MERGE_MODE", "basic-merge")
    logger.info(f"Loaded SD parameters:"
                f"\n\tSD_SOURCE_TYPE: {sd_source_type}"
                f"\n\tSD_VERSION: {sd_version}"
                f"\n\tSD_DELTA: {sd_delta}")

    return sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode


@pytest.mark.parametrize("cluster_name, env_name, test_case_name", TEST_CASES)
def test_sd(cluster_name, env_name, test_case_name):
    logger.info(f"======TEST HANDLE_SD: {test_case_name}======")

    logger.info(f"Starting SD test:"
                f"\n\tCluster: {cluster_name}"
                f"\n\tEnvironment: {env_name}"
                f"\n\tTest case: {test_case_name}")

    # Load test data
    sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_sd_data(test_case_name)

    # Create base output directory with new structure
    base_output_path = os.path.join(OUTPUT_DIR, test_case_name)

    # Create Environment object for output
    env = Environment(base_output_path, cluster_name, env_name)

    # Source and target paths for Inventory/solution-descriptor
    source_sd_dir = os.path.join(TEST_SD_DIR, test_case_name, "Inventory", "solution-descriptor")
    target_sd_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")

    # Copy Inventory/solution-descriptor directory if it exists
    if os.path.exists(source_sd_dir):
        logger.info(f"Copying Inventory/solution-descriptor from {source_sd_dir} to {target_sd_dir}")
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(target_sd_dir), exist_ok=True)
        # Copy the entire directory
        shutil.copytree(source_sd_dir, target_sd_dir)
    else:
        # If source doesn't exist, just create the target directory
        os.makedirs(target_sd_dir, exist_ok=True)

    logger.info("Generating SD file...")
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)

    expected_dir = os.path.join(ETALON_ENV_DIR, cluster_name, env_name, "Inventory", "solution-descriptor")
    actual_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")

    TestHelpers.assert_dirs_content(expected_dir, actual_dir)
    logger.info(f"=====SUCCESS - {test_case_name}======")
