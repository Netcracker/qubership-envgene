import json
from pathlib import Path

import jsonschema
import pytest
from envgenehelper import EnvDefinitionModel

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


def _env_specific_profiles_schema():
    return _schema("env-definition.schema.json")["properties"]["envTemplate"]["properties"][
        "envSpecificResourceProfiles"]


def _generated_profiles_schema():
    return _schema("env-definition.schema.json")["properties"]["envTemplate"]["properties"][
        "generatedProfileDefaults"]


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


def test_env_specific_override_is_one_name_per_key():
    jsonschema.validate({"bss": "inst-bss", "cloud": "cloud-over"}, _env_specific_profiles_schema())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"bss": ["first-over", "second-over"]}, _env_specific_profiles_schema())


def test_generated_profiles_map_holds_one_name_per_key():
    jsonschema.validate({"bss": "bss-profile-override"}, _generated_profiles_schema())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"bss": ["bss-profile-override", "inst-bss"]}, _generated_profiles_schema())


def test_env_definition_model_accepts_generated_profiles_map(monkeypatch):
    monkeypatch.setenv("JSON_SCHEMAS_DIR", str(SCHEMAS_DIR))
    env_definition = EnvDefinitionModel.model_validate(
        {"envTemplate": {"name": "env", "artifact": "env:1",
                         "envSpecificResourceProfiles": {"bss": "inst-bss"},
                         "generatedProfileDefaults": {"bss": "bss-profile-override"}}})
    assert env_definition.envTemplate.envSpecificResourceProfiles == {"bss": "inst-bss"}
    assert env_definition.envTemplate.generatedProfileDefaults == {"bss": "bss-profile-override"}
