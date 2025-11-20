import difflib
import filecmp
import os
import shutil
from pathlib import Path

from envgenehelper import dump_as_yaml_format, get_all_files_in_dir, logger, openYaml, writeYamlToFile


class TestHelpers:
    
    @staticmethod
    def load_test_pipeline_sd_data(test_sd_dir, test_case_name):
        file_path = Path(test_sd_dir, test_case_name, f"{test_case_name}.yaml")
        test_data = openYaml(file_path)
        sd_data = test_data.get("SD_DATA", "{}")
        sd_source_type = test_data.get("SD_SOURCE_TYPE", "")
        sd_version = test_data.get("SD_VERSION", "")
        sd_delta = test_data.get("SD_DELTA", "")
        sd_merge_mode = test_data.get("SD_REPO_MERGE_MODE", "basic-merge")
        return sd_data, sd_source_type, sd_version, sd_delta, sd_merge_mode
    
    @staticmethod
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
            
    @staticmethod
    def assert_sd_contents(test_sd_dir, output_dir, test_case_name, actual_dir, test_suits_map):
        er_dir = test_sd_dir.joinpath("ER")

        expected_subdir = next((name for name, tests in test_suits_map.items() if test_case_name in tests), None)
        expected_dir = er_dir.joinpath(expected_subdir)
        TestHelpers.assert_dirs_content(expected_dir, actual_dir, True, True)
        TestHelpers.clean_test_dir(output_dir)

    @staticmethod
    def clean_test_dir(path: str | Path) -> Path:
        path = Path(path)
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def assert_dirs_content(source_dir, target_dir, missed_files=False, extra_files=False):
        source_map = {Path(f).name: f for f in get_all_files_in_dir(source_dir)}
        target_map = {Path(f).name: f for f in get_all_files_in_dir(target_dir)}

        source_files = set(source_map.keys())
        target_files = set(target_map.keys())

        if extra_files:
            extra_files = target_files - source_files
            assert not extra_files, f"Extra files in target: {dump_as_yaml_format([target_map[name] for name in extra_files])}"
        if missed_files:
            missing_files = source_files - target_files
            assert not missing_files, f"Missing files in target: {dump_as_yaml_format([source_map[name] for name in missing_files])}"

        files_to_compare = get_all_files_in_dir(source_dir)
        match, mismatch, errors = filecmp.cmpfiles(source_dir, target_dir, files_to_compare, shallow=False)
        logger.info(f"Match: {dump_as_yaml_format(match)}")

        if mismatch:
            for file in mismatch:
                file1 = os.path.join(source_dir, file)
                file2 = os.path.join(target_dir, file)
                with open(file1, 'r') as f1, open(file2, 'r') as f2:
                    diff = difflib.unified_diff(
                        f1.readlines(),
                        f2.readlines(),
                        fromfile=file1,
                        tofile=file2,
                        lineterm=''
                    )
                    logger.error(f"Diff for {file}:\n{''.join(diff)}")

        assert not mismatch, f"Mismatched files: {dump_as_yaml_format(mismatch)}"
        assert not errors, f"Errors: {dump_as_yaml_format(errors)}"
