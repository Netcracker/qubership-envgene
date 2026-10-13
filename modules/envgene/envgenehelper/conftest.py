import pytest

from .config_helper import get_envgene_config_yaml


@pytest.fixture(autouse=True)
def _isolate_ci_project_dir(tmp_path, monkeypatch):
    # prevents tests from depending on ambient CI_PROJECT_DIR left by other test modules
    monkeypatch.setenv('CI_PROJECT_DIR', str(tmp_path))
    get_envgene_config_yaml.cache_clear()
    yield
    get_envgene_config_yaml.cache_clear()
