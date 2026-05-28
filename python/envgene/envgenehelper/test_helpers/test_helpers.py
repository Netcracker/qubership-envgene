import difflib
import filecmp
import io
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from envgenehelper import dump_as_yaml_format, get_all_files_in_dir, logger
from envgenehelper.yaml_helper import writeYamlToFile


class TestHelpers:

    @staticmethod
    def clean_test_dir(path: str | Path) -> Path:
        path = Path(path)
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def compare_dirs_content(source_dir, target_dir) -> tuple[list[str], list[str], dict[str, str] | list, list]:
        source_map = {Path(f).name: f for f in get_all_files_in_dir(source_dir)}
        target_map = {Path(f).name: f for f in get_all_files_in_dir(target_dir)}

        source_files = set(source_map.keys())
        target_files = set(target_map.keys())

        extra_files = ([target_map[name] for name in target_files - source_files])
        missing_files = ([source_map[name] for name in source_files - target_files])

        files_to_compare = get_all_files_in_dir(source_dir)
        match, mismatch, errors = filecmp.cmpfiles(source_dir, target_dir, files_to_compare, shallow=False)
        logger.info(f"Match: {dump_as_yaml_format(match)}")

        if mismatch:
            mismach_dict = {}
            for file in mismatch:
                file1 = os.path.join(source_dir, file)
                file2 = os.path.join(target_dir, file)
                with open(file1, 'r') as f1, open(file2, 'r') as f2:
                    verbose_diff_list = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1,
                                                             tofile=file2, lineterm='')
                    diff_list = []
                    for line in verbose_diff_list:
                        if (line.startswith('+') and not line.startswith('+++')) or (
                                line.startswith('-') and not line.startswith('---')):
                            diff_list.append(line)
                    mismach_dict[file] = ''.join(diff_list)
                    logger.error(f"Diff for {file}:\n{''.join(verbose_diff_list)}")
            mismatch = mismach_dict

        return extra_files, missing_files, mismatch, errors

    @staticmethod
    def assert_dirs_content(source_dir, target_dir, check_for_missing_files=False, check_for_extra_files=False,
                            expected_mismatch: dict[str, str] | None = None):
        extra_files, missing_files, mismatch, errors = TestHelpers.compare_dirs_content(source_dir, target_dir)

        if check_for_extra_files:
            assert not extra_files, f"Extra files in target: {dump_as_yaml_format(extra_files)}"
        if check_for_missing_files:
            assert not missing_files, f"Missing files in target: {dump_as_yaml_format(missing_files)}"

        if expected_mismatch:
            assert expected_mismatch == mismatch, f"Mismatched files: {dump_as_yaml_format(mismatch)}\n\nExpected mismatch: {dump_as_yaml_format(expected_mismatch)}"
        else:
            assert not mismatch, f"Mismatched files: {dump_as_yaml_format(mismatch)}"

        assert not errors, f"Errors: {dump_as_yaml_format(errors)}"

    @staticmethod
    def create_fake_zip(files: dict[str, str] = None) -> bytes:
        if files is None:
            files = {"dummy.txt": "hello"}
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w") as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
        return zip_buffer.getvalue()

    @staticmethod
    def create_file(path: Path, size=1024, mtime=None):
        path.write_bytes(b"x" * size)
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    @staticmethod
    def make_sd(apps: list[dict]) -> dict:
        return {"applications": apps}

    @staticmethod
    def make_sd_app(name: str, version: str, deploy_postfix: str) -> dict[str, Any]:
        return {"version": f"{name}:{version}", "deployPostfix": deploy_postfix}

    @staticmethod
    def create_es_app_dirs(effective_set_dir: Path, deploy_postfix: str, app_name: str) -> None:
        from envgenehelper.effective_set_helper import ESGenerationContext
        for ctx in [ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            app_dir = effective_set_dir / ctx.value / deploy_postfix / app_name
            app_dir.mkdir(parents=True, exist_ok=True)
            (app_dir / "parameters.yaml").write_text("param: value")

    @staticmethod
    def create_es_cleanup_dir(effective_set_dir: Path, deploy_postfix: str) -> None:
        from envgenehelper.effective_set_helper import ESGenerationContext
        cleanup_dir = effective_set_dir / ESGenerationContext.CLEANUP.value / deploy_postfix
        cleanup_dir.mkdir(parents=True, exist_ok=True)
        (cleanup_dir / "parameters.yaml").write_text("param: value")

    @staticmethod
    def create_es_mapping(effective_set_dir: Path, ctx: Any, entries: dict) -> None:
        from envgenehelper.effective_set_helper import ES_MAPPING_FILE
        mapping_path = effective_set_dir / ctx.value / ES_MAPPING_FILE
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(mapping_path, entries)
