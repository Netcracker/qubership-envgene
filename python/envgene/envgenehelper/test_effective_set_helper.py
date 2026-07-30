import pytest
from unittest.mock import patch

from envgenehelper.effective_set_helper import get_full_generation_sd_path

@pytest.mark.unit
def test_returns_none_when_committed_sd_disabled(monkeypatch):
    monkeypatch.setattr("envgenehelper.effective_set_helper.getenv", lambda key: None,)
    monkeypatch.setattr("envgenehelper.effective_set_helper.get_envgene_config_yaml", lambda: {"use_committed_sd": False},)

    assert get_full_generation_sd_path() is None