from pathlib import Path

import pytest

from envgenehelper.config_helper import get_artifact_coordinate_source
from envgenehelper.models import ArtifactCoordinateSource

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


@pytest.mark.parametrize("config_text, expected", [
    ("crypt: false\n", ArtifactCoordinateSource.AUTO),
    ("crypt: false\nartifact_coordinate_source: auto\n", ArtifactCoordinateSource.AUTO),
    ("crypt: false\nartifact_coordinate_source: regdef\n", ArtifactCoordinateSource.REGDEF),
])
def test_artifact_coordinate_source_from_config(tmp_path, monkeypatch, config_text, expected):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "config.yml").write_text(config_text)

    assert get_artifact_coordinate_source() == expected


def test_unknown_artifact_coordinate_source_fails_config_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "config.yml").write_text("crypt: false\nartifact_coordinate_source: dd\n")

    with pytest.raises(ValueError):
        get_artifact_coordinate_source()
