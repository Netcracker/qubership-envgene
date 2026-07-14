from pathlib import Path

import pytest

import envgenehelper.business_helper as business_helper
from envgenehelper.config_helper import get_envgene_config_yaml

business_helper.get_schema_dir = lambda: Path(__file__).resolve().parents[2] / "schemas"


@pytest.fixture(autouse=True)
def _reset_envgenehelper_caches():
    get_envgene_config_yaml.cache_clear()
    yield
    get_envgene_config_yaml.cache_clear()
