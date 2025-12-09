import difflib
import filecmp
import os
import shutil
from pathlib import Path

from envgenehelper import dump_as_yaml_format, get_all_files_in_dir, logger


class TestHelpers:

    @staticmethod
    def clean_test_dir(path: str | Path) -> Path:
        path = Path(path)
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def compare_dirs_content(source_dir, target_dir) -> tuple[set[str],set[str],list,list]:
        source_map = {Path(f).name: f for f in get_all_files_in_dir(source_dir)}
        target_map = {Path(f).name: f for f in get_all_files_in_dir(target_dir)}

        source_files = set(source_map.keys())
        target_files = set(target_map.keys())

        extra_files = target_files - source_files
        missing_files = source_files - target_files

        files_to_compare = get_all_files_in_dir(source_dir)
        match, mismatch, errors = filecmp.cmpfiles(source_dir, target_dir, files_to_compare, shallow=False)
        logger.info(f"Match: {dump_as_yaml_format(match)}")

        if mismatch:
            for file in mismatch:
                file1 = os.path.join(source_dir, file)
                file2 = os.path.join(target_dir, file)
                with open(file1, 'r') as f1, open(file2, 'r') as f2:
                    diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1, tofile=file2, lineterm='')
                    logger.error(f"Diff for {file}:\n{''.join(diff)}")

        return extra_files, missing_files, mismatch, errors

    @staticmethod
    def assert_dirs_content(source_dir, target_dir, missed_files=False, extra_files=False):
        extra_files, missing_files, mismatch, errors = TestHelpers.compare_dirs_content(source_dir, target_dir)

        if extra_files:
            assert not extra_files, f"Extra files in target: {dump_as_yaml_format([target_map[name] for name in extra_files])}"
        if missed_files:
            assert not missing_files, f"Missing files in target: {dump_as_yaml_format([source_map[name] for name in missing_files])}"

        assert not mismatch, f"Mismatched files: {dump_as_yaml_format(mismatch)}"
        assert not errors, f"Errors: {dump_as_yaml_format(errors)}"

