import json
from pathlib import Path

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


def _schema(name):
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def test_namespace_baseline_is_free_form():
    profile_schema = _schema("namespace.schema.json")["properties"]["profile"]
    jsonschema.validate({"name": "ns-over", "baseline": "small"}, profile_schema)


def test_cloud_accepts_profile_block():
    profile_schema = _schema("cloud.schema.json")["properties"]["profile"]
    jsonschema.validate({"name": "cloud-over", "baseline": "prod"}, profile_schema)


def test_override_without_applications_is_valid():
    jsonschema.validate({"name": "inst-bss", "baseline": "prod"}, _schema("resource-profile.schema.json"))
