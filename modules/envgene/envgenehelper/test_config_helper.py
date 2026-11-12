import json
import pytest
from pathlib import Path

from envgenehelper import get_schema


@pytest.mark.unit
def test_regdef_schemas_load_from_configured_root_schema_directory(monkeypatch):
    schemas_dir = Path(__file__).resolve().parents[3] / "schemas"
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schemas_dir))

    assert get_schema("regdef.schema.json")["properties"]["credentialsId"]["type"] == "string"
    assert get_schema("regdef-v2.schema.json")["properties"]["authConfig"]["type"] == "object"
    for schema_path in schemas_dir.glob("*.schema.json"):
        assert get_schema(schema_path.name) == json.loads(schema_path.read_text())
