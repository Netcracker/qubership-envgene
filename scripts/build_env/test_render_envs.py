import difflib
import filecmp
from os import environ
from pathlib import Path

import pytest
from envgenehelper import *

from main import render_environment, cleanup_resulting_dir

test_data = [
    # (cluster_name, environment_name, template)
    ("cluster-01", "env-01", "composite-prod"),
    ("cluster-01", "env-02", "composite-dev"),
    ("cluster-01", "env-03", "composite-dev"),
    ("cluster-01", "env-04", "simple"),
    ("cluster01", "env01", "test-01"),
    ("cluster01", "env01", "test-01"),
    ("cluster01", "env03", "test-template-1"),
    ("cluster01", "env04", "test-template-2")
]

g_templates_dir = getAbsPath("../../test_data/test_templates")
g_inventory_dir = getAbsPath("../../test_data/test_environments")
g_output_dir = getAbsPath("../../tmp/test_environments")
g_base_dir = get_parent_dir_for_dir(g_inventory_dir)


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname + "/../..")


# TODO use func from test_helper during impl replacement ansible
@pytest.mark.parametrize("cluster_name, env_name, version", test_data)
def test_render_envs(cluster_name, env_name, version):
    environ['CI_PROJECT_DIR'] = g_base_dir
    render_environment(env_name, cluster_name, g_templates_dir, g_inventory_dir, g_output_dir, version, g_base_dir)
    source_dir = f"{g_inventory_dir}/{cluster_name}/{env_name}"
    generated_dir = f"{g_output_dir}/{cluster_name}/{env_name}"
    files_to_compare = get_all_files_in_dir(source_dir, source_dir + "/")
    logger.info(dump_as_yaml_format(files_to_compare))
    match, mismatch, errors = filecmp.cmpfiles(source_dir, generated_dir, files_to_compare, shallow=False)
    logger.info(f"Match: {dump_as_yaml_format(match)}")
    if len(mismatch) > 0:
        logger.error(f"Mismatch: {dump_as_yaml_format(mismatch)}")
        for file in mismatch:
            file1 = os.path.join(source_dir, file)
            file2 = os.path.join(generated_dir, file)
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


def setup_test_dir(tmp_path):
    dirs = ["Applications", "Namespaces", "Profiles"]
    for d in dirs:
        (tmp_path / d).mkdir(exist_ok=True)
    files = ["cloud.yml", "tenant.yml", "bg_domain.yml", "composite_structure.yml"]
    for f in files:
        (tmp_path / f).write_text("text")
    (tmp_path / "keep.yml").write_text("text")
    (tmp_path / "keep").mkdir(exist_ok=True)
    return tmp_path


def test_cleanup_target_dir_removes_expected_items():
    target_dir = Path(g_output_dir) / "dump-cluster"
    setup_test_dir(target_dir)
    cleanup_resulting_dir(Path(target_dir))
    assert not (target_dir / "Applications").exists()
    assert not (target_dir / "Namespaces").exists()
    assert not (target_dir / "Profiles").exists()
    assert not (target_dir / "cloud.yml").exists()
    assert not (target_dir / "tenant.yml").exists()
    assert not (target_dir / "bg_domain.yml").exists()
    assert not (target_dir / "composite_structure.yml").exists()

    assert (target_dir / "keep.yml").exists()
    assert (target_dir / "keep").exists()

    delete_dir(target_dir)
