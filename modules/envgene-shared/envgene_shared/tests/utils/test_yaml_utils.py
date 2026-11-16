import threading
from pathlib import Path

import pytest
from ruyaml import CommentedMap

from envgene_shared.utils.yaml_utils import (
    get_schema,
    get_schema_validator,
    openYaml,
    readYaml,
    validate_yaml_by_scheme_or_fail,
    writeYamlToFile,
)


def cred_path_in(tmp_path, name='credentials.yml'):
    path = tmp_path / 'environments' / 'cluster-01' / 'env-01' / 'Credentials' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def assert_no_yaml_comments(path):
    for line in path.read_text().splitlines():
        if '#' in line:
            raise AssertionError(f"unexpected comment in credential file: {line!r}")


class TestCredentialYamlWithoutComments:
    @pytest.mark.unit
    def test_write_cred_file_has_no_comments(self, tmp_path):
        creds = CommentedMap({
            'consul-bootstrap-token': CommentedMap({
                'type': 'secret',
                'data': CommentedMap({
                    'secret': 'token'
                })
            })
        })

        cred_path = cred_path_in(tmp_path)
        writeYamlToFile(cred_path, creds)

        assert 'consul-bootstrap-token:' in cred_path.read_text()
        assert_no_yaml_comments(cred_path)

    @pytest.mark.unit
    def test_write_strips_existing_comments(self, tmp_path):
        cred_path = cred_path_in(tmp_path)
        cred_path.write_text(
            '# provenance comment\n'
            '# tenant prod\n'
            'token-a:\n'
            '  type: "secret"\n'
            '  data:\n'
            '    secret: "envgeneNullValue" # FillMe\n'
        )

        loaded = openYaml(cred_path)
        writeYamlToFile(cred_path, loaded)

        assert_no_yaml_comments(cred_path)


class TestYamlThreadSafety:
    @pytest.mark.unit
    def test_concurrent_load_and_dump(self):
        errors = []
        results = []

        def worker(index: int) -> None:
            try:
                data = readYaml(f"key_{index}: value_{index}\n")
                assert data[f"key_{index}"] == f"value_{index}"
                results.append(index)
            except Exception as exc:
                errors.append((index, exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent YAML operations raised errors: {errors}"
        assert len(results) == 20


class TestGetSchema:
    @pytest.mark.unit
    def test_loads_schema_by_exact_filename(self, monkeypatch, tmp_path):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema_path = tmp_path / "namespace.schema.json"
        schema_path.write_text('{"type":"object","properties":{"name":{"type":"string"}}}')
        monkeypatch.setenv("JSON_SCHEMAS_DIR", str(tmp_path))

        assert get_schema("namespace.schema.json") == schema

    @pytest.mark.unit
    def test_raises_for_unknown_schema(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JSON_SCHEMAS_DIR", str(tmp_path))

        with pytest.raises(FileNotFoundError):
            get_schema("missing.schema.json")

    @pytest.mark.unit
    def test_rejects_path_like_schema_name(self):
        with pytest.raises(ValueError):
            get_schema("../outside.schema.json")

    @pytest.mark.unit
    def test_loads_repository_schema_from_configured_root(self, monkeypatch):
        schemas_dir = Path(__file__).resolve().parents[5] / "schemas"
        monkeypatch.setenv("JSON_SCHEMAS_DIR", str(schemas_dir))

        assert "save_artifacts" in get_schema("config.schema.json")["properties"]

    @pytest.mark.unit
    def test_validation_by_name_resolves_relative_references(self, monkeypatch, tmp_path):
        schema_path = tmp_path / "root.schema.json"
        schema_path.write_text(
            '{"$schema":"https://json-schema.org/draft/2020-12/schema",'
            '"type":"object","properties":{"name":{"$ref":"definitions/name.schema.json"}}}'
        )
        definition_path = tmp_path / "definitions" / "name.schema.json"
        definition_path.parent.mkdir()
        definition_path.write_text('{"type":"string"}')
        monkeypatch.setenv("JSON_SCHEMAS_DIR", str(tmp_path))

        validate_yaml_by_scheme_or_fail(
            input_yaml_content={"name": "namespace"},
            schema_name="root.schema.json",
        )

        cache_before = get_schema_validator.cache_info()
        with pytest.raises(ValueError, match="Validation failed"):
            validate_yaml_by_scheme_or_fail(
                input_yaml_content={"name": 123},
                schema_name="root.schema.json",
            )
        cache_after = get_schema_validator.cache_info()
        assert cache_after.misses == cache_before.misses
        assert cache_after.hits == cache_before.hits + 1

    def test_cached_names_are_isolated_by_schema_directory(self, tmp_path):
        for directory, schema in [("strings", '{"type":"string"}'), ("numbers", '{"type":"number"}')]:
            target = tmp_path / directory
            target.mkdir()
            (target / "value.schema.json").write_text(schema)

        validate_yaml_by_scheme_or_fail(
            input_yaml_content="value", schema_name="value.schema.json", schemas_dir=tmp_path / "strings",
        )
        with pytest.raises(ValueError, match="Validation failed"):
            validate_yaml_by_scheme_or_fail(
                input_yaml_content="value", schema_name="value.schema.json", schemas_dir=tmp_path / "numbers",
            )


class TestSchemaValidatedYamlWriter:
    @pytest.mark.unit
    def test_rejects_invalid_content_before_creating_file(self, monkeypatch, tmp_path):
        schema_path = tmp_path / "namespace.schema.json"
        schema_path.write_text('{"type":"object","properties":{"name":{"type":"string"}}}')
        monkeypatch.setenv("JSON_SCHEMAS_DIR", str(tmp_path))
        target = tmp_path / "namespace.yml"

        with pytest.raises(ValueError, match="Validation failed"):
            writeYamlToFile(target, {"name": 123}, schema_name="namespace.schema.json")

        assert not target.exists()
