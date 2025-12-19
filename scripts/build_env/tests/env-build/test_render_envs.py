from os import environ

import pytest
from envgenehelper import *

from main import render_environment, cleanup_resulting_dir
from tests.test_helpers import TestHelpers

test_data = [
    # (cluster_name, environment_name, template)
    ("cluster-01", "env-01", "composite-prod"),
    ("cluster-01", "env-02", "composite-dev"),
    ("cluster-01", "env-03", "composite-dev"),
    ("cluster-01", "env-04", "simple"),
    ("cluster01", "env01", "test-01"),
    ("cluster01", "env03", "test-template-1"),
    ("cluster01", "env04", "test-template-2"),
    ("cluster03", "rpo-replacement-mode", "simple"),
]

base_dir = Path(__file__).resolve().parents[4]
g_templates_dir = str((base_dir / "test_data/test_templates").resolve())
g_inventory_dir = str((base_dir / "test_data/test_environments").resolve())
g_output_dir = str((base_dir / "/tmp/test_environments").resolve())
g_base_dir = get_parent_dir_for_dir(g_inventory_dir)
environ['CI_PROJECT_DIR'] = g_base_dir
os.environ['CI_COMMIT_REF_NAME'] = "branch_name"


@pytest.fixture(autouse=True)
def change_test_dir(monkeypatch):
    monkeypatch.chdir(base_dir)


@pytest.mark.parametrize("cluster_name, env_name, version", test_data)
def test_render_envs(cluster_name, env_name, version):
    render_environment(env_name, cluster_name, g_templates_dir, g_inventory_dir, g_output_dir, version, g_base_dir)
    source_dir = f"{g_inventory_dir}/{cluster_name}/{env_name}"
    generated_dir = f"{g_output_dir}/{cluster_name}/{env_name}"
    files_to_compare = get_all_files_in_dir(source_dir)
    logger.info(dump_as_yaml_format(files_to_compare))
    TestHelpers.assert_dirs_content(source_dir, generated_dir, True, False)


def setup_test_dir(tmp_path):
    tmp_path.mkdir(exist_ok=True)
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
