import pytest
from pathlib import Path

from envgenehelper.config_helper import get_regdef_schema, get_regdef_v2_schema


@pytest.mark.unit
def test_regdef_schemas_load_from_configured_root_schema_directory(monkeypatch):
    schemas_dir = Path(__file__).resolve().parents[3] / "schemas"
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schemas_dir))

    assert get_regdef_schema()["properties"]["credentialsId"]["type"] == "string"
    assert get_regdef_v2_schema()["properties"]["authConfig"]["type"] == "object"