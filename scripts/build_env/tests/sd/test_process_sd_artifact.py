import os
from pathlib import Path
from unittest.mock import patch

import pytest
from envgenehelper.env_helper import Environment

from scripts.build_env.tests.base_test import BaseTest
from test_sd_helpers import do_prerequisites, assert_sd_contents, load_test_pipeline_sd_data

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from process_sd import handle_sd
from envgenehelper import SD_FILE_NAME, logger, openJson


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
    @patch("process_sd.download_sd_by_appver")
    def test_sd_positive(self, mock_download_sd, test_case_name):
        env = Environment(self.output_dir, self.cluster, self.env_name)
        do_prerequisites(SD_FILE_NAME, self.test_data_dir, self.output_dir, test_case_name, env, test_suits_map)
        logger.info(f"Starting SD test:\n\tTest case: {test_case_name}")

        sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(self.test_data_dir,
                                                                                                  test_case_name)

        file_path = Path(self.test_data_dir, test_case_name, "mock_sd.json")
        sd_data = openJson(file_path)
        mock_download_sd.return_value = sd_data

        handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)

        assert_sd_contents(self.test_data_dir, env.env_path, test_case_name, test_suits_map)
        logger.info(f"=====SUCCESS - {test_case_name}======")

    @pytest.mark.parametrize("test_case_name,expected_exception", [(k, v) for k, v in TEST_CASES_NEGATIVE.items()])
    @patch("process_sd.download_sd_by_appver")
    def test_sd_negative(self, mock_download_sd, test_case_name, expected_exception):

        env = Environment(str(Path(self.output_dir, test_case_name)), self.cluster, self.env_name)
        do_prerequisites(SD_FILE_NAME, self.test_data_dir, self.output_dir, test_case_name, env, test_suits_map)
        logger.info(f"Starting SD test:\n\tTest case: {test_case_name}")

        sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode = load_test_pipeline_sd_data(self.test_data_dir,
                                                                                                  test_case_name)

        file_path = Path(self.test_data_dir, test_case_name, "mock_sd.json")
        sd_data = openJson(file_path)
        mock_download_sd.return_value = sd_data

        with pytest.raises(expected_exception):
            handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)

        logger.info(f"=====SUCCESS - {test_case_name}======")
