import difflib
import filecmp
import os

from envgenehelper import logger
from envgenehelper import dump_as_yaml_format, get_all_files_in_dir


class TestHelpers:
    @staticmethod
    def assert_dirs_content(source_dir, target_dir):
        files_to_compare = get_all_files_in_dir(source_dir, source_dir + "/")
        logger.info(dump_as_yaml_format(files_to_compare))
        match, mismatch, errors = filecmp.cmpfiles(source_dir, target_dir, files_to_compare, shallow=False)
        logger.info(f"Match: {dump_as_yaml_format(match)}")
        if len(mismatch) > 0:
            logger.error(f"Mismatch: {dump_as_yaml_format(mismatch)}")
            for file in mismatch:
                file1 = os.path.join(source_dir, file)
                file2 = os.path.join(target_dir, file)
                try:
                    with open(file1, 'r') as f1, open(file2, 'r') as f2:
                        diff = difflib.unified_diff(
                            f1.readlines(),
                            f2.readlines(),
                            fromfile=file1,
                            tofile=file2,
                            lineterm=''
                        )
                        diff_text = '\n'.join(diff)
                        logger.error(f"Diff for {file}:\n{diff_text}")
                except Exception as e:
                    logger.error(f"Could not read files for diff: {file1}, {file2}. Error: {e}")
        else:
            logger.info(f"Mismatch: {dump_as_yaml_format(mismatch)}")
        if len(errors) > 0:
            logger.fatal(f"Errors: {dump_as_yaml_format(errors)}")
        else:
            logger.info(f"Errors: {dump_as_yaml_format(errors)}")
        assert len(mismatch) == 0, f"Files from source and rendering result mismatch: {dump_as_yaml_format(mismatch)}"
        assert len(errors) == 0, f"Error during comparing source and rendering result: {dump_as_yaml_format(errors)}"
