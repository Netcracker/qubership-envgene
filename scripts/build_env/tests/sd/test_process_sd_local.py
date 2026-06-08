import os

import pytest
from envgenehelper import logger, SD_FILE_NAME, OperationType
from envgenehelper.env_helper import Environment

from scripts.build_env.tests.base_test import BaseTest
from test_sd_helpers import do_prerequisites, assert_sd_contents, load_test_pipeline_sd_data

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from process_sd import handle_sd

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

FEATURE_TEST_DIR = "test_handle_sd"


class TestSdProcessArtifact(BaseTest):
    def setup_method(self):
        self.env_name = "env-01"
        self.cluster = "cluster-01"
        self.full_env_name = f"{self.cluster}/{self.env_name}"

        self.set_ci_project_dir(self.output_dir / FEATURE_TEST_DIR)
        self.test_data_dir = self.test_data_dir / FEATURE_TEST_DIR
        self.output_dir = self.output_dir / FEATURE_TEST_DIR

        os.environ["FULL_ENV_NAME"] = self.full_env_name
        os.environ["ENV_NAME"] = self.env_name
        os.environ["CLUSTER_NAME"] = self.cluster

    @pytest.mark.parametrize("test_case_name", TEST_CASES_POSITIVE)
    def test_sd_positive(self, test_case_name):
        env = Environment(self.output_dir, "cluster-01", "env-01")
        do_prerequisites(SD_FILE_NAME, self.test_data_dir, self.output_dir, test_case_name, env, test_suits_map)
        logger.info(f"Starting SD test:\n\tTest case: {test_case_name}")

        sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(self.test_data_dir, test_case_name)
        handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode, OperationType.DEPLOY)

        assert_sd_contents(self.test_data_dir, env.env_path, test_case_name, test_suits_map)
        logger.info(f"=====SUCCESS - {test_case_name}======")
