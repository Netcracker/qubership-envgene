from pathlib import Path

import pytest

import envgene_shared.utils.business_utils as envgene_shared_business
from envgene_shared.utils.business_utils import get_envgene_config_yaml

envgene_shared_business.get_schema_dir = lambda: Path(__file__).resolve().parents[2] / "schemas"


@pytest.fixture(autouse=True)
def _reset_envgenehelper_caches():
    get_envgene_config_yaml.cache_clear()
    yield
    get_envgene_config_yaml.cache_clear()
