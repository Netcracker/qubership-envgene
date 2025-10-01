from os import environ
from pathlib import Path

import pytest
from envgenehelper import *

from main import render_environment, cleanup_resulting_dir
from test_helper import TestHelpers

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


@pytest.mark.parametrize("cluster_name, env_name, version", test_data)
def test_render_envs(cluster_name, env_name, version):
    environ['CI_PROJECT_DIR'] = g_base_dir
    render_environment(env_name, cluster_name, g_templates_dir, g_inventory_dir, g_output_dir, version, g_base_dir)
    source_dir = f"{g_inventory_dir}/{cluster_name}/{env_name}"
    generated_dir = f"{g_output_dir}/{cluster_name}/{env_name}"
    TestHelpers.assert_dirs_content(source_dir, generated_dir)


def setup_test_dir(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    dirs = ["Applications", "Namespaces", "Profiles"]
    for d in dirs:
        (tmp_path / d).mkdir(exist_ok=True)
    files = ["cloud.yml", "tenant.yml", "bg-domain.yml", "composite-structure.yml"]
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
    assert not (target_dir / "bg-domain.yml").exists()
    assert not (target_dir / "composite-structure.yml").exists()

    assert (target_dir / "keep.yml").exists()
    assert (target_dir / "keep").exists()

    delete_dir(target_dir)
