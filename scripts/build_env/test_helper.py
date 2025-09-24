import difflib
import filecmp
import os

from envgenehelper import logger
from envgenehelper import dump_as_yaml_format, get_all_files_in_dir


class TestHelpers:
    @staticmethod
    def assert_dirs_content(source_dir, target_dir):
        source_files = set(get_all_files_in_dir(source_dir, source_dir + "/"))
        target_files = set(get_all_files_in_dir(target_dir, target_dir + "/"))

        extra_files = target_files - source_files
        missing_files = source_files - target_files

        if extra_files:
            logger.error(f"Extra files in target: {dump_as_yaml_format(list(extra_files))}")
        if missing_files:
            logger.error(f"Missing files in target: {dump_as_yaml_format(list(missing_files))}")

        common_files = list(source_files & target_files)
        match, mismatch, errors = filecmp.cmpfiles(source_dir, target_dir, common_files, shallow=False)

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
        assert not extra_files, f"Extra files in target: {dump_as_yaml_format(list(extra_files))}"
        assert not missing_files, f"Missing files in target: {dump_as_yaml_format(list(missing_files))}"
