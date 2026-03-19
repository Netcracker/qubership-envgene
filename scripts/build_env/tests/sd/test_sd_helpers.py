from pathlib import Path

from envgenehelper import openYaml, writeYamlToFile
from envgenehelper.test_helpers import TestHelpers

def load_test_pipeline_sd_data(test_sd_dir, test_case_name):
    file_path = Path(test_sd_dir, test_case_name, f"{test_case_name}.yaml")
    test_data = openYaml(file_path)
    sd_data = test_data.get("SD_DATA", "{}")
    sd_source_type = test_data.get("SD_SOURCE_TYPE", "")
    sd_version = test_data.get("SD_VERSION", "")
    sd_delta = test_data.get("SD_DELTA", "")
    sd_merge_mode = test_data.get("SD_REPO_MERGE_MODE", "basic-merge")
    return sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode

def do_prerequisites(sd, test_sd_dir, output_dir, test_case_name, env, test_suits_map):
    TestHelpers.clean_test_dir(output_dir)
    pr_dir = test_sd_dir.joinpath("prerequisites")
    target_sd_dir = Path(env.env_path, "Inventory", "solution-descriptor")

    if test_case_name in test_suits_map["replace"]:
        writeYamlToFile(target_sd_dir.joinpath(sd), "")
    elif test_case_name in test_suits_map["basic_not_first"]:
        writeYamlToFile(target_sd_dir.joinpath(sd), openYaml(pr_dir.joinpath("basic").joinpath(sd)))
    elif test_case_name in test_suits_map["exclude"]:
        writeYamlToFile(target_sd_dir.joinpath(sd), openYaml(pr_dir.joinpath("exclude").joinpath(sd)))
    elif test_case_name in test_suits_map["extended"]:
        writeYamlToFile(target_sd_dir.joinpath(sd), openYaml(pr_dir.joinpath("extended").joinpath(sd)))

def assert_sd_contents(test_sd_dir, output_dir, test_case_name, actual_dir, test_suits_map):
    er_dir = test_sd_dir.joinpath("ER")

    expected_subdir = next((name for name, tests in test_suits_map.items() if test_case_name in tests), None)
    expected_dir = er_dir.joinpath(expected_subdir)
    TestHelpers.assert_dirs_content(expected_dir, actual_dir, True, True)
    TestHelpers.clean_test_dir(output_dir)
