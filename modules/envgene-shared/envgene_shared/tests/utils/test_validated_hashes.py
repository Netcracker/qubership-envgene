import json

import pytest

from envgene_shared.utils import yaml_utils
from envgene_shared.utils.yaml_utils import skip_validated, validate_yaml_by_scheme_or_fail

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {"name": {"type": "string"}},
}


@pytest.fixture
def schema_path(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(SCHEMA))
    return path


def fail_if_validated(monkeypatch):
    def validator(_):
        raise AssertionError("validation must be skipped")
    monkeypatch.setattr(yaml_utils, "get_schema_validator", validator)


@pytest.mark.unit
def test_passed_validation_is_remembered(schema_path):
    with skip_validated([]) as validated:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)

    assert len(validated.seen) == 1


@pytest.mark.unit
def test_same_content_and_schema_skip_validation(schema_path, monkeypatch):
    with skip_validated([]) as first:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)
    fail_if_validated(monkeypatch)

    with skip_validated(first.seen) as second:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)

    assert second.seen == first.seen


@pytest.mark.unit
def test_changed_content_is_validated(schema_path):
    with skip_validated([]) as first:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)

    with skip_validated(first.seen), pytest.raises(ValueError):
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": 1}, schema_file_path=schema_path)


@pytest.mark.unit
def test_changed_schema_is_validated(schema_path, tmp_path):
    with skip_validated([]) as first:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)
    strict_path = tmp_path / "strict.json"
    strict_path.write_text(json.dumps({**SCHEMA, "required": ["value"]}))

    with skip_validated(first.seen), pytest.raises(ValueError):
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=strict_path)


@pytest.mark.unit
def test_failed_validation_is_not_remembered(schema_path):
    with skip_validated([]) as validated, pytest.raises(ValueError):
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": 1}, schema_file_path=schema_path)

    assert validated.seen == set()


@pytest.mark.unit
def test_validation_runs_without_open_cache(schema_path):
    with skip_validated([]) as first:
        validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)

    validate_yaml_by_scheme_or_fail(input_yaml_content={"name": "a"}, schema_file_path=schema_path)

    assert yaml_utils._validated_hashes is None
    assert len(first.seen) == 1
