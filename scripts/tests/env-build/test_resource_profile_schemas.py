import json
from pathlib import Path

import jsonschema
import pytest
from envgenehelper import EnvDefinitionModel

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


def _env_specific_profiles_schema():
    return _schema("env-definition.schema.json")["properties"]["envTemplate"]["properties"][
        "envSpecificResourceProfiles"]


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


def test_override_list_and_single_value_are_valid():
    jsonschema.validate({"bss": ["first-over", "second-over"], "cloud": "cloud-over"},
                        _env_specific_profiles_schema())


def test_override_list_rejects_entries_that_are_not_names():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"bss": [{"name": "first-over"}]}, _env_specific_profiles_schema())


def test_env_definition_model_accepts_override_list(monkeypatch):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    env_definition = EnvDefinitionModel.model_validate(
        {"envTemplate": {"name": "env", "artifact": "env:1",
                         "envSpecificResourceProfiles": {"bss": ["first-over", "second-over"]}}})
    assert env_definition.envTemplate.envSpecificResourceProfiles == {"bss": ["first-over", "second-over"]}
