import json
from pathlib import Path

import pytest

from envgenehelper import get_schema
from envgenehelper.config_helper import get_artifact_coordinate_source, get_sbom_cache_enabled
from envgenehelper.models import ArtifactCoordinateSource

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


@pytest.mark.unit
def test_regdef_schemas_load_from_configured_root_schema_directory(monkeypatch):
    schemas_dir = Path(__file__).resolve().parents[3] / "schemas"
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schemas_dir))

    assert get_schema("regdef.schema.json")["properties"]["credentialsId"]["type"] == "string"
    assert get_schema("regdef-v2.schema.json")["properties"]["authConfig"]["type"] == "object"
    for schema_path in schemas_dir.glob("*.schema.json"):
        assert get_schema(schema_path.name) == json.loads(schema_path.read_text())


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


@pytest.mark.parametrize("config_text, expected", [
    ("crypt: false\n", True),
    ("sbom_cache: {}\n", True),
    ("sbom_cache:\n  enabled: true\n", True),
    ("sbom_cache:\n  enabled: false\n", False),
])
def test_sbom_cache_enabled_from_config(tmp_path, monkeypatch, config_text, expected):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "config.yml").write_text(config_text)

    assert get_sbom_cache_enabled() is expected


@pytest.mark.parametrize("value", ['"false"', "0", "null", "[]", "{}"])
def test_non_boolean_sbom_cache_enabled_fails_validation(tmp_path, monkeypatch, value):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "config.yml").write_text(f"sbom_cache:\n  enabled: {value}\n")

    with pytest.raises(ValueError):
        get_sbom_cache_enabled()
